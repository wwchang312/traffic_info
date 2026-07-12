# 서울시 교통량 이력 정보 시각화 Pipeline
<img width="1468" height="781" alt="image" src="https://github.com/user-attachments/assets/f09f47eb-bf3a-4a27-97d3-cfa6325f8ede" />


## Tech Stack

### Data Orchestration
- Apache Airflow

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

