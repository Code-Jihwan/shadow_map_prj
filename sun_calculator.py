'''
태양 위치 및 그림자 계산 로직 구현하기
태양 위치 계산 함수 구현 (sun_calculator.py)
'''

from astral.location import LocationInfo
from astral.sun import elevation, azimuth
from datetime import datetime, date, time
import pytz # 시간대 처리를 위해 필요

def get_sun_position(lat: float, lon: float, query_date: date, query_time: time, timezone_str: str = 'Asia/Seoul'):
    """
    특정 위치, 날짜, 시간에 태양의 고도각(elevation)과 방위각(azimuth)을 계산합니다.

    Args:
        lat (float): 위도
        lon (float): 경도
        query_date (date): 조회하려는 날짜 (datetime.date 객체)
        query_time (time): 조회하려는 시간 (datetime.time 객체)
        timezone_str (str): 시간대 문자열 (예: 'Asia/Seoul', 'America/New_York')

    Returns:
        tuple: (elevation, azimuth) - 고도각(도), 방위각(도)
               계산 실패 시 (None, None) 반환.
    """
    try:
        # --- 수정된 부분: 다시 LocationInfo 클래스 사용 ---
        # 이 클래스는 라이브러리 내부에서 위도/경도 정보를 담은 .observer 속성을 제공합니다.
        loc = LocationInfo(
            name='Custom Location',
            region='Custom Region',
            timezone=timezone_str,
            latitude=lat,
            longitude=lon
        )

        # datetime 객체 생성 (시간대 정보 포함)
        tz = pytz.timezone(timezone_str)
        dt_with_tz = tz.localize(datetime.combine(query_date, query_time))

        # --- 수정된 부분: loc.observer를 elevation과 azimuth 함수에 전달 ---
        # 이렇게 하면 함수가 필요로 하는 정확한 Observer 객체가 전달됩니다.
        elev = elevation(loc.observer, dt_with_tz)
        azim = azimuth(loc.observer, dt_with_tz)

        return elev, azim

    except Exception as e:
        print(f"Error calculating sun position: {e}")
        return None, None

# --- 테스트 코드 (수정 없음) ---
if __name__ == "__main__":
    # 부산 센텀시티 대략적인 위경도 (예시)
    test_lat = 35.1706  # 위도
    test_lon = 129.1305 # 경도
    
    # 오늘 날짜로 계산
    test_date = date.today()
    print(f"Calculating for date: {test_date}")
    
    # 오전 9시
    elevation_09, azimuth_09 = get_sun_position(test_lat, test_lon, test_date, time(9, 0))
    if elevation_09 is not None and azimuth_09 is not None:
        print(f"09:00 - Elevation: {elevation_09:.2f}°, Azimuth: {azimuth_09:.2f}°")
    else:
        print("09:00 - Sun position calculation failed.")

    # 정오 12시
    elevation_12, azimuth_12 = get_sun_position(test_lat, test_lon, test_date, time(12, 0))
    if elevation_12 is not None and azimuth_12 is not None:
        print(f"12:00 - Elevation: {elevation_12:.2f}°, Azimuth: {azimuth_12:.2f}°")
    else:
        print("12:00 - Sun position calculation failed.")

    # 오후 3시
    elevation_15, azimuth_15 = get_sun_position(test_lat, test_lon, test_date, time(15, 0))
    if elevation_15 is not None and azimuth_15 is not None:
        print(f"15:00 - Elevation: {elevation_15:.2f}°, Azimuth: {azimuth_15:.2f}°")
    else:
        print("15:00 - Sun position calculation failed.")