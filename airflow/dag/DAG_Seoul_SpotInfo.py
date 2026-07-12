from airflow.sdk import DAG,Variable,task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import pendulum
import requests
import xmltodict
import json

with DAG(
    dag_id='DAG_Seoul_SpotInfo',
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2026, 7, 1,tz='Asia/Seoul'),
    tags=['서울시','지점정보'],
    description='서울시 교통량 지점 정보 호출 API',
    catchup= False
) as dag:

    @task
    def call_api(**context):
        api_key =Variable.get('seoul_api_key')

        #
        url = f'http://openapi.seoul.go.kr:8088/{api_key}/xml/SpotInfo/1/3'

        response = requests.get(url)
        # xml -> dic
        dic = xmltodict.parse(response.content)


        # API 호출 에러 발생시 확인용
        if dic['SpotInfo']['RESULT']['CODE'] != 'INFO-000':
            raise Exception(f"API request failed: {response.status_code}, {response.text}")

        # 총 페이지 수
        end_page = int(dic['SpotInfo']['list_total_count'])


        url = f'http://openapi.seoul.go.kr:8088/{api_key}/xml/SpotInfo/1/{end_page}'
        response = requests.get(url)
        dic = xmltodict.parse(response.content)

        data=dic['SpotInfo']['row']

        return data

    @task
    def get_spot_info_to_s3(data:list[dict],**context):
        logical_date = context['logical_date'].strftime("%Y%m%d")

        s3_hook = S3Hook(aws_conn_id="minio_connection")

        content = json.dumps(data, ensure_ascii=False)

        s3_hook.load_string(
            string_data=content,
            bucket_name="spot-info",
            key=f'spot_name/{logical_date}_data.json',
            replace=True,
        )


    call_api=call_api()
    get_spot_info_to_s3(call_api)



