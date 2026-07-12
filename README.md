# 서울시 교통량 이력 정보 시각화 Pipeline
<img width="1468" height="781" alt="image" src="https://github.com/user-attachments/assets/f09f47eb-bf3a-4a27-97d3-cfa6325f8ede" />


## Tech Stack

### Data Orchestration
- Apache Airflow (3.1.7)

### Data Processing
- Pandas

### Database
- PostgreSQL

### Storage
- MinIO

### Visualization
- Streamlit
- Folium

### Infrastructure
- Docker



## 목표
서울시 열린데이터 광장에서 제공하는 서울시 교통량 이력 정보를 이용하여 매 시간별 서울시 교통 지점의 차량 통행량을 시각화한다.


서울시 열린데이터 광장에서 제공하고 있는 서울시 교통량 이력 정보는 서울시 주요 도로의 시간대별 교통량 정보를 1시간 주기로 갱신하여 업로드를 수행한다.
이를 호출하기 위해서는  "서울시 교통량 지점 정보"도 호출해서 가져와야한다.

- 서울시 교통량 지점 정보(https://data.seoul.go.kr/dataList/OA-13314/A/1/datasetView.do)

- 서울시 교통량 이력 정보(https://data.seoul.go.kr/dataList/OA-13316/A/1/datasetView.do)


## 프로젝트 구성
<img width="1774" height="887" alt="Image" src="https://github.com/user-attachments/assets/14af9f79-d24b-4e1d-8d79-f5518fad54b2" />



DAG_Seoul_SpotInfo.py는 서울시 교통량 지점 정보를 호출하고 이를 객체 스토리지인 Minio 버켓에 저장한다.
DAG_Seoul_SpotInfo_to_DB.py는 Minio에서 원본 데이터를 읽어 스테이징 테이블에 적재하고, 스테이징 테이블에 있는 데이터를 타겟 테이블로 적재하는 역할을 한다.

이와 동일하게 
DAG_Seoul_TrafficInfo.py는 서울시 교통량 이력 정보를 호출하고 이를 객체 스토리지인 Minio버켓에 저장한다.
DAG_Seoul_TrafficInfo_to_DB.py는 Minio에서 원본 데이터를 읽어 스테이징 테이블에 적재하고, 스테이징 테이블에 있는 데이터를 타겟 테이블로 적재하는 역할을 한다.


postgres에는 spot_info 테이블과 traffic_vol 테이블을 조인하여 View (vw_traffic_info)를 생성한다.



seoul_traffic_volumes_map는 이 View를 참조하여 서울 교통 지점별 교통량을 표시하는 시각화 자료를 streamlit를 이용해서 나타낸다.


### sql 쿼리문

## create_table.sql
해당 프로젝트에 필요한 테이블을 생성하는 쿼리문

## sp_merge_staging_to_target.sql
스테이징 테이블에서 타겟 테이블로 데이터를 적재하는 프로시저
MERGE문을 활용하며, 스테이징이 완료되면 스테이징 테이블의 데이터를 삭제한다.


## S3 객체 스토리지

객체 스토리지에는 S3가 호환되는 Minio를 사용했다.
DAG이 한번 수행이 될때마다 API의 리턴 데이터 중, value값에 해당하는 것을 json 형식으로 덤핑하여 저장한다.
<img width="1719" height="524" alt="image" src="https://github.com/user-attachments/assets/c146d6cb-6abb-4e75-a155-3577ae53a331" />



