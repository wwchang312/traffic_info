import pandas as pd
import streamlit as st
import folium
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from streamlit_folium import st_folium
from dotenv import load_dotenv
import os

load_dotenv()

postgres_usr= os.getenv("POSTGRES_USR")
postgres_pwd= os.getenv("POSTGRES_PWD")

st.set_page_config(
    page_title="서울시 교통지점별 교통량 맵",
    layout="wide",
)


@st.cache_resource
def get_engine():
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=postgres_usr,
        password=postgres_pwd,
        host="localhost",
        port=5433,
        database="postgres",
    )
    return create_engine(connection_url)


@st.cache_data(ttl=300)
def load_traffic_data() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT 
	        spot_id, 
	        spot_name, 
	        longitude, 
            latitude, 
            record_time, 
            io_type, 
            lane_number, 
            traffic_volume
        FROM vw_traffic_info
    """

    return pd.read_sql(sql, engine)


df = load_traffic_data()

if df.empty:
    st.warning("조회된 교통량 데이터가 없습니다.")
    st.stop()

df["record_time"] = (
    pd.to_datetime(df["record_time"])
    .dt.tz_convert("Asia/Seoul")
)

st.title("시간대별 차량 통행량 지도")


# 날짜 및 시간 필터

available_dates = sorted(
    df["record_time"].dt.date.unique()
)

selected_date = st.sidebar.selectbox(
    "날짜 선택",
    available_dates,
)

date_df = df[
    df["record_time"].dt.date == selected_date
]

available_hours = sorted(
    date_df["record_time"]
    .dt.strftime("%H:%M")
    .unique()
)

selected_hour = st.sidebar.selectbox(
    "시간대 선택",
    available_hours,
)

filtered_df = date_df[
    date_df["record_time"]
    .dt.strftime("%H:%M")
    == selected_hour
]

#교통량 지점별 집계

spot_traffic_volumes_sum = (
    filtered_df
    .groupby(
        [
            "spot_id",
            "spot_name",
            "longitude",
            "latitude",
        ],
        as_index=False,
    )
    .agg(
        total_volume=("traffic_volume", "sum")
    )
)


#Folium 지도 생성

center_lat = spot_traffic_volumes_sum["latitude"].mean()
center_lon = spot_traffic_volumes_sum["longitude"].mean()

traffic_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    tiles="OpenStreetMap",
)

max_volume = spot_traffic_volumes_sum["total_volume"].max()


#각 지점별 상세정보 팝업

for _, spot in spot_traffic_volumes_sum.iterrows():
    filtered_spot_detail = filtered_df[
        filtered_df["spot_name"]
        == spot["spot_name"]
    ].copy()

    detail_rows = ""

    for _, detail in filtered_spot_detail.sort_values(
        ["io_type", "lane_number"]
    ).iterrows():
        inout_label = (
            "진입"
            if detail["io_type"] == "IN"
            else "진출"
        )

        detail_rows += f"""
            <tr>
                <td>{inout_label}</td>
                <td>{detail['lane_number']}차선</td>
                <td style="text-align:right;">
                    {detail['traffic_volume']:,}대
                </td>
            </tr>
        """

    popup_html = f"""
        <div style="width:280px;">
            <h4>{spot['spot_name']}</h4>

            <div>
                조회 시간: {selected_date} {selected_hour}
            </div>

            <div>
                총 통행량:
                <strong>{spot['total_volume']:,}대</strong>
            </div>

            <table
                border="1"
                style="
                    width:100%;
                    margin-top:10px;
                    border-collapse:collapse;
                "
            >
                <thead>
                    <tr>
                        <th>구분</th>
                        <th>차선</th>
                        <th>통행량</th>
                    </tr>
                </thead>

                <tbody>
                    {detail_rows}
                </tbody>
            </table>
        </div>
    """

    radius = 5

    if max_volume > 0:
        radius += (
            spot["total_volume"]
            / max_volume
        ) ** 0.5 * 15

    # 데이터 분포에 따라 색깔에 차등을 두기 위한 분위수 계산
    q1 = spot_traffic_volumes_sum["total_volume"].quantile(0.33)
    q2 = spot_traffic_volumes_sum["total_volume"].quantile(0.66)

    #색깔 할당
    def get_marker_color(volume: int) -> str:
        if volume <= q1:
            return "green"
        elif volume <= q2:
            return "orange"
        else:
            return "red"

    color = get_marker_color(spot["total_volume"])


    folium.CircleMarker(
        location=[
            spot["latitude"],
            spot["longitude"],
        ],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        tooltip=(
            f"{spot['spot_name']}<br>"
            f"총 통행량: {spot['total_volume']:,}대"
        ),
        popup=folium.Popup(
            popup_html,
            max_width=350,
        ),
    ).add_to(traffic_map)


# 지도표시
st_folium(
    traffic_map,
    width=None,
    height=700,
)