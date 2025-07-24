# shadow_calculator.py (수정 및 개선 버전)

import math
from shapely.geometry import Polygon, MultiPoint
from shapely.wkt import loads as wkt_loads # (추가) WKT 문자열을 로드하기 위한 명시적인 함수

def deg2rad(degrees):
    return math.radians(degrees)

def calculate_shadow_polygon(building_geometry_wkt: str, building_height: float, sun_elevation: float, sun_azimuth: float):
    """
    단일 건물의 그림자 폴리곤을 계산합니다. (단순화된 모델)
    **주의: 입력되는 building_geometry_wkt는 반드시 미터 단위의 평면 좌표계여야 합니다.**

    Args:
        building_geometry_wkt (str): 건물의 WKT 폴리곤 문자열 (미터 단위 좌표계)
        building_height (float): 건물의 높이 (미터)
        sun_elevation (float): 태양의 고도각 (도, 0-90)
        sun_azimuth (float): 태양의 방위각 (도, 북쪽 0도 기준 시계방향)

    Returns:
        shapely.geometry.Polygon: 계산된 그림자 폴리곤 객체.
                                  그림자가 없거나 계산 실패 시 None 반환.
    """
    if sun_elevation <= 0:
        return None

    elevation_rad = deg2rad(sun_elevation)
    shadow_length = building_height / math.tan(elevation_rad)

    # (수정) 방위각을 수학적 각도(x축 양의 방향에서 반시계 방향)로 변환
    # 북쪽(0도) -> 90도, 동쪽(90도) -> 0도, 남쪽(180도) -> 270도(-90도)
    # math_azimuth = (450 - sun_azimuth) % 360
    # math_azimuth_rad = deg2rad(math_azimuth)
    
    # (수정) 더 직관적인 방법: 그림자 방향을 직접 계산
    # 그림자의 방향은 태양 방위각의 정반대 방향입니다.
    # sin, cos 함수는 북쪽(y축)이 0도가 아닌, 동쪽(x축)이 0도인 데카르트 좌표계를 기준으로 함
    # 태양 방위각(북쪽 기준 0도)을 데카르트 각도(동쪽 기준 0도)로 변환: (90 - azimuth)
    # 그림자는 반대 방향이므로, 이동 벡터를 계산할 때 -1을 곱해줌
    
    # 동쪽이 0도, 북쪽이 90도인 데카르트 좌표계에서의 태양 각도
    cartesian_azimuth_rad = deg2rad((90 - sun_azimuth + 360) % 360)

    # 그림자 변위 계산 (x, y 변화량)
    delta_x = -shadow_length * math.cos(cartesian_azimuth_rad)
    delta_y = -shadow_length * math.sin(cartesian_azimuth_rad)

    try:
        # (수정) shapely.wkt.loads 사용
        building_polygon = wkt_loads(building_geometry_wkt)
        
        exterior_coords = building_polygon.exterior.coords

        shadow_points = []
        for x, y in exterior_coords:
            shadow_points.append((x + delta_x, y + delta_y))

        # (수정) MultiPoint 객체를 사용하여 convex_hull을 더 안정적으로 계산
        all_points = MultiPoint(list(exterior_coords) + shadow_points)
        
        if len(all_points.geoms) < 3:
            return None

        shadow_polygon = all_points.convex_hull
        
        return shadow_polygon

    except Exception as e:
        print(f"Error calculating shadow for building: {e}")
        return None

# --- 테스트 코드 (수정됨) ---
if __name__ == "__main__":
    # (수정) 테스트용 건물 데이터를 미터 단위 평면 좌표계로 가정
    # 예: 한국 중부원점(EPSG:5186) 좌표계의 가상 건물
    # 실제 DB에서 가져온 데이터는 이런 형태일 것입니다.
    test_building_wkt = "POLYGON ((966400 1952200, 966400 1952250, 966450 1952250, 966450 1952200, 966400 1952200))"
    test_building_height = 50.0

    print("--- 테스트 케이스 1: 태양이 남쪽에 있을 때 (그림자는 북쪽으로) ---")
    test_sun_elevation_1 = 60.0
    test_sun_azimuth_1 = 180.0  # 남쪽
    shadow_poly_1 = calculate_shadow_polygon(test_building_wkt, test_building_height, test_sun_elevation_1, test_sun_azimuth_1)

    if shadow_poly_1:
        print(f"Calculated Shadow WKT: {shadow_poly_1.wkt}")
        # 예상: 건물 폴리곤이 북쪽(y축+)으로 길어진 형태
    else:
        print("No shadow calculated or sun is below horizon.")

    print("\n--- 테스트 케이스 2: 태양이 서쪽에 있을 때 (그림자는 동쪽으로) ---")
    test_sun_elevation_2 = 30.0
    test_sun_azimuth_2 = 270.0  # 서쪽
    shadow_poly_2 = calculate_shadow_polygon(test_building_wkt, test_building_height, test_sun_elevation_2, test_sun_azimuth_2)
    
    if shadow_poly_2:
        print(f"Low Sun Shadow WKT: {shadow_poly_2.wkt}")
        # 예상: 건물 폴리곤이 동쪽(x축+)으로 길어진 형태
    else:
        print("No shadow for low sun.")

    print("\n--- 테스트 케이스 3: 태양이 수평선 아래일 때 ---")
    shadow_poly_night = calculate_shadow_polygon(test_building_wkt, test_building_height, -5.0, 90.0)
    if shadow_poly_night:
        print(f"Night Sun Shadow WKT: {shadow_poly_night.wkt}")
    else:
        print("No shadow for night sun (as expected).")