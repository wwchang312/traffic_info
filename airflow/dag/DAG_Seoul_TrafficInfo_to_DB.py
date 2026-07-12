from airflow.sdk import DAG,Variable,task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pendulum
import pandas as pd
import json

with DAG(
    dag_id='DAG_Seoul_TrafficInfo_to_DB',
    schedule="10 * * * *",
    start_date=pendulum.datetime(2026, 7, 1,tz='Asia/Seoul'),
    tags=['서울시','데이터 적재','교통량'],
    description='서울시 교통량 이력정보 호출 데이터 DB 적재',
    catchup= False
) as dag:

    @task
    def load_json_data(**context):
        logical_date = context["logical_date"].in_timezone("Asia/Seoul").subtract(hours=1)

        date_param = logical_date.strftime("%Y%m%d")
        hour_param = logical_date.strftime("%H")


        s3_hook = S3Hook(aws_conn_id='minio_connection')
        content=s3_hook.read_key(
            bucket_name='traffic-info',
            key=f"traffic_vol/{date_param}_{hour_param}_data.json"
        )
        traffic_vol = json.loads(content)

        return traffic_vol

    @task
    def staging_data_postgres(list_dic,**context):
        df = pd.DataFrame(list_dic)

        postgres_hook = PostgresHook(
            postgres_conn_id='postgres_connection'
        )

        engine = postgres_hook.get_sqlalchemy_engine()

        df.to_sql(
            name='stg_traffic_vol',
            con=engine,
            schema='public',
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi',
        )

    @task
    def load_staging():
        postgres_hook = PostgresHook(
            postgres_conn_id='postgres_connection'
        )

        postgres_hook.run(
            """
            CALL public.merge_staging_to_target('traffic_vol');
            """
        )


    json_data = load_json_data()
    staging_task=staging_data_postgres(json_data)
    load_task=load_staging()

    staging_task >> load_task