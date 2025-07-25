## [프로젝트명 : 스마트 그늘길 내비게이션] 무더위 속 시원한 그늘길을 찾아서

#### 여름철 시간에 따라 건물주변으로 발생하는 그늘을 계산하여 표현하고 사용자들이 그늘을 통해 이동할 수 있는 동선 지도 제작을 목표로한다.
***



***
requirements.txt

# Flask 및 웹 서버 관련
Flask
flask-cors

# 데이터베이스 (PostgreSQL) 관련
psycopg2-binary

# 지리 공간 데이터 처리 및 계산 관련
Shapely
pyproj
fiona

# 천문학 계산 (태양 위치) 관련
astral
pytz

Flask: Python API 서버의 핵심 웹 프레임워크
flask-cors: 다른 주소(Origin)에서 오는 프론트엔드의 요청을 허용하기 위해 반드시 필요한 CORS 처리 라이브러리
psycopg2-binary: Python과 PostgreSQL 데이터베이스를 연결해 주는 드라이
Shapely: 파이썬에서 폴리곤과 같은 기하학적 객체를 다루고, 합치거나(unary_union) 분석하는 데 사용
pyproj: 미터 단위 좌표계(EPSG:5186)와 위경도 좌표계(EPSG:4326)를 서로 변환하는 핵심적인 역할
fiona: load_data.py에서 GeoJSON 파일을 쉽게 읽어 들이기 위해 사용
astral: 특정 위치와 시간의 태양 고도/방위각을 계산하는 데 사용
pytz: astral 라이브러리가 시간대(Timezone)를 정확하게 처리하기 위해 필요로 하는 라이브러리
***

