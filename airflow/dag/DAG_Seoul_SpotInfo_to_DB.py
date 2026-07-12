from airflow.sdk import DAG,Variable,task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pendulum
import pandas as pd
import json

with DAG(
    dag_id='DAG_Seoul_SpotInfo_to_DB',
    schedule="1 0 * * *",
    start_date=pendulum.datetime(2026, 7, 1,tz='Asia/Seoul'),
    tags=['서울시 지점정보','데이터 적재'],
    description='서울시 교통지점정보 DB 적재 DAG',
    catchup= False
) as dag:

    @task
    def load_json_data(**context):
        logical_date = context['logical_date'].strftime("%Y%m%d")
        s3_hook = S3Hook(aws_conn_id='minio_connection')
        content=s3_hook.read_key(
            bucket_name='spot-info',
            key=f'spot_name/{logical_date}_data.json'
        )
        spot_list = json.loads(content)

        return spot_list

    @task
    def staging_data_postgres(list_dic,**context):
        df = pd.DataFrame(list_dic)

        postgres_hook = PostgresHook(
            postgres_conn_id='postgres_connection'
        )

        engine = postgres_hook.get_sqlalchemy_engine()

        df.to_sql(
            name='stg_spot_info',
            con=engine,
            schema='public',
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi',
        )

    json_data = load_json_data()
    staging_data_postgres(json_data)
