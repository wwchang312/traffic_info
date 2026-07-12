from airflow.sdk import DAG,Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import pendulum
from airflow.decorators import task
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

    hook = S3Hook(aws_conn_id='minio_connection')

    content = hook.read_key(
        bucket_name="spot-info",
        key="spot_name/20260710_data.json"
    )

    spot_list = json.loads(content)


    print(spot_list)