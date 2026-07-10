from airflow.sdk import DAG,Variable
import pendulum
from airflow.decorators import task
import requests
import xmltodict
import boto3

with DAG(
    dag_id='DAG_Seoul_SpotInfo',
    schedule=None,
    start_date=pendulum.datetime(2026, 6, 1,tz='Asia/Seoul'),
    tags=['서울시','지점정보'],
    description='서울시 교통량 지점 정보 호출 API',
    catch_up= False
) as dag:

    @task
    def call_api(**context):
        api_key =Variable.get('api_key')

        #
        url = f'http://openapi.seoul.go.kr:8088/{api_key}/xml/SpotInfo/1/5'

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
    def get_spot_info_to_s3(data:str,**context):
        logical_date = context['logical_date'].strftime("%Y%m%d")

        s3 = boto3.client(
            "s3",
            endpoint_url="http://minio:9000",
            aws_access_key_id=Variable.get("minio-access-key"),
            aws_secret_access_key=Variable.get("minio-secret-key")
        )

        # MinIO 저장
        s3.put_object(
            Bucket="spot-info",
            Key=f"spot_name/{logical_date}_data.json",
            Body=data,
            ContentType="application/json"
        )

call_api() >> get_spot_info_to_s3()




