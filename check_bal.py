import requests
import json
from config import host_url
from login import fn_au10001 as get_token
import logfile


logger = logfile.setup_log()


# 예수금상세현황요청
def fn_kt00001(cont_yn="N", next_key="", token=None):
    # 1. 요청할 API URL
    endpoint = "/api/dostk/acnt"
    url = host_url + endpoint

    # 1. 토큰 설정
    # token = get_token() # 접근토큰

    # 2. 요청 데이터
    params = {
        "qry_tp": "3",  # 조회구분 3:추정조회, 2:일반조회
    }

    # 2. header 데이터
    headers = {
        "Content-Type": "application/json;charset=UTF-8",  # 컨텐츠타입
        "authorization": f"Bearer {token}",  # 접근토큰
        "cont-yn": cont_yn,  # 연속조회여부
        "next-key": next_key,  # 연속조회키
        "api-id": "kt00001",  # TR명
    }

    # 3. http POST 요청
    response = requests.post(url, headers=headers, json=params)

    # 4. 응답 상태 코드와 데이터 출력
    logger.info("Code: %d", response.status_code)
    logger.info(
        "Body: %s", json.dumps(response.json(), indent=4, ensure_ascii=False)
    )  # JSON 응답을 파싱하여 출력

    ret_code = response.json()["return_code"]
    if int(ret_code) != 0:
        return ""

    entry = response.json()["entr"]
    logger.info("예수금: %s", entry)
    return entry


# 실행 구간
if __name__ == "__main__":
    fn_kt00001(token=get_token())
