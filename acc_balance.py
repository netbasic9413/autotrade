import requests
import json
from config import host_url
from login import fn_au10001 as get_token
import logfile


logger = logfile.setup_log()


# fn_kt00004(print_df=False, cont_yn='N', next_key='', token=None):
# 계좌평가잔고내역요청
def fn_kt00018(print_df=False, cont_yn="N", next_key="", token=None):
    # 1. 요청할 API URL
    endpoint = "/api/dostk/acnt"
    url = host_url + endpoint

    # 2. header 데이터
    headers = {
        "Content-Type": "application/json;charset=UTF-8",  # 컨텐츠타입
        "authorization": f"Bearer {token}",  # 접근토큰
        "cont-yn": cont_yn,  # 연속조회여부
        "next-key": next_key,  # 연속조회키
        "api-id": "kt00018",  # TR명
    }

    # 2. 요청 데이터
    params = {
        "qry_tp": "1",  # 조회구분 1:합산, 2:개별
        "dmst_stex_tp": "KRX",  # 국내거래소구분 KRX:한국거래소,NXT:넥스트트레이드
    }

    # 3. http POST 요청
    response = requests.post(url, headers=headers, json=params)
    acc_evlt_remn_indv_tot = response.json()
    if not acc_evlt_remn_indv_tot:
        return []

    # 4. 응답 상태 코드와 데이터 출력
    logger.info("Code: %d", response.status_code)
    logger.info(
        "Header: %s",
        json.dumps(
            {
                key: response.headers.get(key)
                for key in ["next-key", "cont-yn", "api-id"]
            },
            indent=4,
            ensure_ascii=False,
        ),
    )
    logger.info(
        "Body: %s", json.dumps(response.json(), indent=4, ensure_ascii=False)
    )  # JSON 응답을 파싱하여 출력

    return acc_evlt_remn_indv_tot


# 실행 구간
if __name__ == "__main__":

    # 3. API 실행
    fn_kt00018(True, token=get_token())

    # next-key, cont-yn 값이 있을 경우
    # fn_kt00018(token=MY_ACCESS_TOKEN, data=params, cont_yn='Y', next_key='nextkey..')
