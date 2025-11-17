is_trial_trading = True


real_app_key = ""
real_app_secret = ""

trial_app_key = '_HvK8LF6BSHSBZvrSoXwF4qQQKpz8Ey29IdKyiuPk2E'
trial_app_secret = 'gxIGpzhNY7XGYfpQRPv8uOQSdOWXjZxdzbSt4_d31SY'


real_host_url = 'https://api.kiwoom.com'
trial_host_url = 'https://mockapi.kiwoom.com'

#real_socket_url = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
#trial_socket_url = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'

real_socket_url = 'wss://api.kiwoom.com:10000'
trial_socket_url = 'wss://mockapi.kiwoom.com:10000'

#########
app_key = trial_app_key if is_trial_trading else real_app_key
app_secret = trial_app_secret if is_trial_trading else real_app_secret

host_url = trial_host_url if is_trial_trading else real_host_url
socket_url = trial_socket_url if is_trial_trading else real_socket_url



#telegram bot 
telegram_chat_id = "7796532423"
telegram_token = "8429550471:AAF5yF2KAPD9Pbq6Pv-VQLkdSTmhCaIPTxY"

