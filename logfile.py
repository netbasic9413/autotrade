import logging, logging.handlers
import os
import datetime

# from app.common.consts import HOSTNAME
# base_name = "autotrade"
# extension = ".log"


def setup_log(log_dir="logs"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()  # 또는 logger.removeHandler(handler)

    formatter = logging.Formatter(
        f"%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s"
    )

    # 로그 저장할 폴더 생성
    log_dir = "{}/logs".format(os.path.abspath(os.curdir))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")  # YYYY-MM-DD_HHMMSS 형식

    # 2. 기본 파일 이름과 확장자 설정
    base_name = "autotrade"
    extension = ".log"

    # 3. 날짜를 포함한 새로운 파일 이름 생성
    # log_filename = ""
    log_filename = f"{base_name}_{date_str}{extension}"  # 예: autotrade_2025-11-17.log

    # 로그 파일 경로 설정
    # os.path.exists(log_filename)
    log_path = os.path.join(log_dir, log_filename)

    # log 콘솔 출력
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # log를 파일에 출력
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_path, when="D", interval=1, encoding="utf-8"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    # file_handler.suffix = 'log_%Y%m%d'  # 파일명 끝에 붙여줌; ex. log_20190811
    file_handler.setFormatter(formatter)  # 핸들러에 로깅 포맷 할당
    logger.addHandler(file_handler)  # 로거에 핸들러 추가
    return logger
