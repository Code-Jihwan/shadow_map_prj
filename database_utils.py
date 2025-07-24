# database_utils.py

import psycopg2
from psycopg2 import sql
import os

# --- 데이터베이스 연결 설정 ---
DB_NAME = os.getenv('DB_NAME', 'shadow_map_db')
DB_USER = os.getenv('DB_USER', 'jihwan')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'a9503!@#') # 본인의 비밀번호로 변경!
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# 좌표계 설정 (EPSG:5186은 한국 중부원점 기준의 미터 단위 좌표계)
CRS_METRIC = 5186

def get_buildings_from_db():
    """
    PostGIS에서 건물 데이터를 가져옵니다.
    이때 좌표계를 미터 단위(EPSG:5186)로 변환합니다.
    """
    conn = None
    buildings = []
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        
        query = sql.SQL("""
            SELECT id, height, ST_AsText(ST_Transform(geometry, %s)) as geom_wkt
            FROM buildings;
        """)
        
        cur.execute(query, (CRS_METRIC,))
        buildings = cur.fetchall()
        
        cur.close()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            
    return buildings