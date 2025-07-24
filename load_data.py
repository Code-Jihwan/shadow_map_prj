import fiona
from shapely.geometry import shape
import psycopg2
from psycopg2 import sql
import os

# --- 1. 데이터베이스 연결 설정 ---
DB_NAME = os.getenv('DB_NAME', 'shadow_map_db')
DB_USER = os.getenv('DB_USER', 'jihwan')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'a9503!@#') # 실제 비밀번호로 변경하세요!
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# GeoJSON 파일 경로 (다운로드한 파일 이름에 맞게 수정하세요)
GEOJSON_FILE = 'export.geojson'

# 층당 평균 높이 (미터) - 앞서 결정한 값
METERS_PER_LEVEL = 3.5

def load_geojson_to_postgis(geojson_path):
    conn = None
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        # --- 2. 건물 데이터를 저장할 테이블 생성 ---
        # 기존 테이블이 있다면 삭제 (개발 중에는 편리하지만, 실제 서비스에서는 주의)
        cur.execute("DROP TABLE IF EXISTS buildings;")
        conn.commit() # DROP TABLE은 트랜잭션 종료 후 적용되므로 commit 필요

        cur.execute(sql.SQL("""
            CREATE TABLE buildings (
                id SERIAL PRIMARY KEY,
                osm_id VARCHAR(255),
                levels INTEGER,
                height REAL,
                geometry GEOMETRY(Polygon, 4326) -- 4326은 WGS84 좌표계 (위경도)
            );
        """))
        conn.commit()
        print("Table 'buildings' created successfully.")

        # --- 3. GeoJSON 파일 읽기 및 데이터 삽입 ---
        with fiona.open(geojson_path, 'r') as source:
            # 스키마 확인 (속성 이름 확인)
            # print(source.schema)

            for feature in source:
                props = feature['properties']
                geom_data = feature['geometry']

                osm_id = props.get('id') # OpenStreetMap ID (없을 수도 있음)
                levels = props.get('building:levels')

                # height가 있다면 height 사용, 없다면 levels로 계산
                height = props.get('height')
                if height is not None:
                    try:
                        height = float(height)
                    except ValueError:
                        height = None # 유효하지 않은 값 처리
                
                if height is None and levels is not None:
                    try:
                        levels = int(levels)
                        height = levels * METERS_PER_LEVEL
                    except ValueError:
                        levels = None # 유효하지 않은 값 처리
                        height = None

                if geom_data and geom_data['type'] == 'Polygon' and height is not None:
                    # Shapely를 사용하여 GeoJSON geometry를 파이썬 객체로 변환
                    # PostGIS는 WKT (Well-Known Text) 형식을 선호하므로 to_wkt() 사용
                    geom_wkt = shape(geom_data).wkt

                    # 데이터 삽입 쿼리
                    insert_query = sql.SQL("""
                        INSERT INTO buildings (osm_id, levels, height, geometry)
                        VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))
                    """)
                    cur.execute(insert_query, (osm_id, levels, height, geom_wkt))
                else:
                    print(f"Skipping feature (missing geometry or height/levels): {props}")

            conn.commit()
            print(f"Successfully loaded {cur.rowcount} buildings into 'buildings' table.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback() # 오류 발생 시 롤백
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    if not os.path.exists(GEOJSON_FILE):
        print(f"Error: {GEOJSON_FILE} not found. Please ensure the GeoJSON file is in the same directory.")
        print("Or update the GEOJSON_FILE variable with the correct path.")
    else:
        load_geojson_to_postgis(GEOJSON_FILE)