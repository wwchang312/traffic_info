from airflow.sdk import DAG,Variable,task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pendulum
import pandas as pd
import requests
import xmltodict
import boto3
import json

with DAG(
    dag_id='DAG_Seoul_traffic_info',
    schedule=None,
    start_date=pendulum.datetime(2026, 6, 1,tz='Asia/Seoul'),
    tags=['서울시','교통량'],
    description='서울시 교통량 정보 호출 API',
    catchup= False
) as dag:

    @task
    def load_json_data():
        s3_hook = S3Hook(aws_conn_id='minio_connection')
        content=s3_hook.read_key(
            bucket_name='spot-info',
            key='spot_name/20260710_data.json'
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

        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("DB 연결 성공:", result.scalar())
        except Exception as e:
            print("DB 연결 실패")
            print("예외 타입:", type(e).__name__)
            print("예외 내용:", repr(e))
            raise

        df.to_sql(
            name='stg_traffic',
            con=engine,
            schema='public',
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi',
        )

    json_data = load_json_data()
    staging_data_postgres(json_data)
