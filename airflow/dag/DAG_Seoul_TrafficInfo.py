from airflow.sdk import DAG,Variable,task,Param
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pendulum
import requests
import xmltodict
import json

with DAG(
    dag_id='DAG_Seoul_TrafficInfo',
    schedule="0 * * * *",
    start_date=pendulum.datetime(2026, 7, 1,tz='Asia/Seoul'),
    tags=['서울시','교통량 이력'],
    description='서울시 교통량 이력정보 호출 API',
    catchup= False,
    max_active_tasks=10,
) as dag:
    # DB에 저장된 Spot_Info에서 Spot_num 파라미터 수집
    @task
    def get_spot_num_list():
        postgres_hook = PostgresHook(
            postgres_conn_id='postgres_connection'
        )

        records = postgres_hook.get_records(
            sql="""
                       SELECT DISTINCT spot_num
                       FROM public.spot_info
                       WHERE spot_num IS NOT NULL
                       ORDER BY spot_num
                   """
        )

        return [str(row[0]) for row in records]

    @task
    def call_api(spot_num,**context):
        api_key =Variable.get('seoul_api_key')

        logical_date = context["logical_date"].in_timezone("Asia/Seoul")

        date_param = logical_date.strftime("%Y%m%d")
        hour_param = logical_date.subtract(hours=1).strftime("%H")

        # api 호출 url 작성
        url = f'http://openapi.seoul.go.kr:8088/{api_key}/xml/VolInfo/1/5/{spot_num}/{date_param}/{hour_param}'

        response = requests.get(url)

        # xml -> dic
        dic = xmltodict.parse(response.content)


        # API 호출 에러 발생시 확인용
        if dic['VolInfo']['RESULT']['CODE'] != 'INFO-000':
            raise Exception(f"API request failed: {response.status_code}, {response.text}")

        # 각 spot_num마다 list_total_count가 다르기 때문에 end_page정보를 따로 수집
        end_page = int(dic['VolInfo']['list_total_count'])


        f'http://openapi.seoul.go.kr:8088/{api_key}/xml/VolInfo/1/{end_page}/{spot_num}/{date_param}/{hour_param}'
        response = requests.get(url)
        dic = xmltodict.parse(response.content)

        data=dic['VolInfo']['row']

        return data


    @task
    def save_json_data(data, **context):
        logical_date = context["logical_date"].in_timezone("Asia/Seoul")

        date_param = logical_date.strftime("%Y%m%d")
        hour_param = logical_date.subtract(hours=1).strftime("%H") #한시간 이전의 교통량을 수집해야한다.

        s3_hook = S3Hook(aws_conn_id="minio_connection")

        content = json.dumps(data,ensure_ascii=False)

        s3_hook.load_string(
            string_data=content,
            bucket_name="traffic-info",
            key=f"traffic_vol/{date_param}_{hour_param}_data.json",
            replace=True,
        )


    spot_num_lst=get_spot_num_list()
    data=call_api.expand(spot_num=spot_num_lst)
    save_json_data(data)


