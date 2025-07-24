# app.py (최종 정리 버전)

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date, time
from shapely.ops import unary_union
from shapely.geometry import mapping
from pyproj import Transformer

# --- 로컬 모듈 임포트 ---
# 각 파일에서 필요한 함수들을 정확하게 가져옵니다.
from sun_calculator import get_sun_position
from shadow_calculator import calculate_shadow_polygon
from database_utils import get_buildings_from_db, CRS_METRIC

# --- Flask 애플리케이션 및 CORS 설정 ---
app = Flask(__name__)
# 모든 도메인에서의 요청을 허용합니다. (개발 환경에 적합)
CORS(app) 

# --- 전역 변수 설정 (서버 시작 시 한 번만 실행) ---

# 1. 건물 데이터 로딩
print("Loading building data from PostGIS...")
BUILDINGS_DATA = get_buildings_from_db()
if BUILDINGS_DATA:
    print(f"Successfully loaded {len(BUILDINGS_DATA)} buildings.")
else:
    print("Warning: No building data loaded. Check database connection and data.")

# 2. 좌표계 변환기 생성
# EPSG:5186 (미터 단위) -> EPSG:4326 (위도, 경도)
# always_xy=True 옵션은 결과 좌표 순서를 (경도, 위도)로 일관되게 보장합니다.
transformer = Transformer.from_crs(f"EPSG:{CRS_METRIC}", "EPSG:4326", always_xy=True)


def transform_geom_coordinates(geom):
    """
    GeoJSON 호환 딕셔너리의 좌표를 변환하는 재귀 함수.
    Polygon과 MultiPolygon 타입을 모두 정확하게 처리합니다.
    """
    if isinstance(geom, (list, tuple)):
        # 좌표의 가장 깊은 레벨에 도달했을 때 변환 수행
        if all(isinstance(coord, (int, float)) for coord in geom) and len(geom) == 2:
            return transformer.transform(geom[0], geom[1])
        # 아직 더 깊은 레벨이 있다면 재귀 호출
        return [transform_geom_coordinates(sub_geom) for sub_geom in geom]
    
    # 리스트나 튜플이 아니면 그대로 반환 (예: 딕셔너리)
    return geom


@app.route('/shadows', methods=['GET'])
def get_shadows():
    """
    쿼리 파라미터로 받은 시간과 위치에 대한 그림자 폴리곤을 GeoJSON으로 반환하는 API
    예: /shadows?lat=35.1706&lon=129.1305&time=15:00
    """
    try:
        # 1. 클라이언트 요청에서 파라미터 유효성 검사 및 추출
        lat_str = request.args.get('lat')
        lon_str = request.args.get('lon')
        time_str = request.args.get('time') # "HH:MM" 형식

        if not all([lat_str, lon_str, time_str]):
            return jsonify({"error": "Missing required parameters: lat, lon, time"}), 400

        lat = float(lat_str)
        lon = float(lon_str)
        hour, minute = map(int, time_str.split(':'))
        query_time = time(hour, minute)
        query_date = date.today()

        # 2. 태양 위치 계산
        elevation, azimuth = get_sun_position(lat, lon, query_date, query_time)
        if elevation is None or elevation <= 0:
            return jsonify({"type": "FeatureCollection", "features": []})

        # 3. 모든 건물에 대해 그림자 계산
        all_shadows = []
        for building_id, height, geom_wkt in BUILDINGS_DATA:
            shadow_poly = calculate_shadow_polygon(geom_wkt, height, elevation, azimuth)
            if shadow_poly and not shadow_poly.is_empty:
                all_shadows.append(shadow_poly)

        if not all_shadows:
            return jsonify({"type": "FeatureCollection", "features": []})

        # 4. 모든 그림자를 하나로 합치기
        total_shadow_area = unary_union(all_shadows)
        
        # 5. 결과를 GeoJSON으로 변환 및 좌표계 변환
        shadow_geojson = mapping(total_shadow_area)
        
        # 좌표 변환 적용 (재귀 함수 사용)
        shadow_geojson['coordinates'] = transform_geom_coordinates(shadow_geojson['coordinates'])

        # 최종 GeoJSON 형식으로 포장
        feature_collection = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": shadow_geojson,
                "properties": {"time": time_str}
            }]
        }
        
        return jsonify(feature_collection)

    except ValueError as ve:
        return jsonify({"error": f"Invalid parameter format: {ve}"}), 400
    except Exception as e:
        # 실제 운영 환경에서는 더 일반적인 오류 메시지를 보내는 것이 좋습니다.
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


# Flask 서버 실행
if __name__ == '__main__':
    # debug=True는 개발 중에만 사용하고, 실제 배포 시에는 False로 변경해야 합니다.
    app.run(debug=True, port=5001)