import requests
import json
from config import host_url
from login import fn_au10001 as get_token
import logfile


# 당일실현손익상세요청
def fn_ka10077(stk_cd, cont_yn="N", next_key="", token=None):
    endpoint = "/api/dostk/acnt"
    url = host_url + endpoint

    # 2. header 데이터
    headers = {
        "Content-Type": "application/json;charset=UTF-8",  # 컨텐츠타입
        "authorization": f"Bearer {token}",  # 접근토큰
        "cont-yn": cont_yn,  # 연속조회여부
        "next-key": next_key,  # 연속조회키
        "api-id": "ka10077",  # TR명
    }

    # 2. 요청 데이터
    params = {
        "stk_cd": stk_cd,  # 종목코드
    }

    # 3. http POST 요청
    response = requests.post(url, headers=headers, json=params)

    # 4. 응답 상태 코드와 데이터 출력
    print("Code:", response.status_code)
    print(
        "Header:",
        json.dumps(
            {
                key: response.headers.get(key)
                for key in ["next-key", "cont-yn", "api-id"]
            },
            indent=4,
            ensure_ascii=False,
        ),
    )
    print(
        "Body:", json.dumps(response.json(), indent=4, ensure_ascii=False)
    )  # JSON 응답을 파싱하여 출력

    tdy_rlzt_pl_dtl = response.json()["tdy_rlzt_pl_dtl"]
    f_c = 0
    i = 0
    for get_d in tdy_rlzt_pl_dtl:
        tdy_sel_p = float(tdy_rlzt_pl_dtl[i].get("tdy_sel_pl", 0))
        f_c = float(tdy_sel_p)
        f_c += f_c
        i += 1

    return f_c


# 실행 구간
if __name__ == "__main__":
    # 1. 토큰 설정
    # MY_ACCESS_TOKEN = "사용자 AccessToken"  # 접근토큰

    # 3. API 실행
    fn_ka10077("005930", token=get_token())

    # next-key, cont-yn 값이 있을 경우
    # fn_ka10077(token=MY_ACCESS_TOKEN, data=params, cont_yn='Y', next_key='nextkey..')
