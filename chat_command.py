import json
import os
import asyncio
from rt_search import RealTimeSearch
from tel_send import tel_send
from check_n_sell import chk_n_sell
from acc_val import fn_kt00004
from acc_balance import fn_kt00018
from daily_acc import fn_ka01690
from market_hour import MarketHour
from get_seq import get_condition_list
from login import fn_au10001
from get_setting import get_setting
from check_bal import fn_kt00001
from config import MARKET_START_HOUR
from config import MARKET_START_MINUTE
from config import MARKET_END_HOUR
from config import MARKET_END_MINUTE
import logfile


class ChatCommand:
    def __init__(self):
        self.rt_search = RealTimeSearch(on_connection_closed=self._on_connection_closed)
        # self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_dir = os.getcwd()
        self.settings_path = os.path.join(self.script_dir, "settings.json")
        self.check_n_sell_task = None  # check_n_sell 백그라운드 태스크
        self.token = None  # 현재 사용 중인 토큰
        self.logger = logfile.setup_log()

    def get_token(self, key_in=False):
        """새로운 토큰을 발급받습니다."""
        try:
            token = fn_au10001()
            if token:
                self.token = token
                self.logger.info(f"새로운 토큰 발급 완료: {token[:10]}...")
                return token
            else:
                self.logger.info("토큰 발급 실패")
                return None
        except Exception as e:
            self.logger.info(f"토큰 발급 중 오류: {e}")
            return None

    async def _on_connection_closed(self, key_in=False):
        """WebSocket 연결이 종료되었을 때 호출되는 콜백 함수"""
        try:
            self.logger.info("WebSocket 연결이 종료되어 자동으로 stop을 실행합니다.")
            if not key_in:
                tel_send("⚠️ 서버 연결이 끊어져 자동으로 서비스를 재시작합니다.")
            else:
                self.logger.info(
                    "[cli] ⚠️ 서버 연결이 끊어져 자동으로 서비스를 재시작합니다."
                )
            await self.stop(set_auto_start_false=False)  # auto_start는 그대로 유지

            self.logger.info("1초 후 서비스를 재시작합니다.")
            await asyncio.sleep(1)
            await self.start()
        except Exception as e:
            self.logger.info(f"연결 종료 콜백 실행 중 오류: {e}")
            if not key_in:
                tel_send(f"❌ 연결 종료 처리 중 오류가 발생했습니다: {e}")
            else:
                self.logger.info(f"[cli]❌ 연결 종료 처리 중 오류가 발생했습니다: {e}")

    def update_setting(self, key, value):
        """settings.json 파일의 특정 키 값을 업데이트합니다."""
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            settings[key] = value

            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            self.logger.info(f"설정 업데이트 실패: {e}")
            return False

    def get_csetting(self, key_in=False):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            prosess_name = settings.get("process_name")
            auto_start = settings.get("auto_start")
            search_seq = settings.get("search_seq")
            take_profit_rate = settings.get("take_profit_rate")
            stop_loss_rate = settings.get("stop_loss_rate")
            buy_ratio = settings.get("buy_ratio")
            bstop = settings.get("bstop")
            sstop = settings.get("sstop")
            smarket = settings.get("smarket")

            message = f"📋 [설정]\n"
            message += f"   process_name: {prosess_name}\n"
            message += f"   auto_start: {auto_start}\n"
            message += f"   search_seq: {search_seq}\n"
            message += f"   take_profit_rate: {take_profit_rate:+.1f}\n"
            message += f"   stop_loss_rate: {stop_loss_rate:+.1f}\n"
            message += f"   buy_ratio: {buy_ratio:+.1f}\n"
            message += f"   bstop: {bstop}\n"
            message += f"   sstop: {sstop}\n"
            message += f"   smarket: {smarket}\n"

            if not key_in:
                tel_send(message)
            else:
                self.logger.info("[cli] %s", message)
            return True

        except Exception as e:
            self.logger.info(f"설정 가져오는데 실패: {e}")
            return False

    async def _check_n_sell_loop(self, key_in=False):
        """check_n_sell을 1초마다 실행하는 백그라운드 루프"""
        failure_count = 0  # 연속 실패 횟수 카운터
        max_failures = 10  # 최대 허용 실패 횟수

        try:
            while True:
                try:
                    # chk_n_sell을 비동기로 실행하여 이벤트 루프 블로킹 방지
                    # 동기 HTTP 요청이 이벤트 루프를 블로킹하지 않도록 executor에서 실행
                    get_sell_stop = get_setting("sstop", False)
                    if not get_sell_stop:
                        success = await asyncio.get_event_loop().run_in_executor(
                            None, chk_n_sell, self.token
                        )
                        if success:
                            failure_count = 0  # 성공 시 실패 카운터 리셋
                        else:
                            failure_count += 1
                            self.logger.info(
                                f"chk_n_sell 실행 실패 ({failure_count}/{max_failures})"
                            )

                            # 10번 연속 실패 시 자동 재시작
                            if failure_count >= max_failures:
                                self.logger.info(
                                    f"chk_n_sell이 {max_failures}번 연속 실패하여 자동 재시작을 실행합니다."
                                )
                                if not key_in:
                                    tel_send(
                                        f"⚠️ chk_n_sell이 {max_failures}번 연속 실패하여 자동 재시작합니다."
                                    )
                                else:
                                    self.logger.info(
                                        f"⚠️ chk_n_sell이 {max_failures}번 연속 실패하여 자동 재시작합니다."
                                    )

                                # 현재 루프 중단
                                break
                    else:
                        self.logger.info("sstop이 실행 중...")

                except Exception as e:
                    failure_count += 1
                    self.logger.info(
                        f"chk_n_sell 실행 중 예외 발생 ({failure_count}/{max_failures}): {e}"
                    )

                    # 10번 연속 실패 시 자동 재시작
                    if failure_count >= max_failures:
                        self.logger.info(
                            f"chk_n_sell이 {max_failures}번 연속 실패하여 자동 재시작을 실행합니다."
                        )
                        if not key_in:
                            tel_send(
                                f"⚠️ 서버의 계좌 확인 기능 문제로 자동으로 서비스를 재시작합니다."
                            )
                        else:
                            self.logger.info(
                                f"[cli]⚠️ 서버의 계좌 확인 기능 문제로 자동으로 서비스를 재시작합니다."
                            )

                        # 현재 루프 중단
                        break

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.logger.info("check_n_sell 백그라운드 태스크가 중지되었습니다")
        except Exception as e:
            self.logger.info(f"check_n_sell 백그라운드 태스크 오류: {e}")

        # 10번 연속 실패로 루프가 종료된 경우 자동 재시작
        if failure_count >= max_failures:
            try:
                self.process_command("stop")
                self.process_command("start")
            except Exception as e:
                self.logger.info(f"자동 재시작 중 오류: {e}")
                if not key_in:
                    tel_send(f"❌ 자동 재시작 중 오류가 발생했습니다: {e}")
                else:
                    self.logger.info(
                        f"[cli] ❌ 자동 재시작 중 오류가 발생했습니다: {e}"
                    )

    async def start(self, key_in=False):
        """start 명령어를 처리합니다."""
        try:
            # 기존 check_n_sell 태스크가 실행 중이면 정지
            if self.check_n_sell_task and not self.check_n_sell_task.done():
                self.logger.info("기존 check_n_sell 태스크를 정지합니다")
                self.check_n_sell_task.cancel()
                try:
                    await self.check_n_sell_task
                except asyncio.CancelledError:
                    pass

            # 새로운 토큰 발급
            token = self.get_token()
            if not token:
                if not key_in:
                    tel_send("❌ 토큰 발급에 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 토큰 발급에 실패했습니다")
                return False

            # auto_start를 true로 설정
            if not self.update_setting("auto_start", True):
                if not key_in:
                    tel_send("❌ 설정 파일 업데이트 실패")
                else:
                    self.logger.info("[cli] ❌ 설정 파일 업데이트 실패")
                return False

            # andy
            # 장이 열리지 않았을 때는 auto_start만 설정하고 메시지 전송
            if not MarketHour.is_market_open_time():
                if not key_in:
                    tel_send(
                        f"⏰ 장이 열리지 않았습니다. 장 시작 시간({MARKET_START_HOUR:02d}:{MARKET_START_MINUTE:02d})에 자동으로 시작됩니다."
                    )
                else:
                    self.logger.info(
                        f"[cli] ⏰ 장이 열리지 않았습니다. 장 시작 시간({MARKET_START_HOUR:02d}:{MARKET_START_MINUTE:02d})에 자동으로 시작됩니다."
                    )
                return True

            # WebSocket 연결 재시도 로직
            max_retries = 5  # 최대 재시도 횟수
            retry_delay = 2  # 초기 재시도 간격 (초)

            for attempt in range(max_retries):
                try:
                    # rt_search의 start 실행 (토큰 전달)
                    success = await self.rt_search.start(token)

                    if success:
                        # check_n_sell 백그라운드 태스크 시작
                        self.check_n_sell_task = asyncio.create_task(
                            self._check_n_sell_loop()
                        )
                        if not key_in:
                            tel_send("✅ 실시간 검색과 자동 매도 체크가 시작되었습니다")
                        else:
                            self.logger.info(
                                "[cli] ✅ 실시간 검색과 자동 매도 체크가 시작되었습니다"
                            )
                        return True
                    else:
                        # 연결 실패 시 재시도
                        if attempt < max_retries - 1:  # 마지막 시도가 아닌 경우
                            self.logger.info(
                                f"WebSocket 연결 실패, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries})"
                            )
                            if not key_in:
                                tel_send(
                                    f"⚠️ WebSocket 연결 실패, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries})"
                                )
                            else:
                                self.logger.info(
                                    f"[cli] ⚠️ WebSocket 연결 실패, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries})"
                                )

                            # 지수 백오프: 재시도 간격을 점진적으로 증가
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * 1.5, 10)  # 최대 10초까지

                            # 토큰 갱신 (연결 실패 시 토큰이 만료되었을 가능성)
                            new_token = self.get_token()
                            if new_token:
                                token = new_token
                        else:
                            # 마지막 시도도 실패한 경우
                            self.logger.info(
                                f"WebSocket 연결이 {max_retries}번 연속 실패했습니다."
                            )
                            if not key_in:
                                tel_send(
                                    f"❌ WebSocket 연결이 {max_retries}번 연속 실패했습니다. 나중에 다시 'start' 명령어를 입력해주세요."
                                )
                            else:
                                self.logger.info(
                                    f"[cli] ❌ WebSocket 연결이 {max_retries}번 연속 실패했습니다. 나중에 다시 'start' 명령어를 입력해주세요."
                                )
                            return False

                except Exception as e:
                    if attempt < max_retries - 1:  # 마지막 시도가 아닌 경우
                        self.logger.info(
                            f"WebSocket 연결 중 오류 발생, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries}): {e}"
                        )
                        if not key_in:
                            tel_send(
                                f"⚠️ WebSocket 연결 중 오류 발생, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries})"
                            )
                        else:
                            self.logger.info(
                                f"[cli] ⚠️ WebSocket 연결 중 오류 발생, {retry_delay}초 후 재시도합니다... ({attempt + 1}/{max_retries})"
                            )

                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 10)  # 최대 10초까지

                        # 토큰 갱신
                        new_token = self.get_token()
                        if new_token:
                            token = new_token
                    else:
                        # 마지막 시도도 실패한 경우
                        self.logger.info(
                            f"WebSocket 연결이 {max_retries}번 연속 실패했습니다: {e}"
                        )
                        if not key_in:
                            tel_send(
                                f"❌ WebSocket 연결이 {max_retries}번 연속 실패했습니다: {e}"
                            )
                        else:
                            self.logger.info(
                                f"[cli] ❌ WebSocket 연결이 {max_retries}번 연속 실패했습니다: {e}"
                            )
                        return False

            return False

        except Exception as e:
            if not key_in:
                tel_send(
                    f"❌ start 명령어 실행 중 오류: {e}\n계속 재시작이 되지 않으면 'start' 명령어를 다시 입력해주세요."
                )
            else:
                self.logger.info(
                    f"[cli]❌ start 명령어 실행 중 오류: {e}\n계속 재시작이 되지 않으면 'start' 명령어를 다시 입력해주세요."
                )
            return False

    async def stop(self, set_auto_start_false=True, key_in=False):
        """stop 명령어를 처리합니다."""
        try:
            # auto_start 설정 (사용자 명령일 때만 false로 설정)
            if set_auto_start_false:
                if not self.update_setting("auto_start", False):
                    if not key_in:
                        tel_send("❌ 설정 파일 업데이트 실패")
                    else:
                        self.logger.info("[cli]❌ 설정 파일 업데이트 실패")
                    return False

            # check_n_sell 백그라운드 태스크 정지
            if self.check_n_sell_task and not self.check_n_sell_task.done():
                self.logger.info("check_n_sell 백그라운드 태스크를 정지합니다")
                self.check_n_sell_task.cancel()
                try:
                    await self.check_n_sell_task
                except asyncio.CancelledError:
                    pass

            # rt_search의 stop 실행
            success = await self.rt_search.stop()

            if success:
                if not key_in:
                    tel_send("✅ 실시간 검색과 자동 매도 체크가 중지되었습니다")
                else:
                    self.logger.info(
                        "[cli]✅ 실시간 검색과 자동 매도 체크가 중지되었습니다"
                    )
                return True
            else:
                if not key_in:
                    tel_send("❌ 실시간 검색 중지에 실패했습니다")
                else:
                    self.logger.info("[cli]❌ 실시간 검색 중지에 실패했습니다")
                return False

        except Exception as e:
            if not key_in:
                tel_send(f"❌ stop 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ stop 명령어 실행 중 오류: {e}")
            return False

    async def report(self, key_in=False):
        """report 명령어를 처리합니다 - acc_val 실행 결과를 텔레그램으로 발송"""
        try:
            # 토큰이 없으면 새로 발급
            if not self.token:
                token = self.get_token()
                if not token:
                    tel_send("❌ 토큰 발급에 실패했습니다")
                return False

            # acc_val 실행 (타임아웃 10초)
            try:
                account_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, fn_kt00004, False, "N", "", self.token
                    ),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                if not key_in:
                    tel_send(
                        "⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                else:
                    self.logger.info(
                        "[cli]⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                return False

            if not account_data:
                if not key_in:
                    tel_send("📊 계좌평가현황 데이터가 없습니다.")
                else:
                    self.logger.info("[cli]📊 계좌평가현황 데이터가 없습니다.")
                return False

            # 데이터 정리 및 포맷팅
            message = "📊 [계좌평가현황 보고서]\n\n"

            total_profit_loss = 0
            total_pl_amt = 0
            total_pur_amt = 0

            for stock in account_data:
                stock_code = stock.get("stk_cd", "N/A")
                stock_name = stock.get("stk_nm", "N/A")
                profit_loss_rate = float(stock.get("pl_rt", 0))
                pl_amt = int(stock.get("pl_amt", 0))
                remaining_qty = int(stock.get("rmnd_qty", 0))
                pur_amt = float(stock.get("pur_amt", 0))

                # 수익률에 따른 이모지 설정
                if profit_loss_rate > 0:
                    emoji = "🔴"
                elif profit_loss_rate < 0:
                    emoji = "🔵"
                else:
                    emoji = "➡️"

                message += f"{emoji} [{stock_name}] ({stock_code})\n"
                message += f"   수익률: {profit_loss_rate:+.2f}%\n"
                message += f"   평가손익: {pl_amt:,.0f}원\n"
                message += f"   보유수량: {remaining_qty:,}주\n"
                message += f"   매입금액: {pur_amt:,.0f}원\n\n"

                total_profit_loss += profit_loss_rate
                total_pl_amt += pl_amt
                total_pur_amt += pur_amt

            # 전체 요약
            avg_profit_loss = (
                total_profit_loss / len(account_data) if account_data else 0
            )
            message += f"📋 [전체 요약]\n"
            message += f"   총 보유종목: {len(account_data)}개\n"
            message += f"   평균 수익률: {avg_profit_loss:+.2f}%\n"
            message += f"   총 평가손익: {total_pl_amt:,.0f}원\n"
            message += f"   총 매입금액: {total_pur_amt:,.0f}원\n\n"

            if not key_in:
                tel_send(message)
            else:
                self.logger.info(message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ report 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ report 명령어 실행 중 오류: {e}")
            return False

    async def dep(self, key_in=False):
        """dep 명령을 처리"""
        try:
            # 토큰이 없으면 새로 발급
            if not self.token:
                token = self.get_token()
                self.token = token
                if not token:
                    tel_send("❌ 토큰 발급에 실패했습니다")
                return False

            try:
                balance = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, fn_kt00001, "N", "", self.token
                    ),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                if not key_in:
                    tel_send(
                        "⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                else:
                    self.logger.info(
                        "[cli]⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                return False

            if not balance:
                if not key_in:
                    tel_send("📊 예수금 내역요청 데이터가 없습니다.")
                else:
                    self.logger.info("[cli]📊 예수금 내역요청 데이터가 없습니다.")
                return False

            entr = balance.json()["entr"]
            f_entr = float(entr)
            d2_entra = balance.json()["d2_entra"]
            f_d2_entra = float(d2_entra)

            message = "📊 [예수금 내역]\n\n"
            message += f"   예수금: {f_entr:,.0f}원\n"
            message += f"   D+2추정예수금: {f_d2_entra:,.0f}원\n"

            if not key_in:
                tel_send(message)
            else:
                self.logger.info("[cli] %s", message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ dep 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ dep 명령어 실행 중 오류: {e}")
                return False

    async def acc(self, key_in=False):
        """acc 명령어를 처리합니다 - acc_balance 실행 결과를 텔레그램으로 발송"""
        try:
            # 토큰이 없으면 새로 발급
            if not self.token:
                token = self.get_token()
                if not token:
                    tel_send("❌ 토큰 발급에 실패했습니다")
                return False

            # acc_balance 실행 (타임아웃 10초)
            try:
                account_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, fn_kt00018, False, "N", "", self.token
                    ),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                if not key_in:
                    tel_send(
                        "⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                else:
                    self.logger.info(
                        "[cli]⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                return False

            if not account_data:
                if not key_in:
                    tel_send("📊 계좌평가잔고내역요청 데이터가 없습니다.")
                else:
                    self.logger.info("[cli] 📊 계좌평가잔고내역요청 데이터가 없습니다.")
                return False

            # balance = int(get_balance(self.get_token()))

            # 데이터 정리 및 포맷팅
            message = "📊 [계좌평가잔고내역]\n\n"

            # for stock in account_data:
            total_pur_amt = float(account_data.get("tot_pur_amt", 0))  # 총매입금액
            total_evlt_amt = float(account_data.get("tot_evlt_amt", 0))  # 총평가금액
            total_evlt_pl = float(account_data.get("tot_evlt_pl", 0))  # 총평가손익금
            total_prft_rt = float(account_data.get("tot_prft_rt", 0))  # 총수익률(%)

            # stock_nm = stock.get("stk_nm", "N/A")  # 종목명
            # eval_prtf = stock.get("evltv_prft", "N/A")  # 평가손익
            # profit_rt = float(stock.get("prft_rt", 0))  # 수익률(%)
            # pur_price = stock.get("pur_pric", "N/A")  # 매입가
            # have_qty = stock.get("rmnd_qty", "N/A")  # 보유수량
            # pur_amount = stock.get("pur_amt", "N/A")  # 매입금액
            # eval_amount = stock.get("evlt_amt", "N/A")  # 평가금액

            message += f"   총매입금액: {total_pur_amt:,.0f}원\n"
            message += f"   총평가금액: {total_evlt_amt:,.0f}원\n"
            message += f"   총평가손익금: {total_evlt_pl:,.0f}원\n"
            message += f"   총수익률: {total_prft_rt:+.2f}%\n"
            # message += f"   예수금: {balance:,.0f}원\n"

            # message += f"   매입가: {pur_price:,.0f}원\n"
            # message += f"   보유수량: {have_qty:,}주\n\n"
            # message += f"   매입금액: {pur_amount:,.0f}원\n"
            # message += f"   평가금액: {eval_amount:,.0f}원\n"

            if not key_in:
                tel_send(message)
            else:
                self.logger.info("[cli] %s", message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ acc 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ acc 명령어 실행 중 오류: {e}")
            return False

    async def dacc(self, key_in=False):
        """dacc 명령어를 처리합니다 - daily account 실행 결과를 텔레그램으로 발송"""
        try:
            # 토큰이 없으면 새로 발급
            if not self.token:
                token = self.get_token()
                if not token:
                    tel_send("❌ 토큰 발급에 실패했습니다")
                return False

            # daily_acc 실행 (타임아웃 10초)
            try:
                account_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, fn_ka01690, "N", "", self.token
                    ),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                if not key_in:
                    tel_send(
                        "⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                else:
                    self.logger.info(
                        "[cli]⏰ 서버로부터 응답이 늦어지고 있습니다. 나중에 다시 시도해주세요."
                    )
                return False

            if not account_data:
                if not key_in:
                    tel_send("📊 일별잔고수익률요청 데이터가 없습니다.")
                else:
                    self.logger.info("[cli] 📊 일별잔고수익률요청 데이터가 없습니다.")
                return False

            # 데이터 정리 및 포맷팅
            message = "📊 [일별잔고수익률내역]\n\n"

            # for stock in account_data:
            total_buy_amt = float(account_data.get("tot_buy_amt", 0))  # 총매입금액
            total_evlt_amt = float(account_data.get("tot_evlt_amt", 0))  # 총평가금액
            total_evlt_prft = float(
                account_data.get("tot_evltv_prft", 0)
            )  # 총평가손익금
            total_prft_rt = float(account_data.get("tot_prft_rt", 0))  # 수익률(%)

            message += f"   총매입금액: {total_buy_amt:,.0f}원\n"
            message += f"   총평가금액: {total_evlt_amt:,.0f}원\n"
            message += f"   총평가손익금: {total_evlt_prft:,.0f}원\n"
            message += f"   총수익률: {total_prft_rt:+.2f}%\n"

            if not key_in:
                tel_send(message)
            else:
                self.logger.info("[cli] %s", message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ acc 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ acc 명령어 실행 중 오류: {e}")
            return False

    async def tpr(self, number, key_in=False):
        """tpr 명령어를 처리합니다 - take_profit_rate 수정"""
        try:
            rate = float(number)
            if self.update_setting("take_profit_rate", rate):
                if not key_in:
                    tel_send(f"✅ 익절 기준이 {rate}%로 설정되었습니다")
                else:
                    self.logger.info(f"[cli] ✅ 익절 기준이 {rate}%로 설정되었습니다")
                return True
            else:
                if not key_in:
                    tel_send("❌ 익절 기준 설정에 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 익절 기준 설정에 실패했습니다")
                return False
        except ValueError:
            if not key_in:
                tel_send("❌ 잘못된 숫자 형식입니다. 예: tpr 5")
            else:
                self.logger.info("[cli] ❌ 잘못된 숫자 형식입니다. 예: tpr 5")
            return False
        except Exception as e:
            if not key_in:
                tel_send(f"❌ tpr 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ tpr 명령어 실행 중 오류: {e}")
            return False

    async def slr(self, number, key_in=False):
        """slr 명령어를 처리합니다 - stop_loss_rate 수정"""
        try:
            rate = float(number)
            if rate > 0:
                rate = -rate
            if self.update_setting("stop_loss_rate", rate):
                if not key_in:
                    tel_send(f"✅ 손절 기준이 {rate}%로 설정되었습니다")
                else:
                    self.logger.info(f"[cli] ✅ 손절 기준이 {rate}%로 설정되었습니다")
                return True
            else:
                if not key_in:
                    tel_send("❌ 손절 기준 설정에 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 손절 기준 설정에 실패했습니다")
                return False
        except ValueError:
            if not key_in:
                tel_send("❌ 잘못된 숫자 형식입니다. 예: slr -10")
            else:
                self.logger.info("[cli] ❌ 잘못된 숫자 형식입니다. 예: slr -10")
            return False
        except Exception as e:
            if not key_in:
                tel_send(f"❌ slr 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ slr 명령어 실행 중 오류: {e}")
            return False

    async def brt(self, number, key_in=False):
        """brt 명령어를 처리합니다 - buy_ratio 수정"""
        try:
            ratio = float(number)
            if self.update_setting("buy_ratio", ratio):
                if not key_in:
                    tel_send(f"✅ 매수 비용 비율이 {ratio}%로 설정되었습니다")
                else:
                    self.logger.info(
                        f"[cli] ✅ 매수 비용 비율이 {ratio}%로 설정되었습니다"
                    )
                return True
            else:
                if not key_in:
                    tel_send("❌ 매수 비용 비율 설정에 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 매수 비용 비율 설정에 실패했습니다")
                return False
        except ValueError:
            if not key_in:
                tel_send("❌ 잘못된 숫자 형식입니다. 예: brt 3")
            else:
                self.logger.info("[cli] ❌ 잘못된 숫자 형식입니다. 예: brt 3")
            return False
        except Exception as e:
            if not key_in:
                tel_send(f"❌ brt 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ brt 명령어 실행 중 오류: {e}")
            return False

    async def cget(self, key_in=False):
        try:
            if self.get_csetting(key_in):
                return True
            else:
                if not key_in:
                    tel_send("❌ 설정을 가져오는데 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 설정을 가져오는데 실패했습니다")
                return False
        except Exception as e:
            if not key_in:
                tel_send(f"❌ cget 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ cget 명령어 실행 중 오류: {e}")
            return False

    async def buy_stop(self, key_in=False):
        if not self.update_setting("bstop", True):
            if not key_in:
                tel_send("❌ buy_stop 설정 파일 업데이트 실패")
            else:
                self.logger.info("[cli] ❌ buy_stop 설정 파일 업데이트 실패")
            return False
        else:
            if not key_in:
                tel_send("⭕ buy_stop 설정")
            else:
                self.logger.info("[cli] ⭕ buy_stop 설정")
            return True

    async def buy_go(self, key_in=False):
        if not self.update_setting("bstop", False):
            if not key_in:
                tel_send("❌ buy_go 설정 파일 업데이트 실패")
            else:
                self.logger.info("[cli] ❌ buy_go 설정 파일 업데이트 실패")
            return False
        else:
            if not key_in:
                tel_send("⭕ buy_go 설정")
            else:
                self.logger.info("[cli] ⭕ buy_go 설정")
            return True

    async def sell_stop(self, key_in=False):
        if not self.update_setting("sstop", True):
            if not key_in:
                tel_send("❌ sell_stop 설정 파일 업데이트 실패")
            else:
                self.logger.info("[cli] ❌ sell_stop 설정 파일 업데이트 실패")
            return False
        else:
            if not key_in:
                tel_send("⭕ sell_stop 설정")
            else:
                self.logger.info("[cli] ⭕ sell_stop 설정")
            return True

    async def sell_go(self, key_in=False):
        if not self.update_setting("sstop", False):
            if not key_in:
                tel_send("❌ sell_go 설정 파일 업데이트 실패")
            else:
                self.logger.info("[cli] ❌ sell_go 설정 파일 업데이트 실패")
            return False
        else:
            if not key_in:
                tel_send("⭕ sell_go 설정")
            else:
                self.logger.info("[cli] ⭕ sell_go 설정")
            return True

    async def smarket(self, number, key_in=False):
        """sm 명령어를 처리합니다 - smarket 수정"""
        try:
            market_num = int(number)
            if self.update_setting("smarket", market_num):
                if not key_in:
                    tel_send(f"✅ 거래소 {market_num}로 설정되었습니다")
                else:
                    self.logger.info(f"[cli] ✅ 거래소 {market_num}로 설정되었습니다")
                return True
            else:
                if not key_in:
                    tel_send("❌ 거래소 설정에 실패했습니다")
                else:
                    self.logger.info("[cli] ❌ 거래소 설정에 실패했습니다")
                return False
        except ValueError:
            if not key_in:
                tel_send("❌ 잘못된 숫자 형식입니다. 예: sm 1")
            else:
                self.logger.info("[cli] ❌ 잘못된 숫자 형식입니다. 예: sm 1")
            return False
        except Exception as e:
            if not key_in:
                tel_send(f"❌ sm 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ sm 명령어 실행 중 오류: {e}")
            return False

    async def condition(self, number=None, key_in=False):
        """condition 명령어를 처리합니다 - 조건식 목록 조회 또는 search_seq 설정"""
        try:
            # 먼저 stop 실행
            if not key_in:
                tel_send("🔄 condition 명령어 실행을 위해 서비스를 중지합니다...")
            else:
                self.logger.info(
                    "[cli]🔄 condition 명령어 실행을 위해 서비스를 중지합니다..."
                )
            await self.stop(set_auto_start_false=False)  # auto_start는 그대로 유지

            # 숫자가 제공된 경우 search_seq 설정
            if number is not None:
                try:
                    seq_number = str(number)
                    if self.update_setting("search_seq", seq_number):
                        if not key_in:
                            tel_send(
                                f"✅ 검색 조건식이 {seq_number}번으로 설정되었습니다"
                            )
                        else:
                            self.logger.info(
                                f"[cli] ✅ 검색 조건식이 {seq_number}번으로 설정되었습니다"
                            )

                        # 장 시간일 경우 자동으로 start 실행
                        if MarketHour.is_market_open_time():
                            if not key_in:
                                tel_send("🔄 장 시간이므로 자동으로 재시작합니다...")
                            else:
                                self.logger.info(
                                    "[cli] 🔄 장 시간이므로 자동으로 재시작합니다..."
                                )

                            # 잠시 대기
                            await asyncio.sleep(2)

                            # 새로운 설정으로 시작
                            success = await self.start()
                            if success:
                                if not key_in:
                                    tel_send("✅ 새로운 조건식으로 재시작되었습니다")
                                else:
                                    self.logger.info(
                                        "[cli]✅ 새로운 조건식으로 재시작되었습니다"
                                    )
                            else:
                                if not key_in:
                                    tel_send("❌ 재시작에 실패했습니다")
                                else:
                                    self.logger.info("[cli]❌ 재시작에 실패했습니다")
                        else:
                            if not key_in:
                                tel_send(
                                    f"⏰ 장이 열리지 않았습니다. 장 시작 시간({MARKET_START_HOUR:02d}:{MARKET_START_MINUTE:02d})에 자동으로 시작됩니다."
                                )
                            else:
                                self.logger.info(
                                    f"[cli]⏰ 장이 열리지 않았습니다. 장 시작 시간({MARKET_START_HOUR:02d}:{MARKET_START_MINUTE:02d})에 자동으로 시작됩니다."
                                )

                        return True
                    else:
                        if not key_in:
                            tel_send("❌ 검색 조건식 설정에 실패했습니다")
                        else:
                            self.logger.info("[cli]❌ 검색 조건식 설정에 실패했습니다")
                        return False
                except ValueError:
                    if not key_in:
                        tel_send("❌ 잘못된 숫자 형식입니다. 예: condition 0")
                    else:
                        self.logger.info(
                            "[cli]❌ 잘못된 숫자 형식입니다. 예: condition 0"
                        )
                    return False

            # 숫자가 제공되지 않은 경우 조건식 목록 조회
            # 조건식 목록 가져오기 (타임아웃 10초로 단축)
            try:
                condition_data = await asyncio.wait_for(
                    get_condition_list(self.token), timeout=10.0
                )
            except asyncio.TimeoutError:
                if not key_in:
                    tel_send(
                        "⏰ 조건식 목록 조회가 시간 초과되었습니다. 나중에 다시 시도해주세요."
                    )
                else:
                    self.logger.info(
                        "[cli]⏰ 조건식 목록 조회가 시간 초과되었습니다. 나중에 다시 시도해주세요."
                    )
                return False

            if not condition_data:
                if not key_in:
                    tel_send("📋 조건식 목록이 없습니다.")
                else:
                    self.logger.info("[cli]📋 조건식 목록이 없습니다.")
                return False

            # 조건식 목록 포맷팅
            message = "📋 [조건식 목록]\n\n"

            for condition in condition_data:
                condition_id = condition[0] if len(condition) > 0 else "N/A"
                condition_name = condition[1] if len(condition) > 1 else "N/A"
                message += f"• {condition_id}: {condition_name}\n"

            message += "\n💡 사용법: condition {번호} (예: condition 0)"
            if not key_in:
                tel_send(message)
            else:
                self.logger.info("[cli] %s", message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ condition 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli]❌ condition 명령어 실행 중 오류: {e}")
            return False

    async def help(self, key_in=False):
        """help 명령어를 처리합니다 - 명령어 설명 및 사용법 가이드"""
        try:
            help_message = """🤖 [키움 REST API 봇 명령어 가이드]

[기본 명령어]
• start - 실시간 검색과 자동 매도 체크 시작
• stop - 실시간 검색과 자동 매도 체크 중지
• report 또는 r - 계좌평가현황 보고서 발송
• cond - 조건식 목록 조회
• cond {번호} - 검색 조건식 변경 (예: cond 0)
• acc - 계좌정보
• bstop - 실시간 매수 정지
• bgo - 실시간 매수 다시 시작
• sstop - 실시간 매도 정지
• sgo - 실시간 매도 다시 시작
• cget - 설정 가져오기
• dep - 예수금 조회

[설정 명령어]
• tpr {숫자} - 익절 기준 설정 (예: tpr 5)
• slr {숫자} - 손절 기준 설정 (양수 입력 시 음수로 변환)
• brt {숫자} - 매수 비용 비율 설정 (예: brt 3)

[사용 예시]
• tpr 5 (수익률 5%에서 매도)
• slr 10 (손실률 -10%에서 매도)
• brt 3 (매수 비율 3%로 설정)
• cond 0 (0번 조건식으로 변경)

[도움말]
• help 또는 h - 이 도움말 표시

모든 명령어는 퍼센트 단위로 입력하세요."""

            if not key_in:
                tel_send(help_message)
            else:
                self.logger.info("[cli] %s", help_message)
            return True

        except Exception as e:
            if not key_in:
                tel_send(f"❌ help 명령어 실행 중 오류: {e}")
            else:
                self.logger.info(f"[cli] ❌ help 명령어 실행 중 오류: {e}")
            return False

    async def process_command(self, text, key_in=False):
        """텍스트 명령어를 처리합니다."""
        # 텍스트 trim 및 소문자 변환
        command = text.strip().lower()

        if command == "start":
            return await self.start(key_in)
        elif command == "stop":
            return await self.stop(
                True, key_in
            )  # 사용자 명령이므로 auto_start를 false로 설정
        elif command == "report" or command == "r":
            return await self.report(key_in)
        elif command == "acc":
            return await self.acc(key_in)
        elif command == "dacc":
            return await self.dacc(key_in)
        elif command == "dep":
            return await self.dep(key_in)
        elif command == "cond":
            return await self.condition(None, key_in)
        elif command.startswith("cond "):
            # condition 명령어 처리
            parts = command.split()
            if len(parts) == 2:
                return await self.condition(parts[1], key_in)
            else:
                if not key_in:
                    tel_send("❌ 사용법: cond {번호} (예: cond 0)")
                else:
                    self.logger.info("[cli]❌ 사용법: cond {번호} (예: cond 0)")
                return False
        elif command == "help" or command == "h":
            return await self.help(key_in)
        elif command == "cget":
            return await self.cget(key_in)
        elif command == "bstop":
            return await self.buy_stop(key_in)
        elif command == "bgo":
            return await self.buy_go(key_in)
        elif command == "sstop":
            return await self.sell_stop(key_in)
        elif command == "sgo":
            return await self.sell_go(key_in)
        elif command.startswith("tpr "):
            # tpr 명령어 처리
            parts = command.split()
            if len(parts) == 2:
                return await self.tpr(parts[1], key_in)
            else:
                if not key_in:
                    tel_send("❌ 사용법: tpr {숫자} (예: tpr 5)")
                else:
                    self.logger.info("[cli]❌ 사용법: tpr {숫자} (예: tpr 5)")
                return False
        elif command.startswith("slr "):
            # slr 명령어 처리
            parts = command.split()
            if len(parts) == 2:
                return await self.slr(parts[1], key_in)
            else:
                if not key_in:
                    tel_send("❌ 사용법: slr {숫자} (예: slr -10)")
                else:
                    self.logger.info("[cli]❌ 사용법: slr {숫자} (예: slr -10)")
                return False
        elif command.startswith("brt "):
            # brt 명령어 처리
            parts = command.split()
            if len(parts) == 2:
                return await self.brt(parts[1], key_in)
            else:
                if not key_in:
                    tel_send("❌ 사용법: brt {숫자} (예: brt 3)")
                else:
                    self.logger.info("[cli]❌ 사용법: brt {숫자} (예: brt 3)")
                return False
        elif command.startswith("sm "):
            # sm 명령어 처리
            parts = command.split()
            if len(parts) == 2:
                return await self.smarket(parts[1], key_in)
            else:
                if not key_in:
                    tel_send("❌ 사용법: sm {숫자} (예: sm 1)")
                else:
                    self.logger.info("[cli]❌ 사용법: sm {숫자} (예: sm 1)")
                return False
        else:
            if not key_in:
                tel_send(f"❓ 알 수 없는 명령어입니다: {text}")
            else:
                self.logger.info("[cli] ❓ 알 수 없는 명령어입니다: {text}")
            return False
