from airflow.sdk import DAG,Variable,task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pendulum
import folium

with DAG(
    dag_id='DAG_Seoul_SpotInfo_to_DB',
    schedule="15 * * * *",
    start_date=pendulum.datetime(2026, 7, 1,tz='Asia/Seoul'),
    tags=['서울시 교통량','시각화'],
    description='서울시 교통지점별 교통이력 시각화 DAG',
    catchup= False
) as dag:

    #
    def create_time_traffic_map(df, output_path):
        traffic_map = folium.Map(
            location=[
                df["longitude"].mean(),
                df["latitude"].mean(),
            ],
            zoom_start=11,
        )

        # 마커 및 시간 슬라이더 생성

        traffic_map.save(output_path)

        return output_path

    @task
    def create_and_upload_traffic_file():
        postgres_hook = PostgresHook(
            postgres_conn_id="postgres_connection"
        )

        df = postgres_hook.get_pandas_df(
            """
            SELECT 
                spot_id, --지점ID
                spot_name, --지점명
                longitude, --경도
                latitude,  --위도
                "date",    --날짜
                "hour",    --시간
                io_type,   --입출입
                lane_number, --차선
                traffic_volume --각 기준별 통행량
            FROM vw_traffic_info;
            """
        )

        html_path = create_time_traffic_map(
            df,
            "/tmp/traffic_time_map.html",
        )

        s3_hook = S3Hook(
            aws_conn_id="minio_connection"
        )

        s3_hook.load_file(
            filename=html_path,
            bucket_name="traffic-info",
            key="traffic-map/traffic_time_map.html",
            replace=True,
        )