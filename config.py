is_trial_trading = True
is_telegram_bot1 = True
is_acc_30954838 = True
# is_acc_30954838 (False : 계좌 60440040)

g_use_queue = True


SW_VERSION = "0.0.4"


# 장 시작/종료 시간 상수
d_MARKET_START_HOUR = 9
d_MARKET_START_MINUTE = 0
d_MARKET_END_HOUR = 15
d_MARKET_END_MINUTE = 30


r_MARKET_START_HOUR = 8
r_MARKET_START_MINUTE = 0
r_MARKET_END_HOUR = 20
r_MARKET_END_MINUTE = 0


MARKET_START_HOUR = d_MARKET_START_HOUR if is_trial_trading else r_MARKET_START_HOUR
MARKET_START_MINUTE = (
    d_MARKET_START_MINUTE if is_trial_trading else r_MARKET_START_MINUTE
)
MARKET_END_HOUR = d_MARKET_END_HOUR if is_trial_trading else r_MARKET_END_HOUR
MARKET_END_MINUTE = d_MARKET_END_MINUTE if is_trial_trading else r_MARKET_END_MINUTE


acc_30954838_app_key = "9I_5Z73Xjcc8DOeOKbmNbno7LLV0lmY1wtC8sJA7kc4"
acc_30954838_app_secret = "S_qgXiGOrXPSBk9rNO0ELrZnKE7j5TwF4xMeZZf5S7Y"


acc_60440040_app_key = "2LuKonusLQiXm4xgGm-qhQjcnT7a1x_M6sJNM5SpcTk"
acc_60440040_app_secret = "9dECWk3ayoAmIa5afhPPsA2pYIatLWdeosNyU6QewFs"


real_app_key = acc_30954838_app_key if is_acc_30954838 else acc_60440040_app_key
real_app_secret = (
    acc_30954838_app_secret if is_acc_30954838 else acc_60440040_app_secret
)


trial_app_key = "_HvK8LF6BSHSBZvrSoXwF4qQQKpz8Ey29IdKyiuPk2E"
trial_app_secret = "gxIGpzhNY7XGYfpQRPv8uOQSdOWXjZxdzbSt4_d31SY"


real_host_url = "https://api.kiwoom.com"
trial_host_url = "https://mockapi.kiwoom.com"

# real_socket_url = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
# trial_socket_url = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'

real_socket_url = "wss://api.kiwoom.com:10000"
trial_socket_url = "wss://mockapi.kiwoom.com:10000"


# telegram bot 1
telegram_chat_id_bot1 = "7796532423"
telegram_token_bot1 = "8429550471:AAF5yF2KAPD9Pbq6Pv-VQLkdSTmhCaIPTxY"

# telegram bot 2
telegram_chat_id_bot2 = "7796532423"
telegram_token_bot2 = "8387867127:AAEPHbNO9p0N52qWiMsqb-MlHXyRrbxzgOA"


#########
app_key = trial_app_key if is_trial_trading else real_app_key
app_secret = trial_app_secret if is_trial_trading else real_app_secret

host_url = trial_host_url if is_trial_trading else real_host_url
socket_url = trial_socket_url if is_trial_trading else real_socket_url


telegram_chat_id = telegram_chat_id_bot1 if is_telegram_bot1 else telegram_chat_id_bot2
telegram_token = telegram_token_bot1 if is_telegram_bot1 else telegram_token_bot2
