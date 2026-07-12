--교통 지점정보 스테이징 테이블
drop table public.stg_spot_info;
create table public.stg_spot_info(
	spot_nm 	VARCHAR(512),
	spot_num	VARCHAR(32),
	grs80tm_x   double precision,
	grs80tm_y	double precision,
	loaded_at   TIMESTAMP default CURRENT_TIMESTAMP
);

--교통 지점정보 타겟 테이블
drop table public.spot_info;
create table public.spot_info(
	spot_nm 	VARCHAR(512),
	spot_num	VARCHAR(32),
	grs80tm_x   double precision,
	grs80tm_y	double precision,
	constraint pk_spot_info primary key (spot_num)
);

--서울시 교통량 이력 스테이징 테이블
drop table public.stg_traffic_vol;
create table public.stg_traffic_vol(
	ymd			VARCHAR(32),
	hh			VARCHAR(4),
	spot_num	VARCHAR(32),
	io_type		VARCHAR(4), --입출입 구분
	lane_num	VARCHAR(4), --차선
	vol			BIGINT,
	loaded_at   TIMESTAMP default CURRENT_TIMESTAMP
);

--서울시 교통량 이력 타겟 테이블
drop table public.traffic_vol;
create table public.traffic_vol(
	ymd			VARCHAR(32),
	hh			VARCHAR(4),
	spot_num	VARCHAR(32),
	io_type		VARCHAR(4), --입출입 구분
	lane_num	VARCHAR(4), --차선
	vol			BIGINT,
	constraint pk_traffic_vol primary key (ymd,hh,spot_num,io_type,lane_num)
);


-- 서울시 교통지점별 통행량 정보 view
drop view vw_traffic_info;

create view vw_traffic_info as
select
	si.spot_num "spot_id",
	si.spot_nm  "spot_name",
	ST_X(
		ST_Transform(
			ST_SetSRID(
				ST_MakePoint(grs80tm_x,grs80tm_y),
				5181
			),
			4326
		)
	) "longitude",
	ST_Y(
		ST_Transform(
			ST_SetSRID(
				ST_MakePoint(grs80tm_x,grs80tm_y),
				5181
			),
			4326
		)
	) "latitude",
	TO_TIMESTAMP(tv.ymd||LPAD(hh,2,'0'),'YYYYMMDDHH24') as record_time,
	case
		when tv.io_type = '1' then 'IN'
		when tv.io_type = '2' then 'OUT'
		else 'unknown'
	end "io_type",
	tv.lane_num "lane_number",
	SUM(tv.vol) "traffic_volume"
from public.spot_info si
inner join public.traffic_vol tv
on si.spot_num=tv.spot_num
group by
	si.spot_num,
	si.spot_nm,
	tv.ymd,
	tv.hh,
	tv.io_type,
	tv.lane_num
order by
	tv.ymd,
	tv.hh,
	tv.io_type,
	tv.lane_num;



