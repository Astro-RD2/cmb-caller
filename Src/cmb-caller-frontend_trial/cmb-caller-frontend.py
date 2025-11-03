'''
websockets 14 板以上有相容性問題
pip uninstall websockets -y
pip install websockets==13.1
pip show websockets
'''

'''
2025/0x/xx  Roy Ching    支援 GCE.
2025/03/03  Roy Ching    傳送至 sever 之 call_num 由 string 改為 int.
2025/03/24  Roy Ching    支援 GCR & GCE.
2025/04/01  Roy Ching    支援 get.
2025/04/07  Roy Ching    支援密碼登錄.
2025/04/08  Roy Ching    加入密碼登錄驗證對上重試機制.
2025/04/09  Roy Ching    修正login後get不到目前的號碼問題.
2025/04/10  Roy Ching    修正登入後從0開始問題.
2025/04/14  Roy Ching    加入叫號資料更新通知 (update)功能.
2025/04/15  Roy Ching    修復斷線重連後叫號資料更新通知失效問題(add_connection) (2025/04/16 取消).
2025/04/16  Roy Ching    斷線重連需要衝新認證(auth).
2025/04/16  Roy Ching    加入 'get_num_info' 及 'info' 呼叫支援
2025/04/17  Roy Ching    修復斷線重連號碼歸零問題.
2025/04/17  Roy Ching    支援 get_num_info 新舊規格
2025/04/18  Roy Ching    handle_auth 加 auth_lock:
2025/04/22  Roy Ching    斷線時間 0~9 改 1~10
2025/04/25  Roy Ching    加入 LockWithNotification & TracedLock
2025/04/28  Roy Ching    修正 CMB Caller 登入錯誤問題
2025/05/02  Roy Ching    auth_lock 改為 ws_cmd_lock
2025/05/02  Roy Ching    增加 new_get_num 命令.
2025/05/02  Roy Ching    auth 命令 增加 "user_get_num" 登入, 增加 wait_time_avg、new_get_num、get_num_switch及user_get_num 命令.
2025/05/02  Roy Ching    get_num_switch 增加主動通知功能, user_get_num 增加 "user_id" 欄位, 增加 get_num_status 命令.
2025/05/06  Roy Ching    改為主動通知 user_get_num
2025/05/07  Roy Ching    "user_get_num",限定權限,user_get_num(Server 不主動通知)、get_num_switch(僅接收),且無 send、new_get_num  功能.
2025/05/14  Roy Ching    json send 資料去除 []
2025/05/14  Roy Ching    'update' 不傳送給發送端
2025/05/14  Roy Ching    修改 'user_get_num' 廣播資訊 -> 'new_get_num'
2025/06/05  Roy Ching    加入 login(auth) json 執行
2025/06/05  Roy Ching    加入 get_num_info json  執行
2025/06/05  Roy Ching    CMB Main 資料未 remove_matched 錯誤處理
2025/06/05  Roy Ching    加入 CMB Main 資料 及 登入類別 顯示
2025/06/12  Roy Ching    修復 user_get_num 未回覆 get_num_item_id 之問題.
2025/06/20  Roy Ching    handle_send_message retry 加入 delay.
2025/06/20  Roy Ching    傳入 Maim Server 的資料皆加入 Retry 3次 功能.
2025/06/24  Roy Ching    新加入之 ID 會查詢 CMB Main Server 取得最後的叫號號碼.
2025/06/24  Roy Ching    加入 'reset_caller' 叫號號碼的功能.
2025/07/02  Roy Ching    加入執行時踢除上一版本的功能.
2025/07/02  Roy Ching    對 WiFi 設定程式 傳送 Caller 斷線廣播.
2025/07/02  Roy Ching    加入 login 提供 hardware 參數.
2025/07/07  Roy Ching    加入執行時僅保留一個 Instance 的功能.
2025/07/07  Roy Ching    加入 12.取消取號 (Line使用者) "cancel_get_num".
2025/07/07  Roy Ching    加入 13.取消取號 (網頁使用者) "web_cancel_get_num".
2025/07/07  Roy Ching    加入 14.到號保留 (中央主動傳送) "reserve_number" 
2025/07/08  Roy Ching    修正 handle_auth(...) 之 invalid literal for int() with base 10: '' 之錯誤.
2025/07/09  Roy Ching    修正 add_connection(...) 之 invalid literal for int() with base 10: '' 之錯誤.
2025/07/09  Roy Ching    修正 web_cancel_get_num 加入廣播至全部店家功能.
2025/07/17  Roy Ching    加入 被GCR斷線重連時 Server 上資料與 Caller LED 顯示不同之問題處理.
2025/07/21  Roy Ching    只對 Caller 作用 被GCR斷線重連時 Server 上資料與 Caller LED 顯示不同之問題處理.
2025/07/21  Roy Ching    加強 執行時僅保留一個 Instance 的功能.
2025/07/21  Roy Ching    加入 15.移除號碼 "remove_number" (需廣播至全部店家)
2025/07/24  Roy Ching    JSON login 改為不等待方式.
2025/07/25  Roy Ching    修復 CSV login 失效問題.
2025/07/29  Roy Ching    CSV login 改為不等待方式.
2025/07/30  Roy Ching    部分 websocket.send 增加 try.
2025/07/30  Roy Ching    LockWithNotification 改名 NotifyingLock
2025/07/30  Roy Ching    ws_cmd_lock -> ws_device_lock 
2025/07/30  Roy Ching    取消 TracedLock 全部改用 NotifyingLock
2025/07/31  Roy Ching    取消 user_get_num 廣播對應至 new_get_num.
2025/08/01  Roy Ching    get_num_switch' new_get_num' user_get_num 皆發送給訪客.
2025/08/06  Roy Ching    cancel_get_num 發送給訪客.
2025/08/27  Roy Ching    respones_Threshold 調整 0.4Sec -> 0.8Sec
2025/08/27  Roy Ching    加入 16.參數設定. set_params.
2025/08/27  Roy Ching    加入 連線失敗 LINE 通知功能.
2025/08/28  Roy Ching    如無叫號資料或叫號值錯誤則設 0.
2025/09/09  Roy Ching    update_caller_info 如資料不正確就不設定 clients[ID]['caller_num']
2025/09/11  Roy Ching    修正斷線頻繁重蓮又斷線問題, 加 await asyncio.sleep(0.5) 及 不使用 self.connected
2025/09/11  Roy Ching    修正 login 錯誤會與 CMB Main Server 斷線之問題.
2025/09/16  Roy Ching    修正 歸零時因時間差導致資料回朔之問題.
2025/09/19  Roy Ching    get_num_info 不執行 update_caller_info.
2025/09/19  Roy Ching    加入 process_reset 回覆 OK.
2025/09/23  Roy Ching    修正 例行資料數值為 0 顯示空值之問題.
2025/09/25  Roy Ching    加入 GCP 斷線問題處理，增加錯誤碼(005).
2025/10/23  Roy Ching    取消 class WebSocketClient: connect 重連 await asyncio.sleep(0.5).
'''


import re
import nest_asyncio
import functools
import traceback
from google.auth import default
from logging.handlers import RotatingFileHandler
import logging
import websockets
import asyncio
import json
import requests
import os
import platform
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, Any, Deque
from contextlib import asynccontextmanager
from google.api_core.exceptions import NotFound
import psutil  # 用於獲取進程記憶體資訊
from collections import deque
from linebot import LineBotApi
from linebot.models import TextSendMessage

VER = "20251023"

print(".", flush=True)
print(".", flush=True)
print("============================ New Instance started!!! ============================", flush=True)
print(".", flush=True)
print(".", flush=True)

try:
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None
    print("警告：無法匯入 google.cloud.pubsub_v1，請確認是否已安裝相關套件。")
    print("如於 Windows 環境下執行，請忽略此訊息!")

nest_asyncio.apply()


# 讓所有 print 都即時輸出
print = functools.partial(print, flush=True)

# instance_uuid = str(uuid.uuid4())
timestamp = time.time()     # 必須有

# app = Flask(__name__)

# 設置 websockets.server 記錄器的日誌級別為 WARNING 或更高
# 這樣 INFO 級別的 'connection open' 和 'connection closed' 就不會顯示
logging.getLogger("websockets.server").setLevel(logging.WARNING)


# -------------------------------------------------------------
#           *** Caller & WEB (CSV & JSON) ***

# 定義 Caller CSV 需要處理的指令
CALLER_CSV_COMMANDS_TO_PROCESS = {
    'send', 'auth', 'get_num_info', 'info', 'get'}

# Caller 傳入 JSON file 需等待 Server 回覆時使用, login 另外先處理.
# 需 reply 之原因
# user_get_num:         回覆 & 群發 new_get_num 至其他店家
# get_num_status:       回覆不廣播
# get_num_info:         回覆 & 更新caller的號碼
# web_cancel_get_num:   (回覆店家及)廣播至全部店家及訪客
# remove_number:        (回覆店家及)廣播至全部店家及訪客
# 新增 '等待' 命令在此加入, 為何需等待?
client_wait_reply_actions_check = {
    "user_get_num", "get_num_status", "get_num_info", "web_cancel_get_num", "remove_number"}    # json


# -------------------------------------------------------------
#           *** listen CMB Main Server ***

# listen CMB Main Server 回覆 或 主動通知, 直接轉發 或 處理後續.
# 新增命令在此加入
servsr_replay_active_actions_check = {
    # "get_num_switch", "new_get_num", "reset_caller", "cancel_get_num", "reserve_number"}
    "get_num_switch", "new_get_num", "reset_caller", "cancel_get_num", "reserve_number", 'login', 'set_params', "set_time_period"}

# listen CMB Main Server (主動通知 處理完後) 回覆 OK 給 CMB Main Server.              #
servsr_active_actions_replay_ok_check = {
    # "new_get_num", "reset_caller", "cancel_get_num", "reserve_number"}
    "new_get_num", "reset_caller", "cancel_get_num", "reserve_number"}  # login 不需要


# 全局變數
if pubsub_v1 != None:
    publisher = pubsub_v1.PublisherClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    topic_path = publisher.topic_path(project_id, 'cross-instance-comms')
    revision = os.getenv('K_REVISION', 'local')
    match = re.search(r'-(\d{5})-', revision)
    revision_code = int(match.group(1)) if match else None
else:
    publisher = "Windows Local"
    project_id = "Windows Local"
    topic_path = "Windows Local"
    revision = "Windows Local"
    match = "Windows Local"
    revision_code = "Windows Local"

subscriber = None
is_subscribed = False
streaming_pull_future = None
ws_server = None
# ConnectionBlocker = True        # (Trial 才有效) 模擬斷線設
ConnectionBlocker = False    # (Trial 才有效) 模擬斷線設
start_timestamp = time.time()
run_mode = 'Local'
periodic_pass = False


# curl -X POST http://127.0.0.1:8081/trigger-subprogram		# OK
# curl -X GET http://127.0.0.1:8081/test                    # OK

# curl -X POST "https://cmb-caller-frontend-306511771181.asia-east1.run.app/trigger-subprogram"
# curl -X GET "https://cmb-caller-frontend-306511771181.asia-east1.run.app/test"


# def sys_exit():
#     logging.info("系統重新啟動!!!")
#     time.sleep(1)
#     sys.exit(1)  # 非 0 表示異常結束，Cloud Run 會重新啟動容器
#     # return

def sys_exit():
    reason = ''
    logging.info("系統重新啟動!!!")
    time.sleep(1)

    """優雅關閉並重啟"""
    logging.critical(f"開始優雅關閉程序: {reason}")

    try:
        # 清理資源
        # self.cleanup_resources()

        # 記錄重啟原因
        logging.critical(f"容器即將重啟: {reason}")

        # # 非 0 退出碼觸發 Cloud Run 重啟
        # logging.critical("容器即將重啟: sys.exit(1)")
        # sys.exit(1)

        # 強制退出
        logging.critical("容器即將重啟: os._exit(1)")
        os._exit(1)

    except Exception as e:
        logging.error(f"優雅關閉過程中發生錯誤: {e}")
        # 強制退出
        os._exit(1)


# # 新增一個簡單的 HTTP 端點
# @app.route('/trigger-subprogram', methods=['GET', 'POST'])
# def trigger_subprogram():
#     """觸發副程式的 HTTP 端點"""
#     try:
#         print("HTTP 端點 trigger_subprogram!", flush=True)
#         # 在背景執行緒中執行副程式，避免阻塞主程式
#         thread = threading.Thread(target=run_subprogram)
#         thread.daemon = True
#         thread.start()
#         return jsonify({"status": "success", "message": "副程式已開始執行"})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


# def run_subprogram():
#     """你的副程式邏輯"""
#     print("副程式開始執行...", flush=True)
#     # 這裡放入你的副程式程式碼
#     # 例如：處理特定任務、清理資料等
#     print("副程式執行完成", flush=True)

# # 簡單的測試端點


# @app.route('/test', methods=['GET', 'POST'])
# def test_endpoint():
#     print("HTTP 端點 test!", flush=True)
#     return jsonify({
#         "status": "ok",
#         "service": "cmb-caller-frontend",
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "revision": revision
#     })


class LineNotifier:
    global run_mode

    def __init__(self):
        # LINE BOT Token
        self.channel_access_token = "vcClHW6zeF2V/nBoWQtDR7XiSOl98/uqK0s615RbKXHkGeRS3l2TTAZVQr3DjIE+l3yzEHydaekwMRapABOGcvrX7BX7mJsV4XKKRdO/x2nPGKz4f9conu09LbPQQFylNn/VvZONdEwmNEvaiDxo2QdB04t89/1O/w1cDnyilFU="
        self.line_bot_api = LineBotApi(self.channel_access_token)

        # 事件設定檔
        self.settings = {
            "event_1": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"}
                ],
                "template": "{status}"
            },
            "event_2": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"},
                    {"id": "U95547b7b9b1226f08563825c7f8db533", "name": "Jando"},
                    {"id": "Ubfd6afe6fc674dd60bb7712e3a0681b5", "name": "Alvin"},
                    {"id": "U925476ebe228a22175cfcc499cec617e", "name": "Sam"},
                    {"id": "Ud9dfd12cfadcfa768c33c51a9c07b2d2", "name": "李大涵 "},
                    {"id": "U90ed94e344db6b2014cc1b3f29adbfe3", "name": "客服"}
                ],
                "template": "{status}"
            }
        }

    def send_event_message(self, event_key, status):
        event = self.settings.get(event_key)
        if not event:
            print(f"❌ 找不到事件設定：{event_key}")
            return

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = event["template"]
        recipients = event["recipients"]

        result = False
        for user in recipients:
            try:
                message_text = template.format(
                    status=status
                )
                self.line_bot_api.push_message(
                    user["id"], TextSendMessage(text=message_text))
                print(f"✅ 已發送給 {user['name']}")
                result = True
            except Exception as e:
                print(f"❌ 發送給 {user['name']} 失敗: {e}")
        return result


LineNotifier = LineNotifier()


class ConnectionMonitor:
    def __init__(self, window_size_seconds: int = 1800):  # 預設30分鐘
        self._lock = asyncio.Lock()

        # 連線狀態記錄
        # self.last_connect_time: Optional[float] = None
        self.last_connect_time = time.time()
        # self.last_disconnect_time: Optional[float] = None
        self.last_disconnect_time = time.time() - 1
        self.last_disconnect_reason: Optional[str] = None

        # 斷線頻率統計
        self.disconnect_timestamps: Deque[float] = deque(
            maxlen=1000)  # 設置最大長度防止記憶體泄漏
        self.window_size = window_size_seconds
        self.total_reconnects = 0

        # 錯誤記錄
        self.error_log: Deque[str] = deque(maxlen=50)  # 保留最近50條錯誤

        # 重啟標誌
        self._restart_required = False
        self._notify_required = False

        # 閾值設定
        if run_mode == 'Live':
            self.disconnect_threshold_notify = 3    # 2 -> 3
            self.disconnect_threshold_restart = 15   # 4 -> 10
        else:
            self.disconnect_threshold_notify = 10
            self.disconnect_threshold_restart = 20

        if run_mode == 'Local':
            self.disconnect_threshold_notify = 10        # 3, <6 一定會作動
            self.disconnect_threshold_restart = 20       # 6, <6 一定會作動

        self.notify = False

        self.notifier = LineNotifier

        self.last_recent_disconnects = 0

    async def record_connect(self):
        """記錄成功連線"""
        async with self._lock:
            logging.info(
                f"記錄成功連線: {self._format_time(self.last_connect_time)}")
            self.last_connect_time = time.time()
            disconnection_duration = self.last_connect_time - self.last_disconnect_time
            if self.notify and (disconnection_duration/60) >= 3:
                self.notify = False
                print(
                    f"---LINE--- 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")
                if run_mode == 'Trial':
                    send_result = self.notifier.send_event_message(
                        "event_1", status=f"        ====== 測試! ======\n叫叫我 Trial Caller Server 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")
                    # "event_2", status=f"        ====== 測試! ======\n叫叫我 Caller Server 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")
                elif run_mode == 'Local':
                    send_result = self.notifier.send_event_message(
                        "event_1", status=f"        ====== Local 測試! ======\n叫叫我 Local Caller Server 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")
                elif run_mode == 'Live':
                    send_result = self.notifier.send_event_message(
                        "event_2", status=f"叫叫我 Caller Server 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")
                    # "event_1", status=f"叫叫我 Caller Server 已重新連線!\n(斷線{int(disconnection_duration/60)}分鐘)")

    async def record_disconnect(self, reason: str):
        """記錄斷線事件"""
        async with self._lock:
            timestamp = time.time()
            self.last_disconnect_time = timestamp
            self.last_disconnect_reason = reason
            self.disconnect_timestamps.append(timestamp)
            self.total_reconnects += 1
            logging.info(
                f"記錄 CMB Main Server 斷線事件: {self._format_time(self.last_disconnect_time)}")

            # 記錄錯誤
            error_msg = f"{self._format_time(timestamp)} - {reason}"
            self.error_log.append(error_msg)

            current_count = self.get_recent_disconnect_count()
            logging.warning(
                f"記錄斷線: {reason}. 30分鐘內 CMB Main Server 斷線次數: {current_count}次")

    def get_recent_disconnect_count(self) -> int:
        """獲取最近30分鐘內的斷線次數"""
        now = time.time()
        cutoff = now - self.window_size
        return sum(1 for ts in self.disconnect_timestamps if ts >= cutoff)

    async def check_health(self):
        """檢查健康狀態並觸發相應操作"""
        # logging.info("check_health_0")
        async with self._lock:
            # logging.info("check_health_1")
            disconnection_status = (
                self.last_disconnect_time > self.last_connect_time)
            disconnection_duration = 0
            if disconnection_status:
                disconnection_duration = time.time() - self.last_disconnect_time
                print(f"\n已斷線 {disconnection_duration:.2f} 秒.", flush=True)  # 因 check_health 10 秒才被呼叫一次,所以只是概略的時間.
            else:
                # print(
                #     f"\n連線時間 {time.time() - self.last_connect_time} 秒.", flush=True)
                pass

            if not self.notify and disconnection_status and (disconnection_duration/60) >= 3:
                # self.notify = True
                print(f"---LINE--- 斷線{int((disconnection_duration/60))}分鐘")
                if run_mode == 'Trial':
                    send_result = self.notifier.send_event_message(
                        "event_1", status=f"        ====== 測試! ======\n叫叫我 Trial Caller Server 已斷線 {int((disconnection_duration/60))} 分鐘.!\n(與 CMB Main Server 連線)")
                    # "event_2", status=f"        ====== 測試! ======\n叫叫我 Caller Server 已斷線 {int((disconnection_duration/60))} 分鐘.!\n(與 CMB Main Server 連線)")
                elif run_mode == 'Local':
                    send_result = self.notifier.send_event_message(
                        "event_1", status=f"        ====== Local 測試! ======\n叫叫我 Local Caller Server 已斷線 {int((disconnection_duration/60))} 分鐘.!\n(與 CMB Main Server 連線)")
                elif run_mode == 'Live':
                    send_result = self.notifier.send_event_message(
                        "event_2", status=f"叫叫我 Caller Server 已斷線 {int((disconnection_duration/60))} 分鐘.!\n(與 CMB Main Server 連線)")
                    # "event_1", status=f"叫叫我 Caller Server 已斷線 {int((disconnection_duration/60))} 分鐘.!\n(與 CMB Main Server 連線)")

                self.notify = send_result

            # if self.notify and disconnection_duration <= 0:
            #     self.notify = False
            #     print("已重新連線{}分鐘")

            recent_disconnects = self.get_recent_disconnect_count()

            # 檢查是否需要通知
            if recent_disconnects >= self.disconnect_threshold_notify and recent_disconnects > self.last_recent_disconnects:
                self._notify_required = True
                self.last_recent_disconnects = recent_disconnects
                logging.warning(f"觸發通知閾值: {recent_disconnects}次斷線")

            # 檢查是否需要重啟
            # if recent_disconnects >= self.disconnect_threshold_restart:
            if recent_disconnects >= self.disconnect_threshold_restart and recent_disconnects > self.last_recent_disconnects:
                self._restart_required = True
                logging.critical(f"觸發重啟閾值: {recent_disconnects}次斷線")

            if (recent_disconnects + 1) < self.last_recent_disconnects:
                self.last_recent_disconnects = recent_disconnects

    async def generate_health_report(self) -> dict:
        """生成健康報告"""
        async with self._lock:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "timestamp": time.time(),
                "last_connect_time": self.last_connect_time,
                "last_disconnect_time": self.last_disconnect_time,
                "last_disconnect_reason": self.last_disconnect_reason,
                "recent_disconnect_count_30min": self.get_recent_disconnect_count(),
                "total_reconnects": self.total_reconnects,
                "recent_errors": list(self.error_log)[-10:],  # 最近10條錯誤
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "status": "HEALTHY" if self.get_recent_disconnect_count() == 0 else "DEGRADED"
            }

    def should_restart(self) -> bool:
        """檢查是否需要重啟"""
        return self._restart_required

    def should_notify(self) -> bool:
        """檢查是否需要通知"""
        return self._notify_required

    def reset_notify_flag(self):
        """重置通知標誌"""
        self._notify_required = False

    @staticmethod
    def _format_time(timestamp: Optional[float]) -> str:
        if timestamp is None:
            return "N/A"
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))


class LoginBuffer:
    def __init__(self):
        # uuid -> {"websocket": ..., "ws_type": ...}
        self._buffer: Dict[str, Dict[str, any]] = {}
        self._lock = asyncio.Lock()

    async def add(self, websocket, ws_type: str):
        uuid = hex(id(websocket))  # 使用 websocket 物件的記憶體地址作為唯一識別碼
        async with self._lock:
            self._buffer[uuid] = {
                "websocket": websocket,
                "ws_type": ws_type
            }
            # print(f"[LoginBuffer] 使用者加入: {uuid}, 類型: {ws_type}")

    async def get(self, uuid: str) -> Optional[Dict[str, any]]:
        async with self._lock:
            entry = self._buffer.get(uuid)
            if entry:
                return {
                    "websocket": entry["websocket"],
                    "ws_type": entry["ws_type"]
                }
            return None

    # async def get_type(self, uuid: str) -> Optional[str]:
    #     async with self._lock:
    #         entry = self._buffer.get(uuid)
    #         return entry["ws_type"] if entry else None

    async def get_all(self) -> Dict[str, Dict[str, any]]:
        """取得所有 WebSocket 連線資料（包含 websocket 與 ws_type）"""
        async with self._lock:
            return {
                uuid: {
                    "websocket": entry["websocket"],
                    "ws_type": entry["ws_type"]
                }
                for uuid, entry in self._buffer.items()
            }

    async def remove(self, uuid: str):
        async with self._lock:
            if uuid in self._buffer:
                # print(f"[LoginBuffer] 使用者移出: {uuid},  類型: {self._buffer[uuid]['ws_type']}")
                del self._buffer[uuid]

    # async def broadcast(self, message: str, ws_type: Optional[str] = None):
    #     """廣播訊息給所有使用者，或指定 ws_type 的使用者"""
    #     async with self._lock:
    #         for uuid, entry in self._buffer.items():
    #             if ws_type is None or entry["ws_type"] == ws_type:
    #                 try:
    #                     await entry["websocket"].send(message)
    #                 except Exception as e:
    #                     print(f"[LoginBuffer] 傳送失敗: {uuid}, 原因: {e}")


# 建立實例
login_buffer = LoginBuffer()


async def delayed_subscribe():
    """延遲訂閱 Pub/Sub 並處理訊息，包含完整錯誤處理和資源清理"""
    global subscriber, is_subscribed, streaming_pull_future, ws_server, topic_path, revision, revision_code, project_id
    print("#{revision} 延遲訂閱 Pub/Sub 並處理訊息...")
    # revision = os.getenv('K_REVISION', 'local')
    # match = re.search(r'-(\d{5})-', revision)
    # revision_code = int(match.group(1)) if match else None

    try:
        subscriber_wait = 0
        print(f"#{revision} [啟動] 等待 {subscriber_wait} 秒後開始訂閱...", flush=True)
        await asyncio.sleep(subscriber_wait)

        if subscriber is None:
            subscriber = pubsub_v1.SubscriberClient()
            print(f"#{revision} [訂閱] SubscriberClient 初始化完成", flush=True)
        # EX:  subscription_sub_name:version-sub-cmb-caller-frontend-00333-9nt-local
        subscription_sub_name = f"version-sub-{revision}-{os.getenv('CLOUD_RUN_EXECUTION', 'local')}"
        print(
            f"#{revision} [訂閱] subscription_sub_name:{subscription_sub_name}\n", flush=True)
        subscription_path = subscriber.subscription_path(
            project_id,
            subscription_sub_name
        )

        try:
            # subscriber = pubsub_v1.SubscriberClient()
            project_path = f"projects/{project_id}"

            # print("刪除舊訂閱_0")
            for subscription in subscriber.list_subscriptions(request={"project": project_path}):
                # print(f"刪除舊訂閱,subscription：{subscription}")
                # match = re.search(r'-sub-(\d{5})-', subscription.name)
                match = re.search(r'-(\d{5})-', subscription.name)
                if match:
                    # print(f"#{revision} 刪除舊訂閱,match:{match}")
                    sub_revision_code = int(match.group(1))
                    # print(f"#{revision} 刪除舊訂閱,sub_revision_code,revision_code:{sub_revision_code},{revision_code}")
                    if sub_revision_code < (revision_code - 1):     # !!!@@@
                        try:
                            subscriber.delete_subscription(
                                subscription=subscription.name)
                            print(f"✅ #{revision} 已刪除舊訂閱：{subscription.name}")
                        except NotFound:
                            print(f"⚠️ #{revision} 訂閱不存在：{subscription.name}")
                        except Exception as e:
                            print(
                                f"❌ #{revision} 刪除失敗：{subscription.name}, 錯誤：{e}")

            # 重建訂閱
            subscriber.create_subscription(
                name=subscription_path,
                topic=topic_path,
                ack_deadline_seconds=30
            )
            print(
                f"#{revision} [訂閱] 訂閱建立成功: {subscription_path},{topic_path}", flush=True)
        except Exception as e:
            if "already exists" in str(e):
                print(
                    f"#{revision} [訂閱] 使用現有訂閱: {subscription_path},{topic_path}", flush=True)
            else:
                print(
                    f"#{revision} [訂閱] 訂閱建立成功: {subscription_path},{topic_path}", flush=True)
                raise

        shutdown_event = asyncio.Event()
        sender_revision = None
        sender_timestamp = None
        sender_revision_code = None
        stop_service_flag = False
        data = None

        def callback(message):
            nonlocal sender_revision, sender_timestamp, sender_revision_code, stop_service_flag, data

            try:
                try:
                    data = json.loads(message.data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    logging.error(f"#{revision} [錯誤] JSON 解析失敗: {e}")
                    message.nack()
                    return
                except UnicodeDecodeError as e:
                    logging.error(f"#{revision} [錯誤] 訊息解碼失敗: {e}")
                    message.nack()
                    return
                # TRial:
                # gcloud pubsub topics publish projects/callme-op-419108/topics/cross-instance-comms --message="{\"content\": \"SYS_REQUEST\", \"message\": \"sys_restart\"}"
                # Live:
                # gcloud pubsub topics publish projects/callme-398802/topics/cross-instance-comms --message="{\"content\": \"SYS_REQUEST\", \"message\": \"sys_restart\"}"
                if data.get('content') == 'SYS_REQUEST' and data.get('message') == 'sys_restart':     #
                    message.ack()
                    logging.info(
                        f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')}, {data.get('message')}")
                    logging.info("系統結束容器以觸發重啟!")
                    sys_exit()
                    return

                if data.get('content') == 'STOP_SERVER':
                    try:
                        try:
                            parts = data.get('sender', 'unknown').split('/')
                            sender_revision = parts[0]
                            sender_timestamp = float(parts[1])
                            match = re.search(r'-(\d{5})-', sender_revision)
                            sender_revision_code = int(
                                match.group(1)) if match else None
                        except (IndexError, ValueError, AttributeError) as e:
                            logging.error(
                                f"#{revision} [錯誤] 解析 sender 資訊失敗: {e}")
                            message.nack()
                            return

                        if stop_service_flag:
                            logging.info(
                                f"#{revision} 系統已開始執行 '停止服務程序' 忽略以下請求!!! ")
                            logging.info(
                                f"#{revision} 忽略以下請求: [訊息] 來自 {data.get('sender')}: {data.get('content')}, {data.get('message')}")
                            message.ack()
                            return
                        else:
                            logging.info(
                                f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')}, {data.get('message')}")

                        # logging.info(
                        #     f"#{revision} revision_code,timestamp:{revision_code},{timestamp} , sender_revision_code,sender_timestamp:{sender_revision_code},{sender_timestamp}")

                        try:
                            if revision_code > sender_revision_code:
                                message.ack()
                                logging.info(
                                    f"#{revision} [過濾] 忽略較舊版本之停止服務請求：執行程式版本 {revision_code} > 訊號來源版本 {sender_revision_code}")
                                return

                            if revision_code == sender_revision_code and timestamp >= sender_timestamp:
                                message.ack()
                                if timestamp == sender_timestamp:
                                    logging.info(
                                        f"#{revision} [過濾] 忽略自己提出之停止服務請求：版本相同 {revision_code}，且執行程式時間戳 {timestamp} == 來源時間戳 {sender_timestamp}")
                                else:
                                    logging.info(
                                        f"#{revision} [過濾] 忽略較舊 Instance 之停止服務請求：版本相同 {revision_code}，但執行程式時間戳 {timestamp}  > 來源時間戳 {sender_timestamp}")
                                return
                        except TypeError as e:
                            logging.error(f"#{revision} [錯誤] 比較版本或時間戳失敗: {e}")
                            message.nack()
                            return

                        if revision_code < sender_revision_code:
                            logging.info(
                                f"#{revision} [過濾] 較新版本之停止服務請求：執行程式版本 {revision_code} < 訊號來源版本 {sender_revision_code}")
                        if revision_code == sender_revision_code and timestamp < sender_timestamp:
                            logging.info(
                                f"#{revision} [過濾] 較新 Instance 執行程式時間戳之停止服務請求：版本相同 {revision_code}，但執行程式時間戳 {timestamp} < 來源時間戳 {sender_timestamp}")
                        stop_service_flag = True
                        logging.info(
                            f"#{revision} [訊息] 較新版本/執行程式時間戳 執行停止服務請求 來自 {data.get('sender')}: {data.get('content')}, {data.get('message')}")
                        shutdown_event.set()
                        message.ack()
                        return

                    except Exception as e:
                        logging.error(
                            f"#{revision} [錯誤] 處理 STOP_SERVER 訊息失敗: {e}")
                        message.nack()
                        return

                # print(f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')}", flush=True)
                print(
                    f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')},{data}", flush=True)
                message.ack()
                return

            except Exception as e:
                logging.error(f"#{revision} [錯誤] 處理訊息時發生未預期錯誤: {e}")
                message.nack()
                return

        logging.info(f"#{revision} [訂閱] 開始監聽訊息...")
        streaming_pull_future = subscriber.subscribe(
            subscription_path,
            callback=callback,
            await_callbacks_on_shutdown=True
        )
        is_subscribed = True

        await shutdown_event.wait()
        logging.info(
            f"#{revision},{timestamp} ********** [訂閱] 收到停止訊號，開始清理..., 訊號來源版本 {sender_revision_code}，時間戳 {sender_timestamp} ********** ")
        # logging.info(f"#{revision} [訂閱] 收到停止訊號，開始清理...")

    except Exception as e:
        logging.info(f"#{revision} [錯誤] 訂閱流程異常: {type(e).__name__}: {e}")
        logging.exception(e)

    finally:
        print(f"#{revision} 安全釋放資源")

        if streaming_pull_future and not streaming_pull_future.done():
            logging.info(f"#{revision} [清理] 取消訂閱任務")
            streaming_pull_future.cancel()

        if subscriber is not None:
            logging.info(f"#{revision} [清理] 關閉 SubscriberClient")
            try:
                # await subscriber.close()    #
                subscriber.close()    # !!!@@@
            except Exception as e:
                logging.info(f"#{revision} [清理] 關閉 SubscriberClient 錯誤: {e}")
            subscriber = None

        if ws_server is not None:       # 連至 Caller
            logging.info(f"#{revision} [清理] 停止 WebSocket Server & Clinnt 服務")
            try:
                await ws_server.stop()
                # print("0_關閉 CMB Main Server WebSocket 連接!!!")
                await ws_server.ws_client.close()  # "關閉 CMB Main Server WebSocket 連接!!!"
            except Exception as e:
                logging.info(f"#{revision} [清理] 停止 WebSocket 服務錯誤: {e}")
            ws_server = None

        # print(f'#{revision},起始時間:{datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")}, 訂閱 & Websocket 服務已完全停止')
        logging.info(
            f"#{revision},{timestamp}, 訂閱 & Websocket 服務已完全停止!!!, 訊號來源版本 {sender_revision_code},時間戳 {sender_timestamp},訊息 {data.get('message')} ")


def broadcast_message(content, pmessage):
    """廣播訊息到所有實例"""
    try:
        # EX:
        # sender: 'cmb-caller-frontend-00333-9nt/1752724232.618618/local'
        # timestamp: 1752724263.9171188
        # ID:15657991195878896
        messages = {
            "content": content,
            "message": pmessage,
            "sender": f"{os.getenv('K_REVISION', 'local')}/{timestamp}/{os.getenv('CLOUD_RUN_EXECUTION', 'local')}",
            "timestamp": timestamp
        }

        future = publisher.publish(
            topic_path,
            json.dumps(messages).encode('utf-8')
        )
        logging.info(
            f"#{os.getenv('K_REVISION', 'local')} [廣播] 已發送訊息:{messages},ID:{future.result()}")
        return True, None  # Success, no error
    except Exception as e:
        logging.info(
            f"#{os.getenv('K_REVISION', 'local')} 廣播訊息時發生錯誤: {str(e)}")
        return False, str(e)  # Failure, with error message


# @app.get("/health")
# async def health_check():
#     """健康檢查端點"""
#     return {"status": "ok", "websocket": "running" if ws_server else "stopped"}

# @app.post("/broadcast")
# async def handle_broadcast(request: Request):
#     """HTTP 接口觸發廣播"""
#     data = await request.json()
#     content = data.get('message', '')
#     broadcast_message(content)
#     return {"status": "success", "message": "已廣播"}

# @app.post("/internal-message")
# async def handle_internal_message(request: Request):
#     """接收其他實例的直接訊息"""
#     if not is_subscribed:
#         print("[隊列] 訂閱未就緒，訊息暫存")
#         message_queue.append(await request.body())
#         return {"status": "queued"}
#     return {"status": "ignored"}


# @app.route('/', methods=['GET', 'POST'])
# def my_help():
#     routes = """
#     ('/help', methods=['GET', 'POST'])
#     ('/', methods=['GET', 'POST'])
#     ('/complete_shop_list', methods=['GET', 'POST'])    # 重建 shop_list
#     ('/garbage_collection', methods=['GET', 'POST'])
#     ('/generate_shop_list', methods=['GET', 'POST'])    # 重建 shop_list
#     ('/hello', methods=['GET', 'POST'])
#     ('/info', methods=['GET', 'POST'])
#     ('/last_updated_time', methods=['GET', 'POST'])
#     ('/no_sleep', methods=['GET', 'POST'])
#     ('/restart', methods=['GET', 'POST'])
#     ('/stay_awake', methods=['GET', 'POST'])
#     ('/system_info', methods=['GET', 'POST'])
#     ('/update_json_file', methods=['GET', 'POST'])      # 強制更新 shop_list
#     ('/update_shop_list', methods=['GET', 'POST'])      # 每分鐘檢查 eMail
#     """
#     return "<pre>" + routes.replace('\n', '<br>') + "</pre>"


# class TaipeiFormatter(logging.Formatter):
#     def formatTime(self, record, datefmt=None):
#         dt = datetime.fromtimestamp(record.created, ZoneInfo("Asia/Taipei"))
#         if datefmt:
#             return dt.strftime(datefmt)
#         else:
#             return dt.isoformat()

# # 設定 logging 使用台北時間
# # print('設定 logging 使用台北時間')
# formatter = TaipeiFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
# handler = logging.StreamHandler()
# handler.setFormatter(formatter)
# logging.basicConfig(level=logging.INFO, handlers=[handler])


# def local_datetime():
#     return f"{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}"


# @app.route('/reboot', methods=['GET', 'POST'])
# def my_exit():
#     # global sys_reboot
#     # global mainpi_main_crawler
#     try:
#         # 啟動後臺執行緒
#         threadE = threading.Thread(target=exit_th)
#         threadE.start()
#         logging.info(f"Exit event return {local_datetime()}")
#         print(f"\nExit event return {local_datetime()}", flush=True)
#         return f"{local_datetime()} Exit!"
#     except Exception as e:
#         logging.error(f"Error exit: {e}")
#         print(f"Error exit: {e}", flush=True)
#         return f"Error exit: {e}", 500  # 返回 HTTP 500 錯誤


# def exit_th():
#     logging.warning(f'{local_datetime()} 結束程序(程式重新啟動)!!!')
#     time.sleep(1)
#     # stop_all_threads(60)   # 60 sec
#     time.sleep(5)
#     os._exit(0)


class NotifyingLock:
    # def __init__(self):
    def __init__(self, name="unnamed_lock"):
        self._lock = asyncio.Lock()
        self.name = name
        self._waiting_messages: Dict[int, Dict[str, Any]] = {}
        self._lock_stats = {
            'total_acquires': 0,
            'total_wait_time': 0.0,
            'max_wait_time': 0.0,
            'immediate_acquires': 0
        }
        self._last_acquired_time = None
        print(f'🔐 Init {self.name}')

    @asynccontextmanager
    async def acquire(self, context: Optional[str] = None):
        """帶有等待通知的鎖定上下文管理器"""
        start_wait = time.monotonic()
        acquired = False
        task_id = id(asyncio.current_task())
        debug_info = {
            'context': context,
            'start_time': start_wait,
            'wait_time': 0.0,
            'status': 'init'
        }
        # print(f"🔐 [嘗試獲取鎖定] {context or '無上下文'} ", flush=True)
        try:
            # 嘗試非阻塞獲取鎖
            if not self._lock.locked():
                await self._lock.acquire()
                acquired = True
                self._lock_stats['immediate_acquires'] += 1
                self._lock_stats['total_acquires'] += 1
                self._last_acquired_time = time.monotonic()
                debug_info['status'] = 'immediate_acquire'
                # print(f"🔓 [立即獲取鎖定] {context or '無上下文'} ", flush=True)
                yield
                return

            # 記錄等待開始
            if context:
                self._waiting_messages[task_id] = debug_info
                debug_info['status'] = 'waiting'
                print(
                    f"⌛ [等待開始] {context} (當前等待任務數: {len(self._waiting_messages)})", flush=True)

            # 等待鎖定並記錄時間
            start_time = time.monotonic()
            last_print_time = start_time
            print_interval = 1.0  # 狀態更新間隔

            while not acquired:
                try:
                    await asyncio.wait_for(
                        self._lock.acquire(),
                        timeout=0.5  # 合理的檢查間隔
                    )
                    acquired = True
                    debug_info['status'] = 'acquired'
                    current_time = time.monotonic()
                    wait_time = current_time - start_time
                    debug_info['wait_time'] = wait_time

                    # 更新統計數據
                    self._lock_stats['total_acquires'] += 1
                    self._lock_stats['total_wait_time'] += wait_time
                    if wait_time > self._lock_stats['max_wait_time']:
                        self._lock_stats['max_wait_time'] = wait_time
                    self._last_acquired_time = current_time

                    # print(f"🔓 [獲取鎖定成功] {context or '無上下文'} 等待時間: {wait_time:.2f}秒", flush=True)
                except asyncio.TimeoutError:
                    current_time = time.monotonic()
                    wait_time = current_time - start_time
                    debug_info['wait_time'] = wait_time

                    # ⏳➡️⌛
                    # 定期打印等待狀態
                    if current_time - last_print_time >= print_interval:
                        last_print_time = current_time
                        waiting_tasks = len(self._waiting_messages)
                        print(
                            f"\n⏳ [等待中] {context or '無上下文'} "
                            f"已等待 {wait_time:.1f}秒 "
                            f"(總等待任務: {waiting_tasks})",
                            flush=True
                        )

            yield

        except Exception as e:
            debug_info['status'] = f'error: {str(e)}'
            raise
        finally:
            if acquired:
                self._safe_release(context)
                if task_id in self._waiting_messages:
                    del self._waiting_messages[task_id]

    def _safe_release(self, context: Optional[str] = None):
        """內部安全的釋放方法（共用邏輯）"""
        if self._lock.locked():
            self._lock.release()
            hold_time = time.monotonic() - self._last_acquired_time if self._last_acquired_time else 0
            # print(f"🔓 [釋放鎖定] {context or '手動操作'} (持有時間: {hold_time:.2f}秒)", flush=True)
            delay_check = 0.7
            if hold_time >= delay_check:
                print(
                    f"\n🔓 [釋放鎖定] {context or '手動操作'} (持有時間(>={delay_check}): {hold_time:.1f}秒)", flush=True)
            return True
        print(f"⚠️ 釋放失敗: {context or '手動操作'} 鎖定未被持有", flush=True)
        return False

    # 獨立的 release() 方法
    def release(self):
        """手動釋放鎖（安全方法）"""
        self._safe_release("手動釋放")

    def get_waiting_tasks(self) -> Dict[int, Dict[str, Any]]:
        """獲取當前等待中的任務詳細資訊"""
        return {
            task_id: {
                **info,
                'current_wait_time': time.monotonic() - info['start_time']
            }
            for task_id, info in self._waiting_messages.items()
        }

    def get_lock_stats(self) -> Dict[str, Any]:
        """獲取鎖的統計資訊"""
        stats = self._lock_stats.copy()
        if stats['total_acquires'] > 0:
            stats['avg_wait_time'] = stats['total_wait_time'] / \
                (stats['total_acquires'] - stats['immediate_acquires'])
        else:
            stats['avg_wait_time'] = 0.0
        return stats

    def get_lock_status(self) -> str:
        """獲取當前鎖的狀態摘要"""
        if self._lock.locked():
            holder_wait = time.monotonic() - self._last_acquired_time if self._last_acquired_time else 0
            return (
                f"🔒 鎖定中 (持有時間: {holder_wait:.1f}秒) | "
                f"等待任務: {len(self._waiting_messages)} | "
                f"最近統計: {self.get_lock_stats()}"
            )
        return "🔓 鎖定可用 (無持有者)"


# class TracedLock:
#     """追蹤等待時間的鎖"""

#     def __init__(self, name="unnamed_lock"):
#         self._lock = asyncio.Lock()
#         self.name = name

#     async def __aenter__(self):
#         task = asyncio.current_task()
#         task_id = id(task)
#         start_wait = time.time()

#         # 立即檢查鎖狀態
#         if self._lock.locked():
#             wait_start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
#             print(
#                 f"等待 {self.name} 鎖... [開始時間: {wait_start_time}]", end='', flush=True)

#             # 實際獲取鎖
#             await self._lock.acquire()

#             # 計算等待時間並顯示
#             wait_duration = time.time() - start_wait
#             wait_end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
#             print(
#                 f"取得 {self.name} 鎖，等待了 {wait_duration:.2f} 秒 [結束時間: {wait_end_time}]", end='', flush=True)
#         else:
#             # 沒有等待，直接獲取鎖
#             await self._lock.acquire()

#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         self._lock.release()


class PreciseTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            if "%F" in datefmt:  # 自訂 %F 表示秒數帶2位小數
                s = datetime.fromtimestamp(record.created).strftime("%S.%f")[
                    :8]  # 取 .xx
                return ct.strftime(datefmt).replace("%F", s)
            return ct.strftime(datefmt)
        else:
            t = ct.strftime("%H:%M:%S")
            s = datetime.fromtimestamp(record.created).strftime("%S.%f")[:8]
            return t[:-2] + s  # 替換最後兩位秒數


class TwoDecimalSecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = self.formatter_time(ct, datefmt)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            s = "%s,%03d" % (t, record.msecs)
        # 自訂格式到兩位小數
        return time.strftime("%H:%M:%S", ct) + ".%02d" % (record.msecs // 10)


class Logger:
    @staticmethod
    def log(message):
        """顯示帶時間戳的狀態訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{timestamp} {message}", flush=True)

    # def log(message):
    #     """顯示台北時間的狀態訊息"""
    #     taipei_tz = pytz.timezone('Asia/Taipei')
    #     timestamp = datetime.now(taipei_tz).strftime("%H:%M:%S.%f")[:-3]
    #     print(f"{timestamp} {message}", flush=True)


def setup_logger(log_to_console=True, log_to_file=True, log_level=logging.DEBUG, max_bytes=5*1000*1024, backup_count=1):
    # Get the current script file name without extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_file = f"{script_name}.log"

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create handlers based on user preference
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    if log_to_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    # Create a formatter and set it for all handlers

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Formatter with only time (no date)
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     datefmt='%H:%M:%S'
    # )
    # formatter = PreciseTimeFormatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     datefmt='%H:%M:%F'  # 用 %F 表示要顯示小數秒
    # )

    # formatter = TwoDecimalSecondFormatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )

    for handler in logger.handlers:
        handler.setFormatter(formatter)


new_add = False


class ClientManager:        # 紀錄管理 caller 連線
    global ws_server, new_add

    def __init__(self):
        self.clients = {}
        self.CLM_lock = NotifyingLock("ClM_lock")

    async def remove_client(self, caller_id):
        async with self.CLM_lock.acquire(f"ClM_lock remove_client: {caller_id}"):
            if caller_id in self.clients:
                del self.clients[caller_id]

    async def add_connection(self, caller_id, websocket, ws_type):
        # global new_add
        """添加一個新的WebSocket連接到指定caller_id"""
        # print("add_connection 0")
        try:
            # 嘗試取得所有客戶端資訊
            caller_num = 0  # 預設值
            try:
                clients = await self.get_all_clients()
                # 取得 caller_id 的 caller_num，如果不存在則預設 0，並確保是 int
                # existing_num = clients.get(caller_id, {}).get('caller_num', 0)
                existing_num = clients.get(caller_id, {}).get('caller_num', -1)
                caller_num = int(existing_num)  # 確保是 int
            except Exception as e:
                logging.error(
                    f"0_轉換客戶端 {caller_id} existing_num={existing_num} 為整數時發生錯誤: {e}")
                caller_num = 0  # 預設值

            new_add = False
            # print("add_connection 1")
            try:
                async with self.CLM_lock.acquire(f"ClM_lock add_connection: {caller_id},{ws_type}"):
                    # print("add_connection 2")
                    try:
                        if caller_id not in self.clients:   # 加入一新的 caller_id
                            new_add = True
                            print('加入一新的 caller_id:{caller_id}')
                            self.clients[caller_id] = {
                                'connections': {},    # 使用 dict 儲存連接
                                'caller_num': caller_num,   #
                                'caller_name': '',
                                'connect_time': datetime.now(),
                                'disconnect_time': None
                            }

                        # 更新連接資訊
                        # self.clients[caller_id]['connections'][websocket] = ws_type
                        ws_last_modified = time.time()
                        self.clients[caller_id]['connections'][websocket] = {
                            'ws_type': ws_type,
                            # 'ws_last_modified': datetime.now(),
                            # 'ws_connect_time': datetime.now()
                            'ws_last_modified': ws_last_modified,
                            'ws_connect_time': ws_last_modified,
                            'uuid': hex(id(websocket))
                        }

                        self.clients[caller_id]['disconnect_time'] = None
                    except Exception as e:
                        logging.error(f"更新客戶端資料時發生錯誤: {e}")
                        raise  # 重新拋出異常

            except Exception as e:
                logging.error(f"獲取鎖時發生錯誤: {e}")
                return False  # 添加連接失敗
            # print("add_connection 3")
            # if new_add:         # 如果是新連線，先取得之前叫號資訊!
            #     # await asyncio.sleep(500)    # !!!@@@
            #     print("add_connection 4")
            #     try:
            #         print('add_connection: get_num_info frontend', flush=True)
            #         data = {             # 設定叫號機
            #             'action': "get_num_info",   # 取號資訊
            #             "vendor_id": "tawe",
            #             "caller_id": caller_id,
            #             "user_id": "_frontend",
            #             "uuid": hex(id(websocket))
            #         }
            #         try:
            #             print("add_connection 5")
            #             # await ws_server.process_message(json.dumps(data), websocket, is_new_connection=False)
            #             await ws_server.process_message(json.dumps(data), websocket, True)
            #         except Exception as e:
            #             logging.error(f"處理新連接訊息時發生錯誤: {e}")
            #     except Exception as e:
            #         logging.error(f"準備新連接資料時發生錯誤: {e}")

            # print("add_connection 6")
            return True  # 添加連接成功

        except Exception as e:
            logging.error(f"添加連接時發生未預期錯誤: {e}")
            return False  # 添加連接失敗

    async def remove_connection(self, caller_id, websocket):
        """從指定caller_id移除一個WebSocket連接"""
        async with self.CLM_lock.acquire(f"ClM_lock remove_connection: {caller_id}"):
            if caller_id in self.clients:
                if caller_id in self.clients and websocket in self.clients[caller_id]['connections']:
                    del self.clients[caller_id]['connections'][websocket]
                    # print(f'0_discard({websocket}):{caller_id}', end='\n', flush=True)    # 與 1_discard & 2_discard 重複
                else:
                    logging.warning(
                        f"0_discard WebSocket not found for caller_id {caller_id}")

                # 如果沒有連接了，記錄斷開時間
                if not self.clients[caller_id]['connections']:
                    # print(f'記錄斷開時間:{caller_id}', end='\n', flush=True)
                    self.clients[caller_id]['disconnect_time'] = datetime.now()

    async def update_caller_info(self, caller_id, caller_num=None, caller_name=None):
        """更新 caller 的號碼與名稱（若提供），僅當 caller_num 為數字時才儲存"""
        lock_key = f"ClM_lock update_caller_info: {caller_id},{caller_num}"
        async with self.CLM_lock.acquire(lock_key):
            try:
                if caller_id not in self.clients:
                    print(
                        f"[update_caller_info] caller_id {caller_id} 不存在於 clients", flush=True)
                    return False

                if caller_num is not None:
                    if isinstance(caller_num, int) or (isinstance(caller_num, str) and caller_num.isdigit()):
                        self.clients[caller_id]['caller_num'] = int(caller_num)
                        # print(f"[update_caller_info] 設定 clients[{caller_id}]['caller_num'] = {caller_num}")
                        # print(f"[update_caller_info]設定{caller_id}='{caller_num}' ", end='', flush=True)
                        print(
                            f"[update_caller_info]設定{caller_id}='{self.clients[caller_id]['caller_num']}' ", end='', flush=True)
                    else:
                        print(
                            f"[update_caller_info]設定{caller_id} 忽略無效 caller_num: '{caller_num}'（非數字）", flush=True)
                        pass

                # if caller_name is not None:
                #     self.clients[caller_id]['caller_name'] = caller_name
                #     print(f"[update_caller_info] 設定 clients[{caller_id}]['caller_name'] = {caller_name}")

                return True

            except Exception as e:
                print(f"[update_caller_info] 發生錯誤: {type(e).__name__} -> {e}")
                return False

    # ws_type_enable 1:CMB Caller, 2:SOFT CMB Caller, 4:user_get_num, 8:Setup WiFi
    async def notify_clients(self, caller_id, message, ws_type_enable, ws_bypass=None):
        """通知指定caller_id的所有連接"""
        # print(f'notify_clients:{caller_id},{message},{ws_type_enable},{ws_bypass} ', end='', flush=True)
        # print(f'notify_clients:{caller_id},{message},{ws_type_enable}... ', end='', flush=True)
        async with self.CLM_lock.acquire(f"ClM_lock notify_clients: {caller_id}"):
            # print('na ', end='', flush=True)
            if caller_id in self.clients:   # 如未連線則不廣播
                # print('nb ', end='', flush=True)
                disconnected = set()
                # print(f'clients:{self.clients}')

                notify_count = 0
                # for websocket, ws_type in self.clients[caller_id]['connections'].items():
                for websocket, info in self.clients[caller_id]['connections'].items():
                    ws_type = info['ws_type']
                    # ws_last_modified = info['ws_last_modified']
                    # ws_connect_time = info['ws_connect_time']

                    # print('nc ', end='', flush=True)
                    try:
                        if websocket.open:
                            if ws_type & ws_type_enable:
                                if websocket != ws_bypass:
                                    # print('nd ', end='', flush=True)
                                    # EX: v0005,696,update
                                    # logging.info(f"通知客戶端:{message}")
                                    # 至 caller
                                    await websocket.send(message)
                                    notify_count += 1
                                    # print(f'主動通知:{ws_type},{ws_type_enable}', flush=True)
                                else:
                                    # print(f'BYPASS 主動通知:{ws_bypass},{ws_type},{ws_type_enable}', flush=True)
                                    # print(f'BYPASS 主動通知:{ws_type}', flush=True)
                                    pass
                            else:
                                # print(f'不主動通知:{ws_type},{ws_type_enable}', flush=True)
                                pass
                        else:
                            # print('ne ', end='', flush=True)
                            # logging.info(f"disconnected.add({websocket}):{caller_id}")
                            disconnected.add((caller_id, websocket))
                            pass
                    except Exception as e:
                        print('nf ', end='', flush=True)
                        logging.error(
                            f"通知 Client {caller_id},{ws_type} 失敗: {e}")
                        traceback.print_exc()
                        disconnected.add((caller_id, websocket))
                # print(f'notify_clients 傳送次數:{notify_count}')
                if (notify_count == 0):
                    pass
                return notify_count

                # print(f'disconnected:{disconnected}', end='\n', flush=True)
                # 移除已斷開的連接
                # # 2025/05/13 先不做，由每分鐘例行發送一起處理!   !!!@@@
                # for caller_id, ws in disconnected:
                #     # print(f'移除已斷開的連接:{caller_id} ', end='', flush=True)
                #     # print(f'disconnected:{disconnected}', end='\n', flush=True)
                #     if caller_id in self.clients and ws in self.clients[caller_id]['connections']:
                #         del self.clients[caller_id]['connections'][ws]
                #         print(f'\n2x_discard:{ws}:{caller_id}',
                #               end='\n', flush=True)
                #         # print(f'2x_discard:{ws}:{caller_id}    *** BYPASS ***', end='\n', flush=True)
                #     else:
                #         logging.warning(
                #             f"2x_discard:{ws} not found for caller_id {caller_id}")

    async def get_caller_num(self, caller_id):
        """獲取指定caller_id的當前號碼"""
        async with self.CLM_lock.acquire(f"ClM_lock get_caller_num: {caller_id}"):
            # print(
            #     f" get_caller_num:{caller_id},{self.clients[caller_id]['caller_num']} ", end='', flush=True)
            if caller_id in self.clients:
                return self.clients[caller_id]['caller_num']
            return 0

    async def cleanup(self):
        """清理長時間無連接的caller記錄"""
        async with self.CLM_lock.acquire("ClM_lock cleanup"):
            now = datetime.now()
            to_remove = []
            for caller_id, info in self.clients.items():
                if info['disconnect_time'] and (now - info['disconnect_time']).total_seconds() > 3600:
                    to_remove.append(caller_id)
            for caller_id in to_remove:
                del self.clients[caller_id]
                print(f'已移除斷線60分鐘之ID:{caller_id}')

    async def get_all_clients(self):
        """獲取所有客戶端資訊"""
        async with self.CLM_lock.acquire("ClM_lock get_all_clients"):
            return {k: v for k, v in sorted(self.clients.items())}


client_manager = ClientManager()

# 從 CMB Main Server 傳入的資料


class JSONMemoryManager:
    def __init__(self, max_capacity=100):
        self.data = {"records": []}
        self.max_capacity = max_capacity

    def add_data(self, new_record):
        try:
            new_record_1 = json.loads(new_record)
            self.data["records"].append(new_record_1)
            # print(f"0_add_data count_data:{manager.count_data()}, {new_record_1}")
            # 如果超過最大容量，移除最舊的資料
            if len(self.data["records"]) > self.max_capacity:
                to_remove = self.data["records"][0]
                print(f"即將移除最舊一筆回覆暫存資料: {to_remove}")
                self.data["records"].pop(0)
                print(
                    f"1_add_data count_data:{manager.count_data()}, {new_record_1}")
        except json.JSONDecodeError:
            print("加入資料失敗：不是合法的 JSON 格式")

    def count_data(self):
        return len(self.data["records"])

    def search_data(self, condition):
        """根據條件搜索資料"""
        matched = [record for record in self.data["records"]
                   if condition(record)]  # [2][3]
        # print(f"search_data count_data:{manager.count_data()}, {condition}")
        return matched

    def remove_matched(self, matched):
        """自動整理剩餘資料"""
        self.data["records"] = [
            record for record in self.data["records"] if record not in matched]  # [4]
        # print(f"remove_matched count_data:{manager.count_data()}, {matched}")

    def show_all_data(self):
        """顯示所有資料"""
        print(f"目前共有 {self.count_data()} 筆資料：")
        for i, record in enumerate(self.data["records"], start=1):
            print(f"{i}: {record}")


# manager = JSONMemoryManager()
manager = JSONMemoryManager(max_capacity=5)    # 限制最多 xx 筆資料
server_connection_monitor = ConnectionMonitor()

# 連結 CMB Main Server


class WebSocketClient:
    global ConnectionBlocker, ws_server, run_mode, server_connection_monitor

    def __init__(self, ws_url):     # CMB Main Server
        """初始化 WebSocket Client"""
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws_server = None  # CMB Main Server
        self.retry_delay = 3
        self.max_retry_delay = 30   # 20 -> 30
        self.ws_server_server_lock = NotifyingLock("ws_server_lock")
        # 建立一個統一的訊息佇列
        self.message_queue = asyncio.Queue()
        # self.connected = True
        self.websocket_listener_task = None

        self.server_connection_monitor = server_connection_monitor
        # 健康報告任務
        self.health_report_task = None

        self.notifier = LineNotifier
        self.last_message_time = 0

        print(
            f"#{os.getenv('K_REVISION', 'local')} 初始化 WebSocket Client (對 CMB Main Server) 完成!")

    async def connect(self):
        """主要的連接邏輯（已整合監控）"""

        max_total_retry_time = 600  # 連線失敗 10 分鐘就重新開機
        start_retry_time = time.time()

        self.server_connection_monitor.last_disconnect_time = time.time()
        while True:
            try:
                start_time = time.time()
                logging.info("嘗試連接到伺服器(CMB Main Server)...")

                if time.time() - start_retry_time > max_total_retry_time:
                    logging.error("連線失敗超過時間限制，結束容器以觸發重啟")
                    sys_exit()
                    return

                if ConnectionBlocker:
                    ws_url = "wss://fail"
                    pass
                else:
                    ws_url = self.ws_url
                    pass
                async with websockets.connect(
                    # self.ws_url,
                    ws_url,
                    # ping_interval=30,
                    # ping_timeout=10,
                    ping_interval=10,  # 原本是 30，改小可更快偵測
                    ping_timeout=5,    # 原本是 10，改小可更快判定失敗
                ) as ws_server:

                    connect_time = (time.time() - self.server_connection_monitor.last_disconnect_time)
                    print(f"已成功連線!(斷線 {connect_time:.2f} 秒) ")

                    self.ws_server = ws_server
                    # 記錄成功連線
                    await self.server_connection_monitor.record_connect()
                    logging.info(
                        f"#{os.getenv('K_REVISION', 'local')} 已連接到 CMB Main Server {self.ws_url}")



                    # 發送連接數據（重試機制）
                    max_retries = 6
                    for attempt in range(max_retries):
                        try:
                            connect_data = {"source": "tawe"}
                            await self.ws_server.send(json.dumps(connect_data))
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1)
                            continue

                    # 開始監聽消息
                    await self.listen()

                    reason = "連接關閉, 原因: 'Sever 斷線?!'"
                    # logging.info(reason)
                    await self.server_connection_monitor.record_disconnect(reason)

                    # 連線持續時間計算
                    connected_duration = time.time() - start_time
                    threshold = 5

                    start_retry_time = time.time()

                    if connected_duration > threshold:
                        # await asyncio.sleep(0.5)      # !!!@@@
                        continue
                    else:
                        await asyncio.sleep(threshold)

            except websockets.exceptions.ConnectionClosed as e:
                reason = f"CMB Main Server 連接關閉，代碼: {e.code}, 原因: '{e.reason}'"
                logging.info(reason)
                # await self.server_connection_monitor.record_disconnect(reason)
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(
                    self.retry_delay * 2, self.max_retry_delay)
                start_retry_time = time.time()

            except Exception as e:
                reason = f"連線到 CMB Main Server 發生未知錯誤: {e}"
                logging.info(reason)
                # await self.server_connection_monitor.record_disconnect(reason)
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(
                    self.retry_delay * 2, self.max_retry_delay)

    # async def graceful_shutdown(self):
    #     """執行優雅關閉程序"""
    #     logging.critical("執行優雅關閉程序...")

    #     try:
    #         # 1. 取消健康報告任務
    #         if self.health_report_task:
    #             self.health_report_task.cancel()
    #             try:
    #                 await self.health_report_task
    #             except asyncio.CancelledError:
    #                 pass

    #         # 2. 關閉 WebSocket 連接
    #         if self.ws_server:
    #             await self.ws_server.close()

    #         # 3. 等待短暫時間讓操作完成
    #         await asyncio.sleep(2)

    #     except Exception as e:
    #         logging.error(f"優雅關閉過程中發生錯誤: {e}")
    #     finally:
    #         # 4. 退出進程
    #         logging.critical("進程退出")
    #         sys.exit(1)

    async def health_report_loop(self):
        """每10分鐘生成健康報告"""
        while True:
            try:
                await asyncio.sleep(600)  # 10分鐘
                report = await self.server_connection_monitor.generate_health_report()
                # logging.info("🔍 系統健康報告:", extra={"custom_json": report})
                # print(f"\n🔍 系統健康報告:\n{report}")
                logging.info(f"🔍 系統健康報告:\n{report}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"生成健康報告時出錯: {e}")

    async def heartbeat_task(self):
        """每分鐘執行的心跳任務"""
        # while True:
        while ws_server != None:
            try:
                await asyncio.sleep(10)  # 每x秒檢查一次
                # logging.info("heartbeat_task。")
                # 執行心跳邏輯
                # await self.send_heartbeat()

                # 檢查健康狀態
                await self.server_connection_monitor.check_health()

                # 如頻繁斷線則x分鐘 Line 才呼叫一次.
                if self.server_connection_monitor.should_notify() and time.time() - self.last_message_time >= (5*60):
                    self.last_message_time = time.time()
                    logging.warning("⚠️  需要發送通知!")

                    version_label = {
                        'Trial': "Trial Version",
                        'Local': "Local Version",
                        'Live': "Live Version"
                    }.get(run_mode, "Unknown Version")

                    message = (
                        f"     ===== {version_label}! =====\n"
                        f"叫叫我 Caller Server 頻繁斷線!!!\n"
                        f"30分鐘內斷線次數: {self.server_connection_monitor.get_recent_disconnect_count()}"
                    )

                    send_result = self.notifier.send_event_message(
                        "event_1", status=message)
                    self.server_connection_monitor.reset_notify_flag()

                # 檢查是否需要重啟
                # if self.server_connection_monitor.should_restart():
                #     logging.critical("🚨 觸發重啟機制!")
                #     await self.graceful_shutdown()
                #     break

                # await asyncio.sleep(10)  # 每分鐘檢查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"心跳任務執行失敗: {e}")
                await asyncio.sleep(10)

    async def run(self):
        """主運行循環"""
        # 啟動健康報告任務
        self.health_report_task = asyncio.create_task(
            self.health_report_loop())

        # 啟動心跳任務
        heartbeat_task = asyncio.create_task(self.heartbeat_task())

        try:
            # 啟動主連接循環
            await self.connect()
        except asyncio.CancelledError:
            logging.info("應用程式被取消")
        finally:
            # 清理任務
            heartbeat_task.cancel()
            self.health_report_task.cancel()

            try:
                await heartbeat_task
                await self.health_report_task
            except asyncio.CancelledError:
                pass

    async def process_reset(self, input_data):      # 將 Caller 叫號號碼歸零
        global periodic_pass
        periodic_pass = True
        # 判斷是單一還是全部
        data = json.loads(input_data)
        new_num = 0

        print('')   # 避免 GOOGLE 記錄檔篩選條件時看不到
        if data["caller_id"] != "all":
            # 單一 - 直接印出 caller_id
            # print(data["caller_id"], flush=True)
            caller_id = data["caller_id"]
            print(f'reset caller_id: {caller_id}')
            # 更新叫號資訊
            await client_manager.update_caller_info(caller_id, new_num)
            # 傳送給全部
            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff)
        else:
            clients = await client_manager.get_all_clients()  # 使用 await 取得實際資料
            excluded = data["excluded"]
            # 從 excluded 中提取 caller_id (去掉 vendor_id 前綴)
            excluded_ids = [x.split('_')[1] for x in excluded if '_' in x]

            for caller_id, info in clients.items():
                if caller_id in excluded_ids:
                    print(f'pass reset caller_id: {caller_id}')
                else:
                    print(f'reset caller_id: {caller_id}')
                    # 更新叫號資訊
                    await client_manager.update_caller_info(caller_id, new_num)
                    # 傳送給全部
                    await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff)

        data["result"] = "OK"
        logging.info(
            f"回覆 OK 至 CMB Main Server_R:{json.dumps(data)} ")
        # 至 CMB Main Server
        await ws_server.ws_client.send(json.dumps(data), "RESET_OK_RETURN")      # async def send(
        periodic_pass = False

    async def generate_mock_message(self, message_data):
        """生成模擬訊息並放入佇列"""
        mock_message = json.dumps(message_data)
        logging.info(f"生成模擬訊息: {mock_message}")
        await self.message_queue.put(mock_message)

    async def _websocket_listener(self):
        """專門負責從 WebSocket 接收訊息並放入佇列"""
        logging.info("_websocket_listener 啟動!")
        # self.connected = True
        try:
            async for message in self.ws_server:
                if message is None:
                    logging.info(f"WebSocket 收到無效訊息 '{message}'。")
                else:
                    await self.message_queue.put(message)
            logging.info("WebSocket 連線已關閉，監聽任務結束。")
        except asyncio.CancelledError:
            logging.warning("WebSocket 監聽任務已被取消!!!")
        except Exception as e:
            logging.info(f"WebSocket 監聽發生錯誤: '{e}'!")
        # logging.info("WebSocket 發送 None 訊息。")
        logging.info("WebSocket 監聽結束，已將 Poison Pill 放入訊息佇列。")
        # self.connected = False
        await self.message_queue.put(None)  # 發送 Poison Pill

    async def listen(self):     # CMB Main Server
        """處理接收到的訊息"""
        # self.connected = True
        # print(
        #     f'\nCMB Main Server WebSocketClient listen 啟動! {self.connected}', flush=True)
        logging.info("CMB Main Server WebSocketClient listen 啟動!")
        listen_start = time.time()
        try:
            self.websocket_listener_task = asyncio.create_task(
                self._websocket_listener())
            # self.connected = True

            # 清除 self.message_queue
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                    self.message_queue.task_done()  # 如果使用了 join()，需要调用 task_done()
                except asyncio.QueueEmpty:
                    break

            # async for message in self.ws_server:
            while True:     # !!!@@@
                # while self.connected:
                # 從佇列中等待並取出訊息
                message = await self.message_queue.get()
                # print("^", end=' ', flush=True)
                # print(f"listen: {message}")
                # 檢查是否為斷線訊息 (Poison Pill)
                if message is None:
                    logging.info("收到斷線通知，Listen 任務準備結束。")
                    break  # 跳出 while 循環，結束 listen 任務或觸發重連

                try:
                    # logging.info(f"CMB接收: {message}")
                    if not is_json(message):
                        logging.warning(f"收到非 JSON 訊息，略過: {message}")
                        continue

                    self.cmb_msg = message  # 儲存原始訊息
                    manager.add_data(message)

                    # 優先找出符合直接廣播的 action 的資料
                    cmb_msg = manager.search_data(
                        lambda x: x.get('action') in servsr_replay_active_actions_check)    # ~~~~

                    # 若找不到符合直接廣播的 action 的資料，嘗試找 wait_time_avg, ( *** send 回覆 ***)
                    if not cmb_msg and not manager.search_data(lambda x: 'action' in x):
                        cmb_msg = manager.search_data(
                            lambda x: "wait_time_avg" in x)
                        if not cmb_msg:
                            logging.warning(
                                "找不到 wait_time_avg 資料，略過處理")    # 錯誤!
                            continue

                        # 例行資料(send), 移除且不廣播.
                        if cmb_msg[0].get('wait_time_avg') == '':
                            # print(f'0_cmb_msg:{cmb_msg}')
                            manager.remove_matched(cmb_msg)
                            continue
                        # print(f'1_cmb_msg:{cmb_msg}')
                        pass

                    if cmb_msg:             # CMB Main Server, listen
                        # 如果是 CSV login 則不處理
                        # if cmb_msg[0].get('uuid', '').startswith('CSV_') and cmb_msg[0].get('action', '') == 'login':
                        #     print(" CSV login! ")
                        #     continue

                        # Logger.log(f"收到 CMB Main Server JSON 訊息: {message}")
                        # print(f'2_cmb_msg:{cmb_msg}')
                        json_data = cmb_msg[0]
                        manager.remove_matched(cmb_msg)
                        caller_id = json_data.get('caller_id', '')
                        action = json_data.get('action', '')
                        # if action == '':
                        #     action = json_data.get(
                        #         'action_0', '')     # 備援 action 欄位
                        if action == '':    # send, 設 'action' 值為 'send'
                            json_data['action'] = 'send'
                            action = json_data.get('action', '')

                            # if not caller_id and json_data['action'] != 'reset_caller':
                        if not caller_id:
                            logging.error(f"回覆資料錯誤，缺少 caller_id: {cmb_msg}")
                            continue

                        # CMB Main Server, listen
                        if action == 'new_get_num':     # 群發至店家 及 訪客
                            # logging.info(f"群發訊息至 SOFT cmb-caller 的 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            # 2025/08/01 改
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2+0x4))
                        elif action == 'reset_caller':
                            logging.info(
                                f"收到 reset_caller 訊息: {json.dumps(cmb_msg)}")
                            await self.process_reset(json.dumps(json_data))
                        elif action == 'get_num_switch':    # get_num_switch 群發訊息至非 H/W Caller 及 訪客
                            # logging.info(f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            # logging.info(f"群發訊息至 caller_id:{caller_id}, action:{json_data.get('action', '')}, switch:{json_data.get('switch', '')}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2+0x4))
                        elif action == 'cancel_get_num':    # 群發訊息至非 H/W Caller 及 訪客
                            logging.info(
                                f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            # 2025/08/06 改
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2+0x4))
                        elif action == 'reserve_number':
                            logging.info(
                                f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', 0x2)
                        elif action == 'send' or action == '':  # send 群發訊息至非 H/W Caller，因需要 "wait_time_avg"
                            # logging.info(f"群發訊息至非 Caller. caller_id={caller_id}: {json.dumps(cmb_msg)}, send")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2))
                        elif action == 'set_params':    # set_params 群發訊息至非 H/W Caller 及 訪客
                            # logging.info(f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2+0x4))
                        elif action == 'set_time_period':    # set_time_period 群發訊息至非 H/W Caller 及 訪客
                            # logging.info(f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', (0x2+0x4))
                        elif action == 'login':     # listen
                            # logging.info(f"發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            logging.info(
                                f"回覆訊息至 caller_id={caller_id}: {json_data}")
                            # print(f"login_buffer:{await login_buffer.get_all()}")
                            websocket_info = await login_buffer.get(json_data['uuid'].removeprefix('CSV_'))
                            await login_buffer.remove(json_data['uuid'].removeprefix('CSV_'))
                            websocket = websocket_info['websocket']
                            ws_type = websocket_info['ws_type']

                            if json_data["result"] == "OK":          # Json
                                # 驗證成功

                                # try:
                                #     # print(f' {caller_id},驗證成功_J_1! ',end='', flush=True)
                                #     # print(f'{caller_id},{json_data}')

                                try:
                                    if websocket.open:
                                        # 至 caller
                                        # print(f' {caller_id},驗證成功_J_2_1! ',end='', flush=True)

                                        # 更新叫號資訊
                                        clients = await client_manager.get_all_clients()

                                        # 防止 caller_id 不存在或 caller_num 欄位缺失
                                        caller_num = clients.get(
                                            caller_id, {}).get('caller_num', -1)

                                        if not json_data.get('uuid', '').startswith('CSV_'):
                                            if "hardware" not in json_data:   # 如未設就加入
                                                # 虛擬機器
                                                if json_data.get("caller_id", "").startswith("v"):
                                                    json_data["hardware"] = False
                                                else:
                                                    json_data["hardware"] = True
                                            # print(
                                            #     f'{caller_id},{ws_type},驗證成功_J! ', end='\n', flush=True)
                                            await websocket.send(json.dumps(json_data))
                                        else:
                                            # print(f'{caller_id},{ws_type},驗證成功_C! ', end='\n', flush=True)
                                            # print(f"CSV AUTH:{json_data} ")
                                            #
                                            await websocket.send(f"OK,{json_data.get('caller_name','')},auth")
                                        await client_manager.add_connection(caller_id, websocket, ws_type)

                                        # 防止 curr_num 欄位不存在
                                        curr_num = json_data.get(
                                            'curr_num', -1)

                                        # 如果 caller_num 是大於 0 的整數，且與 curr_num 不同，就更新 curr_num 並印出結果
                                        if isinstance(caller_num, int) and caller_num >= 0 and curr_num != caller_num:
                                            print(
                                                f"Issue {caller_id} curr_num:{caller_num} <-> {curr_num}")
                                            json_data['curr_num'] = caller_num
                                        curr_num = json_data.get(
                                            'curr_num', -1)
                                        if (curr_num < 0):

                                            print(
                                                f"收到_0 {caller_id} curr_num<0 ({curr_num}) 不更新現在叫號值:{caller_num}", flush=True)

                                            # # 2025/09/24 失敗!
                                            # print(f"{caller_id}: 發送 get_num_info!", flush=True )
                                            # send_data = {
                                            #     'action': "get_num_info",         # 動作指令
                                            #     "vendor_id": self.vendor_id,      # 叫號機廠商 id
                                            #     "caller_id": caller_id,          # 叫號機 id
                                            #     "uuid": hex(id(websocket))
                                            # }

                                            # # Try Block added for reconnection logic or error handling
                                            # try:
                                            #     if not self.ws_client:
                                            #         print('login_get_num_info: ws_client 已斷線!')
                                            #         # 這裡可以嘗試重連 ws_client，或直接跳過
                                            #         pass
                                            #     else:
                                            #         try:
                                            #             print(f'ws_client.send: {json.dumps(send_data)}')
                                            #             # 至 CMB Main Server
                                            #             await self.ws_client.send(json.dumps(send_data), "login_get_num_info")    # async def send(
                                            #         except Exception as e:
                                            #             logging.error(
                                            #                 f"login_get_num_info 傳送至 Server 失敗): {e}")
                                            # except Exception as e:
                                            #     logging.error(f"login_get_num_info 外層 Try 失敗: {e}")

                                            pass
                                        else:
                                            print(
                                                f"OK  {caller_id} curr_num:{caller_num} <-> {json_data['curr_num']}")
                                            # login 會傳回目前號碼 "curr_num"
                                            await client_manager.update_caller_info(caller_id, json_data['curr_num'])
                                    else:
                                        logging.warning(
                                            f"WebSocket 已關閉，無法回傳成功訊息給 {caller_id}")
                                except Exception as e:
                                    logging.error(
                                        f"傳送成功訊息至 Caller {caller_id} 失敗: {e}")

                                # except Exception as e:
                                #     logging.error(
                                #         f"驗證成功處理時發生錯誤: {e}")
                                #     return False
                            else:
                                # 驗證失敗
                                print(
                                    f'驗證失敗 {caller_id},{json_data}')
                                try:
                                    if websocket.open:
                                        # 至 caller
                                        if not json_data.get('uuid', '').startswith('CSV_'):
                                            await websocket.send(json.dumps(json_data))
                                        else:
                                            code = json_data.get("result").split(
                                                ',')[1].split(':')[0].strip()
                                            msg_map = {
                                                '051': '001:驗證失敗',
                                                '003': '001:驗證失敗',
                                                '002': '002:無效的CallerID',
                                                '001': '006:無效的CMD指令',
                                                '009': '007:文字錯誤/其它'
                                            }
                                            msg = msg_map.get(code, '001,驗證失敗')
                                            print(f'{caller_id},{msg}')
                                            # 至 Caller
                                            # 至 caller
                                            await websocket.send(f"Fail, {msg},auth")
                                    else:
                                        logging.warning(
                                            f"WebSocket 已關閉，無法回傳失敗訊息給 {caller_id}")
                                except Exception as e:
                                    logging.error(
                                        f"傳送失敗訊息至 Caller {caller_id} 失敗: {e}")
                                # return False
                            # if not json_data.get('uuid', '').startswith('CSV_'):
                            #     log_mode = 'JSON'
                            # else:
                            #     log_mode = 'CSV'
                            # print(f"login {log_mode} 流程結束! ")

                        else:   # 未定義,群發至全部
                            logging.info(
                                f"群發未定義訊息至全部 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', 0xff)
                            websocket = await login_buffer.get(json_data['uuid'])
                            # await websocket.send(json.dumps(json_data))
                            pass

                        # print(f'return check {action}')
                        if action in servsr_active_actions_replay_ok_check:     # 檢查是否需要回覆 OK
                            json_data["result"] = "OK"
                            logging.info(f"回覆 OK 至 CMB Main Server_B:{json.dumps(json_data)} ")
                            # 至 CMB Main Server
                            await ws_server.ws_client.send(json.dumps(json_data), "OK_RETURN")      # async def send(
                            pass

                    else:
                        # Logger.log(f"收到 JSON 訊息:{json.loads(message)['action']} 未處理!(由 handle_json_cmd_with_reply 處理)" )
                        # Logger.log(f"收到 JSON 訊息:{json.loads(message)['action']} 未處理!(由 handle_json_cmd_with_reply 處理), {json.loads(message)}" )
                        # Logger.log(f"收到 JSON 訊息:{json.loads(message)['action']} 廣播未處理." )
                        pass

                except Exception as inner_e:
                    logging.error(
                        f"處理單一訊息時發生錯誤: {inner_e}\n訊息內容: {message}", exc_info=True)
                    continue  # 明確表示繼續下一輪循環

        except websockets.exceptions.ConnectionClosedError as e:
            logging.info(f"listen CMB Main Server 連接中斷: {e}")
            await asyncio.sleep(1)
            # 這裡可以選擇重新連接或退出
            raise  # 如果是連接問題，可能需要重新建立連接

        except Exception as e:
            logging.error(f"CMB Main Server 發生未預期錯誤: {e}", exc_info=True)
            await asyncio.sleep(1)
            # 對於其他未預期錯誤，可以選擇繼續運行
            # 移除 raise 以繼續執行
            # raise e
        finally:
            if self.websocket_listener_task:
                self.websocket_listener_task.cancel()
                try:
                    await self.websocket_listener_task
                    logging.info("websocket_listener_task 任務已正常停止。")
                except asyncio.CancelledError:
                    logging.info("websocket_listener_task 任務已被取消。")
                except Exception as e:
                    logging.error(f"websocket_listener_task 任務停止時發生錯誤: {e}")

            logging.info(
                f"Listen 任務已停止! 連線時長:{(time.time()-listen_start):.2f} Sec")

    async def send(self, message, text=None):      # 至 CMB 主伺服器訊息, 統一由此處發出
        # 你可以根據 text 是否為 None 來做不同處理
        if not text:
            text = ''
        """發送訊息"""
        async with self.ws_server_server_lock.acquire(f"ws_server_lock send: {text}, {message}"):
            try:
                # Logger.log(f"發送訊息至 CMB Main Server: {text}, {message} ")
                if self.ws_server:
                    # 至 CMB Main Server
                    await self.ws_server.send(message)
            except Exception as e:
                Logger.log(f"[ws.send] 傳送至Server失敗 {message}, {str(e)}")
                raise  # 向上拋出,異常則保留

    async def close(self):     # CMB Main Server
        """關閉 WebSocket 連接"""
        print("關閉 CMB Main Server WebSocket 連接!!!")
        if self.ws_server:
            await self.ws_server.close()
            self.ws_server = None


def is_json(my_string):
    try:
        json.loads(my_string)
        return True
    except ValueError:
        return False

# cmb-caller-frontend WebSocket Server, 連結 Caller

# 檢查是否已登錄


def has_websocket(clients, target_websocket):
    for client_data in clients.values():
        if target_websocket in client_data['connections']:
            return True
    return False


# 連接至 Caller (Client)
class WebSocketServer:
    global server_connection_monitor

    def __init__(self, host, port):             # Caller
        """初始化 WebSocket Server"""
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None   # 連結至 CMB Main Server 用
        self.server = None      # 連結至 Caller 用
        self.last_num = 0
        # self.ws_type = -1
        self.server_timeout = 2     # 秒, 3 -> 2
        self.ws_device_lock = NotifyingLock('ws_device_lock')
        self.server_connection_monitor = server_connection_monitor
        print(
            f"#{os.getenv('K_REVISION', 'local')} 初始化 WebSocket Server (對Caller) 完成!")

    async def start(self):                      # Caller
        """啟動Server"""
        self.server = await websockets.serve(   # !!!@@@@
            self.handler,
            self.host,
            self.port,
            ping_interval=5,      # xx 秒，減少資源消耗
            ping_timeout=5,       # xx 秒，給予寬裕的回應時間
            max_size=4096,        # 限制訊息大小，避免記憶體問題
            compression=None       # ESP32 不需要壓縮，可提高效能
        )
        logging.info(
            f"#{os.getenv('K_REVISION', 'local')} cmb-caller-frontend WebSocket Server 已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()  # 保持Server運行

    async def stop(self):
        """強制快速關閉 WebSocket 伺服器"""
        if self.server:
            self.server.close()  # 停止接受新連接
            try:
                # 設定超時（例如 2 秒），避免卡住
                await asyncio.wait_for(self.server.wait_closed(), timeout=1.0)
            except asyncio.TimeoutError:
                # 超時後強制關閉所有連接
                for ws in set(self.server.websockets):  # 遍歷所有活躍連接
                    await ws.close(code=1001, reason="Server shutdown")
            logging.info("WebSocket 伺服器已強制關閉")
            print(
                f"\n***** #{os.getenv('K_REVISION', 'local')} Websocket Server 伺服器已強制關閉!!! *****\n", flush=True)

    # async def stop(self):                           # Caller
    #     """停止Server"""
    #     if self.server:
    #         self.server.close()
    #         await self.server.wait_closed()
    #         print(
    #             f"\n***** #{os.getenv('K_REVISION', 'local')} Websocket Server 已關閉!!! *****\n", flush=True)

    async def handler(self, websocket, path):       # 多個 Caller 傳入 (連線先到這裡)
        """處理新Client連接"""
        new_connect = True
        # response_auth = False
        caller_id = None
        caller_id_0 = None
        remove_socket = False

        print(f'\n新連線:{websocket} ! ', flush=True)
        try:
            async for message in websocket:
                try:
                    # print(f'handler:{message}', flush=True)
                    await self.process_message(message, websocket, new_connect)
                    new_connect = False  # 第一次處理後設為False
                except Exception as e:
                    logging.warning(f"處理 Caller 訊息時發生錯誤: {e}", exc_info=True)
                    # caller
                    # await websocket.send(json.dumps({"result": "Fail, 005:處理訊息錯誤"}))
                    try:
                        await websocket.send(json.dumps({"result": "Fail, 005:處理訊息錯誤"}))
                    except Exception as send_err:
                        logging.error(f"回傳錯誤訊息時失敗: {send_err}", exc_info=True)

        except websockets.exceptions.ConnectionClosed as e:
            def get_caller_id_by_websocket(websocket, clients):
                for caller_id, info in clients.items():
                    if websocket in info.get('connections', {}):
                        return caller_id
                # return None
                return '未知'

            try:
                clients = await client_manager.get_all_clients()  # !!!@@@
                caller_id = get_caller_id_by_websocket(websocket, clients)

                if caller_id:
                    caller_id_0 = caller_id
                else:
                    caller_id = caller_id_0
                    print(
                        f'\ncaller_id 可能不正確 {caller_id},{websocket} !!!', flush=True)

                # ws_type = clients.get(caller_id, {}).get('connections', {}).get(websocket)
                # ws_type = clients[caller_id]['connections'][websocket]['ws_type']
                try:
                    ws_type = clients[caller_id]['connections'][websocket]['ws_type']
                except KeyError:
                    ws_type = None  # 或其他預設值

                if ws_type is None:
                    print(
                        f"ws_type 無法取得，caller_id={caller_id},{websocket}", flush=True)
                    ws_type = 0

                # caller_id 未知表示剛連接還未 login 程式就關閉了
                logging.warning(
                    f"客戶端 {caller_id or '未知'},{websocket},{ws_type} 斷開連接 (code: {e.code}, reason: {e.reason})"
                )

                remove_socket = True

                json_data = {
                    'action': "wifi_get_status",
                    "caller_id": caller_id,
                    "result": "Fail, 002:device not found",
                    "uuid": hex(id(websocket))
                }

                if ws_type & 1:     # H/W Caller.
                    # print(f' 傳送斷線廣播!{caller_id},{ws_type} ', flush=True)
                    await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', 0x8)
                else:
                    # print(f'不傳送斷線廣播!{caller_id},{ws_type} ', flush=True)
                    pass

            except Exception as e:
                logging.error(f"處理斷線時發生錯誤: {e}", exc_info=True)

        except asyncio.CancelledError:
            logging.info(f"客戶端 {caller_id or '未知'} 任務被取消")
            remove_socket = True
        except Exception as e:
            logging.error(
                f"處理客戶端 {caller_id or '未知'} 時發生未預期錯誤: {e}", exc_info=True)
            remove_socket = True
        finally:
            if remove_socket and caller_id:
                await self.cleanup_connection(caller_id, websocket)

    async def process_message(self, message, websocket, is_new_connection=False):
        # print(f"process_message:{message}, {websocket}, {is_new_connection}")
        # global get_num_info_frontend
        """處理來自客戶端的訊息"""
        # print(f'Message:{message}', flush=True)
        try:
            # 嘗試解析為JSON格式
            json_data = json.loads(message)
            await self.process_json_message(json_data, websocket, is_new_connection)
        except json.JSONDecodeError:
            # 非JSON格式訊息處理
            await self.process_non_json_message(message, websocket, is_new_connection)

    # Caller
    async def process_json_message(self, json_data, websocket, is_new_connection):
        # disconnet_id = 'z0002'  # 斷線測試指定ID
        disconnet_id = '_____'

        """處理 JSON 格式訊息"""
        try:
            # check = 0
            caller_id = json_data.get(
                'caller_id') or json_data.get('device_id')
            action = json_data.get('action')
            if not action:
                # print(f"No action:{json_data}")
                action = 'SEND'
            if is_new_connection:
                print(
                    f'\n#{revision},{timestamp}, 新 Client 連接_JSON:{caller_id},{action} ', end='', flush=True)
            connect_time = 0
            if (self.server_connection_monitor.last_connect_time >= self.server_connection_monitor.last_disconnect_time):
                connect_time = time.time() - self.server_connection_monitor.last_connect_time
                # print(f"process_json_message 已連線 {time.time() - self.server_connection_monitor.last_connect_time}秒")
            else:
                connect_time = - \
                    (time.time() - self.server_connection_monitor.last_disconnect_time)
                # print(f"process_json_message 已斷線 {time.time() - self.server_connection_monitor.last_disconnect_time}秒")
            if connect_time >= 0:
                # print(f"process_json_message 已連線 {connect_time}秒({action})")
                pass
            else:
                # print(f"process_json_message 已斷線 {-connect_time}秒({action})")
                pass
            if action == 'login':   #
                # return await self.handle_auth_json(caller_id, json_data, websocket)
                if connect_time <= -10 or caller_id == disconnet_id:     # 斷線超過時間就不讓連線
                    logging.info(f"server 斷線中_0! ({caller_id},{action}) ")
                    json_data["result"] = "Fail, 005:disconnected from the center"
                    await websocket.send(json.dumps(json_data))
                    return
                else:
                    return await self.handle_json_cmd_without_reply(caller_id, json_data, websocket)

            # 檢查是否已驗證
            if not await self.check_authentication(caller_id, websocket):
                logging.info(f"1_尚未登入: {json_data}")
                await websocket.send(json.dumps({"result": "Fail, 004:not logged in"}))
                return

            # 處理 WiFi 指令
            if action and action.startswith("wifi_"):
                await self.handle_wifi_command(caller_id, json_data, websocket)
                return

            # 一律斷線超過時間就不讓連線 !!!@@@
            if connect_time <= -10 or caller_id == disconnet_id:     # 斷線超過時間就不讓連線
                logging.info(f"server 斷線中_1! ({caller_id},{action}) ")
                json_data["result"] = "Fail, 005:disconnected from the center"
                await websocket.send(json.dumps(json_data))
                return

            # 處理其他 JSON 指令
            if action in client_wait_reply_actions_check:
                await self.handle_json_cmd_with_reply(caller_id, json_data, websocket)
            else:
                await self.handle_json_cmd_without_reply(caller_id, json_data, websocket)

        except Exception as e:
            # logging.error(f"[process_json_message],{check} 發生錯誤: {e}")
            # await websocket.send(json.dumps({"result": "Fail, 999:internal error"}))
            try:
                # logging.error(f"[process_json_message],{check} 發生錯誤: {e}")
                logging.error(f"[process_json_message] 發生錯誤: {e}")
                await websocket.send(json.dumps({"result": "Fail, 999:internal error"}))
            except Exception as send_err:
                logging.error(
                    f"[process_json_message] 回傳錯誤訊息時又發生錯誤: {send_err}")

    async def process_non_json_message(self, message, websocket, is_new_connection):
        """處理非JSON格式訊息"""
        try:
            caller_id, m_cmd, m_info = self.parse_message(message)

            if is_new_connection:
                print(
                    f'\n#{revision},{timestamp}, 新 Client 連接_CSV:{caller_id},{m_cmd},{m_info} ', end='', flush=True)

            # 處理特殊指令
            if m_cmd in CALLER_CSV_COMMANDS_TO_PROCESS:
                # 印出接收到的指令資訊
                if m_cmd != 'auth' and m_info:  # 如果指令不是 'auth' 且 m_info 不為空
                    if m_cmd == 'info':  # 換行顯示較清楚
                        print('')
                    print(f'C_收0:{caller_id},{m_cmd},{m_info} ',
                          end='', flush=True)
                else:
                    print(f'C_收1:{caller_id},{m_cmd} ', end='', flush=True)
                if m_cmd == 'info':     # info
                    # print(f'\n發送 WiFi 狀態查詢請求:{caller_id} ')   # 準備 WiFi 資訊，傳送給 WEB Caller 告知有 H/W Caller 連線, 以便能設定 WiFi.
                    json_data = {
                        'action': "wifi_get_status",
                        "caller_id": caller_id,
                        # Caller 之 websocket ID
                        "uuid": hex(id(websocket))
                    }

                    try:
                        # await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x1)
                        # Caller
                        await websocket.send(json.dumps(json_data))
                    except Exception as send_err:
                        logging.error(f"[wifi_get_status] 發生錯誤: {send_err}")

            # print(f"PNJM: {message}")
            # 處理驗證
            if m_cmd == 'auth':
                return await self.handle_auth(caller_id, message.split(','), websocket)

            # 檢查是否已驗證
            if not await self.check_authentication(caller_id, websocket):
                logging.info(f"3_尚未登入:'{caller_id},{m_cmd},{m_info}'")
                # Caller
                try:
                    await websocket.send(f"Fail, 004:not logged in,{m_cmd}")
                except Exception as send_err:
                    logging.error(f"[check_authentication] 發送失敗: {send_err}")
                return

            # 處理各種指令 CSV
            try:
                if m_cmd == 'get_num_info':
                    await self.handle_get_num_info(caller_id, message.split(','), websocket, False)
                elif m_cmd == 'get':
                    await self.handle_get_num_info(caller_id, message.split(','), websocket, True)
                elif m_cmd == 'ping':
                    await self.handle_ping(caller_id, m_info, websocket)
                elif m_cmd == 'info':
                    try:
                        # Caller
                        await websocket.send(f'OK,{caller_id},info')
                    except Exception as send_err:
                        logging.error(f"[info] 發送失敗: {send_err}")
                elif m_cmd in ('send', ''):   # 專門處理 'send'
                    await self.handle_send(caller_id, m_info, websocket)
                else:
                    print(f"錯誤的命令! {caller_id},{m_cmd},{m_info}")
                    try:
                        await websocket.send(f'OK,{caller_id},{self.last_num},{m_cmd}')
                    except Exception as send_err:
                        logging.error(f"[錯誤的命令] 發送失敗: {send_err}")
            except Exception as cmd_err:
                logging.error(
                    f"[process_non_json_message] 指令處理時發生錯誤: {cmd_err}")

        except Exception as e:
            logging.error(f"[process_non_json_message] rty error: {e}")
            try:
                await websocket.send("Fail, 999:internal rty error")
            except Exception as send_err:
                logging.error(
                    f"[process_non_json_message] rty error 回報失敗: {send_err}")

    async def check_authentication(self, caller_id, websocket):
        """檢查是否已通過驗證"""
        clients = await client_manager.get_all_clients()
        return has_websocket(clients, websocket)

    async def handle_wifi_command(self, caller_id, json_data, websocket):
        """處理WiFi相關指令"""
        clients = await client_manager.get_all_clients()

        if 'result' not in json_data:  # WiFi 詢問
            print(f'WiFi 傳送至C:{json_data}')
            clients[caller_id]['connections'][websocket]['ws_type'] |= 0x8
            result = await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x1, websocket)
            if result <= 0:     # 沒有 H/W Caller
                json_data["result"] = "Fail, 002:device not found"
                await websocket.send(json.dumps(json_data))     # Caller
        else:  # WiFi 回應
            print(f'WiFi 接收從C:{json_data}')
            await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x8, websocket)

    async def handle_ping(self, caller_id, m_info, websocket):
        """處理ping指令"""
        await websocket.send('pong')    # Caller
        # clients = await client_manager.get_all_clients()
        # existing_num = clients.get(caller_id, {}).get('caller_num', 0)
        # if existing_num == 0 and m_info.isdigit() and int(m_info) != 0:     # !!!@@@ 須注意
        #     clients[caller_id]['caller_num'] = int(m_info)

    async def handle_send(self, caller_id, m_info, websocket):      # CSV
        """處理send指令"""
        clients = await client_manager.get_all_clients()
        if clients[caller_id]['connections'][websocket]['ws_type'] == 4:  # user_get_num
            logging.info(f"5_尚未登入:'{caller_id},send,{m_info}'")
            await websocket.send("Fail, 004:not logged in,send")    # Caller
            return

        new_num = int(m_info)
        clients[caller_id]['connections'][websocket]['ws_last_modified'] = time.time()
        # 更新叫號資訊
        await client_manager.update_caller_info(caller_id, new_num)
        await websocket.send(f'OK,{caller_id},{new_num},send')      # Caller

        # 記錄時間（秒差用）與格式化時間（log用）
        # conn_info = clients[caller_id]['connections'][websocket]
        # now_ts = time.time()
        # now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # conn_info['ws_last_modified'] = now_ts
        # logging.info(f"6_更新號碼: caller_id={caller_id}, new_num={new_num}, ws_type={conn_info['ws_type']}, 修改時間={now_str} ({now_ts:.2f})")
        respones_Threshold = 0.8    # SEc
        time_since_last_access = clients[caller_id]['connections'][websocket]['ws_last_modified'] - \
            clients[caller_id]['connections'][websocket]['ws_connect_time']
        if clients[caller_id]['connections'][websocket]['ws_type'] == 1 and (time_since_last_access < 1.0):
            print(f"Caller {caller_id} C_存取時差: {time_since_last_access}")
        if clients[caller_id]['connections'][websocket]['ws_type'] == 1 and (time_since_last_access < respones_Threshold):
            # 傳給發送端,避免斷線重聯時 H/W Caller 顯示資料與 Server 上不同
            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff)
            print(
                f"Caller C_update 傳給發送端: {caller_id},{new_num}, C_存取時差: {time_since_last_access}")
        else:
            # 不傳給發送端
            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff, websocket)
        # 至 CMB Main Server
        await self.handle_send_message(caller_id, new_num, websocket)

    async def cleanup_connection(self, caller_id, websocket):       # handler 發現
        """清理斷開的連接"""
        try:
            clients = await client_manager.get_all_clients()
            if caller_id in clients and websocket in clients[caller_id]['connections']:
                print(next((
                    f"\n1_discard: {caller_id},{ws}, 类型: {info['ws_type']}"
                    for ws, info in clients[caller_id]['connections'].items()
                    if ws == websocket
                ), "未找到 websocket"), flush=True)
                await client_manager.remove_connection(caller_id, websocket)
        except Exception as cleanup_error:
            logging.error(f"清理資源時發生錯誤: {cleanup_error}", exc_info=True)

    # Caller
    async def handle_json_cmd_without_reply(self, caller_id, json_data, websocket):
        try:
            # HJCWOR_start = time.time()
            action = json_data.get('action', 'SEND')
            try:
                async with self.ws_device_lock.acquire(f"ws_device_lock json_cmd_WOR:{caller_id},{action}"):
                    # print(f"handle_json_cmd_without_reply {json_data}!!!")
                    # action_value = json_data.get('action')
                    max_retries = 6
                    retry_delay = 1
                    for attempt in range(max_retries):
                        if attempt >= 1:
                            print(
                                f'handle_json_cmd_without_reply "{action}" Retry {attempt+1}/{max_retries}')
                        if self.ws_client:
                            try:
                                # 若是 send 則先 發送 update 再傳至 CMB Main Server.
                                # if not 'action' in json_data:           # JSON 'send', OK 由 CMB Main Server 回傳
                                if action == "SEND":           # JSON 'send', OK 由 CMB Main Server 回傳
                                    try:
                                        if not "call_num" in json_data:
                                            logging.warning(
                                                "找不到 call_num 資料，略過處理")
                                            return
                                        new_num = json_data.get('call_num')
                                        print(
                                            f'J_收1:{caller_id},send,{new_num} ', end='', flush=True)
                                        # 更新叫號資訊
                                        await client_manager.update_caller_info(caller_id, new_num)

                                        clients = await client_manager.get_all_clients()
                                        clients[caller_id]['connections'][websocket]['ws_last_modified'] = time.time(
                                        )
                                        time_since_last_access = clients[caller_id]['connections'][websocket]['ws_last_modified'] - \
                                            clients[caller_id]['connections'][websocket]['ws_connect_time']
                                        if (time_since_last_access < 1.0):
                                            print(
                                                f"J_存取時差: {time_since_last_access}")
                                        # if (time_since_last_access > 0.4):
                                        if True:    # JSON 先不傳送給發送端
                                            # 'update' 不傳送給發送端
                                            # send 處理較特殊，其餘命令大多為收到 CMB Main Server 資料後直接廣播.
                                            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff, websocket)
                                        else:
                                            # 'update'  會傳送給發送端
                                            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff)
                                            print(
                                                f"J_update 傳給發送端, J_存取時差: {time_since_last_access}")
                                    except Exception as e:
                                        logging.error(
                                            f"handle_json_cmd_without_reply 處理 SEND 命令時發生錯誤: {e}")
                                        continue

                                # Json, 尚無 H/W Caller login 功能.
                                # elif json_data.get('action') == 'login':
                                elif action == 'login':
                                    try:
                                        json_data['uuid'] = hex(id(websocket))
                                        if json_data.get('password') == 'user_get_num':
                                            print(
                                                f'\n*** user_get_num:{caller_id} Login_J *** ', end='', flush=True)
                                            ws_type = 4
                                        else:
                                            print(
                                                f'\n*** SOFT CMB Caller:{caller_id} login_J *** ', end='', flush=True)
                                            ws_type = 2
                                        print(
                                            f"J_收0:{caller_id},login,{ws_type} ", end='', flush=True)
                                        await login_buffer.add(websocket, ws_type)
                                    except Exception as e:
                                        logging.error(
                                            f"handle_json_cmd_without_reply 處理 LOGIN 命令時發生錯誤: {e}")
                                        continue
                                else:
                                    try:
                                        print(f"J_收2:{caller_id},{action} ",
                                              end='', flush=True)
                                    except Exception as e:
                                        logging.error(
                                            f"handle_json_cmd_without_reply 處理其他命令時發生錯誤: {e}")
                                        continue

                                # 大部分命令直接傳至 CMB Main Server
                                # 至 CMB Main Server
                                # print(f"handle_json_cmd_without_reply 傳送至 CMB Main Server: {json_data}!!!")
                                try:
                                    await self.ws_client.send(json.dumps(json_data), "HJCWOR")      # async def send(
                                    if json_data.get('action') == 'login':      # 顯示 login 耗時
                                        # print(f"\nLogin JSON,{caller_id},{ws_type} 耗時:{time.time() - HJCWOR_start}")
                                        pass
                                    return
                                except Exception as e:
                                    logging.error(
                                        f"handle_json_cmd_without_reply 傳送資料至 CMB Main Server 時發生錯誤: {e}")
                                    raise

                            except Exception as e:
                                logging.error(
                                    f"handle_json_cmd_without_reply,{action} 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}, {json.dumps(json_data)} ")
                                # traceback.print_exc()
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                continue
            except Exception as e:
                logging.error(f"handle_json_cmd_without_reply 獲取鎖時發生錯誤: {e}")
                await websocket.send("Fail, 004:伺服器忙碌中")
        except Exception as e:
            logging.error(f"handle_json_cmd_without_reply 發生未捕捉錯誤: {e}")
            await websocket.send("Fail, 002:伺服器內部錯誤")

    async def handle_json_cmd_with_reply(self, caller_id, json_data, websocket):
        try:
            action = json_data.get('action', '')
            print(f"J_收3:{caller_id},{action} ", end='', flush=True)
            # print(f"0_handle_json_cmd_with_reply {json_data}!!!")
            try:
                async with self.ws_device_lock.acquire(f"ws_device_lock json_cmd_WR:{caller_id},{json_data.get('action')}"):
                    # print(f"1_handle_json_cmd_with_reply {json_data}!!!")
                    # action_value = json_data.get('action')
                    pass
                    max_retries = 6
                    retry_delay = 1
                    for attempt in range(max_retries):
                        if attempt >= 1:
                            print(
                                f"handle_json_cmd_with_reply Retry,{action} {attempt+1}/{max_retries}")
                        if self.ws_client:
                            try:
                                # 至 CMB Main Server
                                # print(f"handle_json_cmd_with_reply 傳送至 CMB Main Server:{json_data}")
                                await self.ws_client.send(json.dumps(json_data), "HJCWR")   # async def send(
                                # 等待回應
                                # print('handle_json_cmd_with_reply 等待回應')
                                start_time = time.time()
                                cmb_msg = []
                                while not cmb_msg and time.time() - start_time < self.server_timeout:       # x 秒
                                    try:
                                        cmb_msg = manager.search_data(
                                            lambda x: x.get('action') in client_wait_reply_actions_check)   # 抓資料至此處理
                                        if cmb_msg:
                                            # print(f'找到資料{action}:{cmb_msg}')
                                            break
                                        else:
                                            # print(f"num_info:{caller_id} 尚未找到資料 {action}，繼續等待...")
                                            pass
                                        await asyncio.sleep(0.001)
                                        # await asyncio.sleep(2)
                                    except Exception as e:
                                        logging.error(
                                            f"handle_json_cmd_with_reply 搜尋資料時發生錯誤: {e}")
                                        continue

                                if cmb_msg:             # Caller, JSON, 收到 CMB Main Server 回覆
                                    try:
                                        manager.remove_matched(
                                            cmb_msg)     # 移除已匹配資料
                                        clients = await client_manager.get_all_clients()
                                        # print(f'handle_json_cmd_with_reply {action} 找到 json 回覆資料:{cmb_msg}')
                                        # 'user_get_num' 需群發
                                        if action == 'user_get_num':
                                            # 發送至取號之 Client, 群發時 'action' 不同
                                            # print(f'發送至Client:{json.dumps(cmb_msg[0])}')
                                            # 回覆
                                            await websocket.send(json.dumps(cmb_msg[0]))
                                            # print(f'不發送至 USER 的裝置:{cmb_msg} ', flush=True)
                                            # logging.info(f"群發訊息至 SOFT cmb-caller 的 caller_id={caller_id}: {cmb_msg}")
                                            # 只發到店家, 2025/08/01 改
                                            await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', (0x2+0x4), websocket)
                                        elif action == 'web_cancel_get_num':
                                            # 發送至取號之 Client
                                            print(
                                                f'\nweb_cancel_get_num 發送至 Client:{json.dumps(cmb_msg[0])}')
                                            # await websocket.send(json.dumps(cmb_msg[0]))    # 回覆
                                            # 發到全部店家
                                            await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', (0x2+0x4))
                                        elif action == 'remove_number':
                                            # 發送至取號之 Client
                                            print(
                                                f'\nremove_number 發送至 Client:{json.dumps(cmb_msg[0])}')
                                            # await websocket.send(json.dumps(cmb_msg[0]))    # 回覆
                                            # 發到全部店家
                                            await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', (0x2+0x4))
                                        else:   # get_num_status & get_num_info, 只回覆不廣播
                                            if action == 'get_num_info':  # 更新caller的號碼
                                                # print(f'設定叫號機 {caller_id}:{cmb_msg[0].get('call_num')}')
                                                # 更新叫號資訊
                                                # await client_manager.update_caller_info(caller_id, cmb_msg[0].get('call_num'))

                                                print(
                                                    f"叫號機 {caller_id} 收到 'get_num_info' call_num={cmb_msg[0].get('call_num')}", flush=True)

                                                # 防止 caller_id 不存在或 caller_num 欄位缺失
                                                caller_num = clients.get(
                                                    caller_id, {}).get('caller_num', -1)

                                                curr_num = cmb_msg[0].get(
                                                    'call_num')

                                                try:
                                                    curr_num = int(curr_num)
                                                except (ValueError, TypeError):
                                                    print(f"call_num 資料格式錯誤：'{curr_num}',{cmb_msg[0]}")
                                                    curr_num = -1

                                                if (curr_num < 0):  #
                                                    # json_data['curr_num'] = 0
                                                    print(
                                                        f"收到_1 curr_num<0 ({curr_num}) 不更新現在叫號值:{caller_num}")
                                                    pass
                                                else:
                                                    print(
                                                        f"OK  {caller_id} curr_num:{caller_num} -> {cmb_msg[0].get('call_num')}")
                                                    # login 會傳回目前號碼 "curr_num"
                                                    await client_manager.update_caller_info(caller_id, cmb_msg[0].get('call_num'))

                                                pass
                                            try:
                                                # 發送至詢問之 Client
                                                # print(f'發送至Client:{json.dumps(cmb_msg[0], ensure_ascii=False)}')
                                                # 回覆
                                                await websocket.send(json.dumps(cmb_msg[0]))
                                            except Exception as e:
                                                logging.info(
                                                    f"handle_json_cmd_with_reply 回覆至 {action} caller 發生錯誤!  error: {e}, {caller_id}: {cmb_msg}")
                                        return
                                    except Exception as e:
                                        logging.error(
                                            f"handle_json_cmd_with_reply 處理回覆資料時發生錯誤: {e}")
                                        continue
                                else:       # 已發送命令但等待回覆愈時.
                                    print(
                                        f"handle_json_cmd_with_reply,{action} 逾時({self.server_timeout}Sec)重送! (嘗試 {attempt+1}/{max_retries})")
                            except Exception as e:
                                logging.error(
                                    f"handle_json_cmd_with_reply,{action} 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}")
                                # traceback.print_exc()
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                continue
            except Exception as e:
                logging.error(f"handle_json_cmd_with_reply 獲取鎖時發生錯誤: {e}")
                await websocket.send("Fail, 003:伺服器忙碌中")
        except Exception as e:
            logging.error(f"handle_json_cmd_with_reply 發生未捕捉錯誤: {e}")
            await websocket.send("Fail, 002:伺服器內部錯誤")

    # Caller, 會等待, CSV
    # get_cmd True -> get
    async def handle_get_num_info(self, caller_id, parts, websocket, get_cmd=False):
        # async with self.ws_device_lock:  # 使用鎖來確保一次只有一個驗證過程
        async with self.ws_device_lock.acquire(f'ws_device_lock CSV get_num_info:{caller_id}'):
            if len(parts) != 2:
                logging.info("無效的 get_num_info 格式!")
                # 至 caller
                await websocket.send("Fail, 006:無效的CMD指令")
                return

            max_retries = 6
            retry_delay = 1

            for attempt in range(max_retries):
                if attempt >= 1:
                    print(
                        f'handle_get_num_info Retry {attempt+1}/{max_retries}')
                send_data = {
                    'action': "get_num_info",         # 動作指令
                    "vendor_id": self.vendor_id,      # 叫號機廠商 id
                    "caller_id": caller_id,          # 叫號機 id
                    "uuid": 'CSV'  # 封包識別碼
                }

                # Try Block added for reconnection logic or error handling
                try:
                    if not self.ws_client:
                        print('handle_get_num_info: ws_client 已斷線!')
                        # 這裡可以嘗試重連 ws_client，或直接跳過
                        pass
                    else:
                        try:
                            # print(f'ws_client.send: {json.dumps(send_data)}')
                            # 至 CMB Main Server
                            await self.ws_client.send(json.dumps(send_data), "handle_get_num_info")    # async def send(
                            # 等待回應
                            start_time = time.time()
                            self.ws_client.cmb_msg = ''

                            cmb_msg = []
                            while not cmb_msg and time.time() - start_time < self.server_timeout:
                                cmb_msg = manager.search_data(
                                    lambda x: x.get('action') == "get_num_info")
                                if cmb_msg:
                                    # print(f'找到資料:{found_data}')
                                    break
                                else:
                                    # print(f"num_info:{caller_id} 尚未找到資料，繼續等待...")
                                    pass
                                await asyncio.sleep(0.001)

                            # print(f'handle_get_num_info 找到資料:{cmb_msg}')
                            manager.remove_matched(cmb_msg)     # 移除已匹配資料
                            # cmb_msg = json.dumps(cmb_msg)
                            if cmb_msg:
                                # response = json.loads(cmb_msg)
                                response = dict(cmb_msg[0])
                                # if self.ws_client.cmb_msg:
                                #     response = json.loads(self.ws_client.cmb_msg)
                                if response.get("result") == "OK":
                                    call_num = response.get("call_num", '')
                                    wait_num = response.get('wait_num', '')
                                    curr_get_num = int(
                                        response.get('curr_num', '0'))
                                    if (wait_num == ''):
                                        current_num = int(await client_manager.get_caller_num(caller_id))
                                        if (current_num < curr_get_num):
                                            wait_num = curr_get_num-current_num
                                        else:
                                            wait_num = curr_get_num

                                    wait_num = int(wait_num)

                                    # 更新叫號資訊
                                    # await client_manager.update_caller_info(caller_id, call_num)
                                    # 至 caller
                                    try:
                                        if get_cmd:     # get
                                            # print(f"get:OK,{caller_id},{call_num},get")
                                            await websocket.send(f"OK,{caller_id},{call_num},get")
                                        else:
                                            # print(f"get_num_info:OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                            await websocket.send(f"OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                        return
                                    except Exception as e:
                                        logging.error(
                                            f"handle_get_num_info 回傳至 Caller 失敗: {e}")
                                        # 可以選擇回傳錯誤訊息或忽略
                                        # await websocket.send("Fail, 999:發送結果失敗")
                                        return
                                    # if get_cmd:
                                    #     # print(f"get:OK,{caller_id},{call_num},get")
                                    #     await websocket.send(f"OK,{caller_id},{call_num},get")
                                    # else:
                                    #     # print(f"get_num_info:OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                    #     await websocket.send(f"OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                    # return
                                else:
                                    # 處理錯誤回應
                                    code = response.get("result").split(
                                        ',')[1].split(':')[0].strip()
                                    msg_map = {
                                        '003': '007:不支援此功能',
                                        '002': '002:無效的CallerID',
                                        '001': '006:無效的CMD指令',
                                        '009': '007:文字錯誤/其它'
                                    }
                                    msg = msg_map.get(code, '001:驗證失敗')
                                    # 至 caller
                                    try:
                                        if get_cmd:
                                            await websocket.send(f"Fail, {msg},get")
                                        else:
                                            await websocket.send(f"Fail, {msg},get_num_info")
                                        return
                                    except Exception as e:
                                        logging.error(
                                            f"handle_get_num_info 回傳至 Caller 失敗: {e}")
                                        # 可以選擇回傳錯誤訊息或忽略
                                        # await websocket.send("Fail, 999:發送結果失敗")
                                        return
                            else:
                                print(
                                    f'handle_get_num_info 逾時({self.server_timeout}Sec)重送! (嘗試 {attempt+1}/{max_retries})')
                        except Exception as e:
                            logging.error(
                                f"handle_get_num_info 傳送至 Server 失敗:(嘗試 {attempt+1}/{max_retries}): {e}")
                            # traceback.print_exc()
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                            continue
                except Exception as e:
                    logging.error(f"handle_get_num_info 外層 Try 失敗: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    continue

            # # 至 caller ???
            # await websocket.send("Fail, 001:不支援此功能,auth")

    async def handle_auth(self, caller_id, parts, websocket):       # Caller CSV
        """處理驗證請求"""
        # login_start = time.time()
        # print(f'handle_auth:{parts} ', end='', flush=True)
        # async with self.ws_device_lock:  # 使用鎖來確保一次只有一個驗證過程
        async with self.ws_device_lock.acquire(f'ws_device_lock CSV auth:{caller_id}'):

            # print(f'{caller_id},處理驗證請求')
            if len(parts) != 3:
                logging.info("無效的驗證格式!")
                await websocket.send("Fail, 004:無效的驗證格式")   # 至 Caller
                return False

            encrypted_password = parts[2]
            max_retries = 6
            retry_delay = 1

            for attempt in range(max_retries):
                if attempt >= 1:
                    print(f'handle_auth Retry {attempt+1}/{max_retries}')
                send_data = {
                    'action': 'login',                  # CSV
                    "vendor_id": self.vendor_id,
                    "caller_id": caller_id,
                    "password": encrypted_password,
                    # "uuid": 'CSV'
                    'uuid': 'CSV_' + hex(id(websocket))
                }

                if self.ws_client:                  # CSV
                    try:
                        # start_time = time.time()
                        ws_type = -1
                        # ASTRO_cmb-caller
                        if (encrypted_password == 'liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='):  # H/W Caller
                            try:
                                print(
                                    f'\n*** H/W CMB Caller:{caller_id} login_C *** ', end='', flush=True)
                                clients = await client_manager.get_all_clients()
                                existing_num = clients.get(
                                    caller_id, {}).get('caller_num', -1)

                                # 嘗試轉換為整數，若失敗則設為 0 並記錄錯誤
                                try:
                                    current_num = int(existing_num)
                                except ValueError:
                                    # print(
                                    #     f"[ERROR] caller_num 轉換失敗，值為: '{existing_num}'，caller_id: {caller_id}")
                                    logging.error(
                                        f"1_轉換客戶端 {caller_id} existing_num={existing_num} 為整數時發生錯誤: {ValueError}")
                                    current_num = -1

                                # 製造一個 CMB Main Server 回傳資訊
                                # json_cmb_msg = (
                                #     f'{{'action':"login","vendor_id":"tawe","caller_id":"{caller_id}",'
                                #     f'"uuid":"Null","caller_name":"{caller_id}_caller","curr_num":"{current_num}",'
                                #     f'"result":"OK"}}'
                                # )

                                # H/W CMB Caller 暫不使用 , !!!@@@
                                # connect_time = 0
                                # if(self.server_connection_monitor.last_connect_time >= self.server_connection_monitor.last_disconnect_time):
                                #     connect_time = time.time() - self.server_connection_monitor.last_connect_time
                                # else:
                                #     connect_time = -(time.time() - self.server_connection_monitor.last_disconnect_time)
                                # if connect_time >= 0 :
                                #     print(f"login 已連線{connect_time}秒(CSVauth)")
                                # else:
                                #     print(f"login 已斷線{-connect_time}秒(CSV auth)")
                                # if connect_time <= -10 :     # 超過時間就不讓連線
                                #     logging.info(f"server 斷線中_2! ({caller_id},CSV auth) ")
                                #     cmb_msg = {             # 設定叫號機
                                #         'action': 'login',                  # CSV
                                #         "vendor_id": self.vendor_id,
                                #         "caller_id": caller_id,
                                #         "password": encrypted_password,
                                #         'uuid': 'CSV_' + hex(id(websocket)),
                                #         'curr_num': current_num,
                                #         'result': 'Fail, 005:disconnected from the center'
                                #     }
                                #     # json_cmb_msg = json.dumps(cmb_msg)
                                #     # manager.add_data(json_cmb_msg)      # 存入預設固定訊息
                                #     await ws_server.ws_client.generate_mock_message(cmb_msg)
                                #     return

                                if (current_num < 0):   #
                                    print(
                                        f"current_num 值錯誤:{current_num}", flush=True)
                                    pass
                                ws_type = 1
                                await login_buffer.add(websocket, ws_type)

                                cmb_msg = {             # 設定叫號機
                                    'action': 'login',                  # CSV
                                    "vendor_id": self.vendor_id,
                                    "caller_id": caller_id,
                                    "password": encrypted_password,
                                    'uuid': 'CSV_' + hex(id(websocket)),
                                    'curr_num': current_num,
                                    'result': 'OK'
                                }
                                # json_cmb_msg = json.dumps(cmb_msg)
                                # manager.add_data(json_cmb_msg)      # 存入預設固定訊息
                                await ws_server.ws_client.generate_mock_message(cmb_msg)
                            except Exception as e:
                                print(f"[EXCEPTION] 處理 CMB Caller 時發生錯誤: {e}")
                        else:       # 至 CMB Main Server
                            # 至 CMB Main Server
                            if encrypted_password == 'user_get_num':
                                print(
                                    f'\n*** user_get_num:{caller_id} login_C *** ', end='', flush=True)
                                ws_type = 4
                            else:
                                print(
                                    f'\n*** SOFT CMB Caller:{caller_id} login_C *** ', end='', flush=True)
                                ws_type = 2

                            await login_buffer.add(websocket, ws_type)
                            await self.ws_client.send(json.dumps(send_data), "login_C")    # async def send(

                        # print(f"\nLogin CSV,{caller_id},{ws_type} 耗時:{time.time() - login_start}")
                        return True

                    except Exception as e:
                        logging.error(
                            f"handle_auth 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}, {caller_id}, ws_client.cmb_msg:{self.ws_client.cmb_msg}")
                        # traceback.print_exc()
                        # print(
                        #     f'self.ws_client.cmb_msg:{self.ws_client.cmb_msg}')
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            await websocket.send("Fail, 001:驗證失敗,auth")      # 至 Caller
            return False

    async def force_close_connection(self, websocket, caller_id, reason):       # Caller
        """強制關閉連線並清理資源"""
        Logger.log("強制關閉連線並清理資源")
        try:
            # 直接關閉 websocket
            # 確保連線關閉
            if not websocket.closed:
                await websocket.close(code=1008, reason=reason)
            # 從客戶端管理器移除
            if caller_id in await client_manager.get_all_clients():
                await client_manager.remove_client(caller_id)
            logging.warning(f"已強制關閉 {caller_id} 連線，原因: {reason}")
        except Exception as e:
            logging.error(f"強制關閉連線時發生錯誤: {e}")
            traceback.print_exc()

    def parse_message(self, message):       # m_cmd 一律變為小寫, CSV
        """解析接收到的訊息"""
        # message = message.lower()
        info = ""
        m_cmd = ""
        try:
            parts = message.split(',')
            parts[1] = parts[1].lower()
            if len(parts) < 2:
                raise ValueError(
                    "訊息格式無效，預期格式為 'caller_id,m_info' 或 'caller_id,m_cmd,m_info'")
            if len(parts) == 2:
                m_info = ''
                if parts[1] == 'get':
                    caller_id, m_cmd = parts
                elif parts[1] == 'ping':
                    caller_id, m_cmd = parts
                elif parts[1] == 'get_num_info':
                    caller_id, m_cmd = parts
                else:       # send
                    caller_id, m_info = parts
                    m_cmd = 'send'

            if len(parts) == 3:
                if parts[1] == 'ping' or parts[1] == 'send' or parts[1] == 'auth' or parts[1] == 'info':
                    caller_id, m_cmd, m_info = parts
                else:       # z0001,121,INFO:.....
                    caller_id, m_info, info = parts
                    m_cmd = 'send'
            # logging.info(f"parse_message return {caller_id}, {m_cmd.lower()}, {m_info}")

            if caller_id is None:
                print(f"傳入資料錯誤:{message} ")
            return caller_id, m_cmd.lower(), m_info
        except Exception as e:
            logging.error(f"parse_message 處理失敗 {e}")
            traceback.print_exc()

    # caller 'send' 命令使用       # Caller
    # SEND CMD, CSV
    async def handle_send_message(self, caller_id, call_num, websocket):
        """處理訊息並生成回應"""
        # call_num = int(call_num)
        try:
            call_num = int(call_num)
        except (ValueError, TypeError):
            call_num = 0  # 或其他預設值
            print(f"call_num 無效: {call_num}")

        max_retries = 6
        retry_delay = 1
        for attempt in range(max_retries):
            if attempt >= 1:
                print(f'handle_send_message Retry {attempt+1}/{max_retries}')
            try:
                # 1. 準備數據
                data = {
                    # "action_0": 'send',     # 備援 action 欄位
                    "vendor_id": self.vendor_id,
                    "caller_id": caller_id,
                    "call_num": call_num,
                    "change": True,
                    "last_update": 0,
                    "uuid": "CSV_SEND"
                    # "uuid": hex(id(websocket))      # Caller 之 websocket ID
                }
                # print(f'C_傳至 CMB Main Server 修補資料:{data} ', end='', flush=True)

                # 2. 檢查WebSocket連接
                if not self.ws_client or not self.ws_client.connect:
                    logging.error("WebSocket連接不可用")
                    await asyncio.sleep(retry_delay)
                    continue

                # 3. 發送消息
                try:
                    # 至 CMB Main Server
                    await self.ws_client.send(json.dumps(data), 'SEND')     # async def send(
                    # logging.info(f"成功發送消息至CMB: caller_id={caller_id}, call_num={call_num}")
                except Exception as send_error:
                    # logging.error(f"發送消息失敗: {send_error}")
                    logging.error(
                        f"handle_send_message 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {send_error}, {call_num}")
                    # raise  # 重新抛出異常以觸發重試機制
                    await asyncio.sleep(retry_delay)
                    continue

                # 4. 等待回應 (帶超時)
                start_time = time.time()
                timeout = 5  # 5秒超時
                response_received = False

                while not response_received and (time.time() - start_time) < timeout:
                    if self.ws_client.cmb_msg:
                        response = f"{self.ws_client.cmb_msg}"
                        self.ws_client.cmb_msg = ''  # 重置消息
                        # logging.info(f"收到CMB回應: {response}")
                        return response

                    await asyncio.sleep(0.1)

                if not response_received:
                    logging.warning("等待回應超時")
                    continue

            except json.JSONDecodeError as json_error:
                logging.error(f"JSON編碼錯誤: {json_error}")

            except websockets.exceptions.ConnectionClosed as conn_error:
                logging.error(f"WebSocket連接已關閉: {conn_error}")
                # 這裡可以添加重新連接邏輯

            except asyncio.TimeoutError:
                logging.warning("操作超時")

            except Exception as e:
                logging.error(
                    f"handle_send_message 處理失敗 (錯誤: {e}), caller_id={caller_id}, call_num={call_num}",
                    exc_info=True
                )

            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            continue

        # 達到最大重試次數後
        logging.error(
            f"達到最大重試次數({max_retries})，放棄處理 caller_id={caller_id}, call_num={call_num}")
        return None


async def periodic_send_frame(ws_server_l):     # 發送例行資料
    global ws_server, periodic_pass
    """定期發送狀態和清理無效連接"""
    await asyncio.sleep(30)
    while True:
        # print("發送例行資料_0: ", end='', flush=True)
        start_time = datetime.now()

        # 清理無效連接
        await client_manager.cleanup()  # 清理長時間無連接的caller記錄

        # 定時清除斷線之Client !!!@@@
        clients = await client_manager.get_all_clients()
        # async with client_manager.lock:     # !!!@@@ **************
        # async with nullcontext():  # 替代鎖，但不實際加鎖
        if True:
            disconnected = set()
            # total_websockets = sum(len(client['connections'])
            #                        for client in clients.values())
            # print(f'定時清除斷線之Client:現有 {total_websockets} 個連線中 Client')
            for caller_id, client_info in clients.items():
                # print(f"Caller ID: {caller_id}")
                # for websocket, ws_type in client_info['connections'].items():
                for websocket, info in client_info['connections'].items():
                    ws_type = info['ws_type']
                    # print(f"  WebSocket: {websocket}, Type: {ws_type}")
                    # print(f"  WebSocket:{ websocket.open }")
                    if not websocket.open:
                        print(f'\n3_discard{websocket}:{caller_id}',
                              end='\n', flush=True)
                        disconnected.add((caller_id, websocket))
            # print("發送例行資料_1: ", end='', flush=True)
            for caller_id, websocket in disconnected:       # 巡查時發現
                print(next((
                    f"\n2_discard: {caller_id},{ws}, 类型: {info['ws_type']}"
                    for ws, info in clients[caller_id]['connections'].items()
                    if ws == websocket
                ), "未找到 websocket"), flush=True)
                await client_manager.remove_connection(caller_id, websocket)
        # print("發送例行資料_2: ", end='', flush=True)
        # 發送狀態更新
        clients = await client_manager.get_all_clients()
        active_client = 0
        connected_client = 0
        # print("發送例行資料_3: ", end='', flush=True)
        print("", flush=True)
        # Logger.log("發送例行資料:")
        # print('發送例行資料:', end='\n', flush=True)

        if ws_server == None or periodic_pass:
            if ws_server == None:
                print(f"#{os.getenv('K_REVISION', 'local')} 發送例行資料:",
                      end=' ', flush=True)
                print(" Websocket Server 早已關閉!\n", flush=True)
            if periodic_pass:
                print(" 略過此次發送!\n", flush=True)
        else:
            print(f"#{os.getenv('K_REVISION', 'local')} 發送例行資料:",
                  end='\n', flush=True)
            print('例行資料 : ', end='', flush=True)
            issue = False
            for caller_id, info in clients.items():
                try:
                    is_connected = bool(info['connections'])

                    # 添加對 disconnect_time 的檢查
                    disconnect_time = info.get('disconnect_time')
                    if disconnect_time is None:
                        is_active = True
                    else:
                        try:
                            time_diff = (datetime.now() -
                                         disconnect_time).total_seconds()
                            is_active = time_diff < 600  # 有效連線(斷線10分鐘內)
                        except TypeError:
                            # 如果 disconnect_time 不是有效的 datetime 對象
                            is_active = True
                            print(f"{caller_id}的disconnect_time格式錯誤  ",
                                  end='', flush=True)

                    if is_connected:
                        connected_client += 1
                    if is_active:
                        active_client += 1

                        def calculate_last_update(is_connected, disconnect_time):
                            if is_connected:
                                return 0
                            if disconnect_time is None:
                                return 1  # 預設值，代表「未知斷線時間」
                            try:
                                time_since_disconnect = datetime.now() - disconnect_time
                                minutes_offline = max(
                                    0, int(time_since_disconnect.total_seconds() / 60))
                                return minutes_offline + 1
                            except TypeError:
                                return 1  # 如果時間格式錯誤，返回預設值
                            # -------------------------------------

                        # 如錯誤或無值則設0 , !!!@@@
                        # caller_num_str = info.get('caller_num', '0')
                        # caller_num_str = info.get('caller_num') or '0'
                        # caller_num_str = info.get('caller_num') or ''
                        # 明確處理 None 情況，但保留 0
                        caller_num = info.get('caller_num')
                        caller_num_str = str(
                            caller_num) if caller_num is not None else ''

                        # 發送更新到CMB主伺服器
                        data = {
                            "vendor_id": "tawe",
                            "caller_id": caller_id,
                            # "call_num": info['caller_num'],
                            "call_num": caller_num_str,
                            "change": not is_connected,
                            "last_update": calculate_last_update(is_connected, info.get('disconnect_time')),
                            # frontend 之 ID
                            "uuid": hex(id(ws_server.ws_client))
                        }

                        # 這裡輸出 - 添加完整的錯誤處理
                        # caller_num_str = info.get('caller_num', '')
                        if not caller_num_str:  # 檢查是否為空字串
                            print(f"{caller_id},空值  ", end='',
                                  flush=True)  #
                            if run_mode == 'Trial':
                                print(f"info:{info}")
                            continue

                        try:
                            caller_num = int(caller_num_str)
                            if caller_num < 0:
                                print(f"{caller_id},資料無效:{caller_num}  ",
                                      end='', flush=True)
                            else:
                                print(
                                    f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]}  ', end='', flush=True)
                                # 至 CMB Main Server
                                await ws_server.ws_client.send(json.dumps(data), 'MINUTE')
                        except (ValueError, TypeError) as num_error:
                            print(
                                f"{caller_id},資料無效:無法轉換為數字 '{caller_num_str}'  ", end='', flush=True)
                            continue

                except Exception as e:
                    # 這裡捕獲其他可能的異常
                    logging.error(f"處理客戶端 {caller_id} 時發生錯誤: {e}")
                    logging.info(f"發送例行資料 傳送至Server失敗:{e}, 10秒後繼續發送例行資料!!!")
                    # 出錯後將 start_time 設為xx秒前
                    start_time = datetime.now() - timedelta(seconds=(60-10))
                    issue = True
                    break   # 離開 for 迴圈

            if not issue:
                # print("發送例行資料_6: ",end='', flush=True)
                print("", flush=True)
                # 記錄狀態
                total_websockets = sum(len(client.get('connections', {}))
                                       for client in clients.values())
                Logger.log(
                    f"總共有 {len(clients)} 個紀錄中 ID, "
                    f"{active_client} 個有效的 ID, "
                    f"{connected_client} 個連線中 ID, "
                    f"{total_websockets} 個連線中 Client, "
                    f"{manager.count_data()} 個 Server 回覆暫存資料"
                )

                # 使用字典來動態統計各類型數量，避免多個獨立變數
                type_counts = {1: 0, 2: 0, 4: 0, 8: 0}

                for caller_id, client_info in clients.items():
                    connections = client_info.get('connections', {})
                    for websocket, info in connections.items():
                        ws_type = info.get('ws_type', 0)
                        # 使用位元運算檢查所有可能的類型
                        for type_flag in type_counts.keys():
                            if ws_type & type_flag:
                                type_counts[type_flag] += 1

                # 最終輸出統計結果
                for type_flag, count in type_counts.items():
                    print(f"Type_{type_flag}:{count} ", end='', flush=True)
                # print('', flush=True)
                # print('-------------------', flush=True)
                print('\n' + '-' * 40, flush=True)

        # 確保每60秒執行一次
        execution_time = (datetime.now() - start_time).total_seconds()
        await asyncio.sleep(max(60 - execution_time, 0))


os_name = ''


def get_platform_config():
    global os_name
    """判斷 platform 並返回相應配置"""
    os_name = platform.system()
    PORT = 8765
    if os_name == 'Windows':
        PORT = 38000
        # return PORT, "ws://localhost:8088", 'Windows'      # Local WIndows PC
        return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Windows'  # CMB Trying
        # return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Windows'  # CMB Live
        # return PORT, "ws://35.185.131.62:4000", 'Windows'  # Jando VM
        # return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app_/", 'Windows'  # CMB Trying  ***** 故意設錯!

    if os_name == 'Linux':
        if 'K_SERVICE' in os.environ:                                                              # Cloud RUN
            PORT = int(os.environ.get("PORT", 8080))
            return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Cloud_Run'  # CMB Trying
            # return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Cloud_Run'  # CMB Live
        try:
            response = requests.get(
                'http://metadata.google.internal/computeMetadata/v1/',
                timeout=15,
                headers={'Metadata-Flavor': 'Google'}
            )
            if response.status_code == 200:
                return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Compute_Engine'    # CMB Trying
                # return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Compute_Engine'    # CMB Live
        except:
            pass
        return PORT, "ws://localhost:8088", 'Linux'
    return PORT, "ws://localhost:8088", 'Unknown'


async def main():
    global ws_server, ConnectionBlocker, start_timestamp, run_mode
    """主程式入口"""
    try:
        # # 設定台北時區
        # taipei_tz = pytz.timezone('Asia/Taipei')
        # # 取得目前時間（台北時間）
        # taipei_time = datetime.now(taipei_tz)
        # print("台北時間：", taipei_time.strftime('%Y-%m-%d %H:%M:%S'))

        # （選擇性）設定程式內預設時區為台北
        # 注意：這不會改變作業系統的時區，只影響程式邏輯
        # datetime.now(ZoneInfo("Asia/Taipei"))
        # print("預設為台北時間：", now.strftime("%Y-%m-%d %H:%M:%S"))

        # 列出所有環境變數
        # print("\n列出所有環境變數")
        # for key, value in os.environ.items():
        #     print(f"{key} = {value}")

        # print(".\n", flush=True)
        # print(".\n", flush=True)
        # await asyncio.sleep(0.1)
        logging.info(
            f"***** #{os.getenv('K_REVISION', 'local')},{start_timestamp}, cmb-caller-frontend Ver.{VER} 開始執行! *****")
        # print(".\n", flush=True)
        # print(".\n", flush=True)

        port, ws_url, platform_name = get_platform_config()
        if platform_name == 'Cloud_Run':
            # 啟動 Pub/Sub 訂閱（非阻塞）
            sub_task = asyncio.create_task(delayed_subscribe())

            CREDENTIALS, PROJECT_ID = default()
            print(
                f"CREDENTIALS: {CREDENTIALS}, Project ID: {PROJECT_ID}", flush=True)
            if PROJECT_ID == 'callme-398802':                                       # CallMe Beta
                ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"  # 強制設定至 CMB Live
                run_mode = 'Live'
                ConnectionBlocker = False
                logging.info("CMB Live Server!")
            else:
                run_mode = 'Trial'
                logging.info("CMB Trial Server!")

        send_result = LineNotifier.send_event_message(
            "event_1", status=f"  ====== {run_mode} Version! ======\n#{os.getenv('K_REVISION', 'local')},{start_timestamp}, cmb-caller-frontend Ver.{VER} 開始執行!")

        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')
        # 初始化並啟動 WebSocket Client, 連接至 CMB Main Server
        ws_client = WebSocketClient(ws_url)
        # asyncio.create_task(ws_client.connect())

        # 背景執行 run()
        asyncio.create_task(ws_client.run())

        # try:
        #     await ws_client.run()
        # except KeyboardInterrupt:
        #     logging.info("收到中斷信號，正在關閉...")
        # except Exception as e:
        #     logging.error(f"應用程式發生未預期錯誤: {e}")
        #     sys.exit(1)

        # 初始化並啟動 WebSocket Server, 對應 Caller
        ws_server = WebSocketServer('0.0.0.0', port)
        ws_server.ws_client = ws_client
        ws_server_task = asyncio.create_task(
            ws_server.start())     # Webserver 啟動

        # 每分鐘例行發送現有之 caller_id 資訊
        periodic_task = asyncio.create_task(periodic_send_frame(ws_server))

        interval_seconds = 2     # 每隔 interval_seconds 秒執行一次
        max_cycles = 15          # 最多執行 max_cycles 次循環
        messages_per_cycle = 1   # 每次循環執行 messages_per_cycle 次
        cycle_count = 0
        last_exec_time = time.time() - interval_seconds  # 確保一開始就能執行一次

        # # 啟動 Flask（在背景執行）
        # if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        #     threading.Thread(target=lambda: app.run(
        #         host='0.0.0.0',
        #         port=8081,  # 使用不同的端口
        #         debug=False,
        #         use_reloader=False
        #     )).start()
        #     print("啟動 Flask!", flush=True)

        # 保持主執行緒運行
        while True:
            current_time = time.time()

            if ConnectionBlocker and (current_time - start_timestamp) >= (5.5*60):     # 5 分鐘
                ConnectionBlocker = False

            # 每 interval_seconds 秒執行一次，最多 max_cycles 次
            if cycle_count < max_cycles and (current_time - last_exec_time >= interval_seconds):
                if platform_name == 'Cloud_Run':
                    for i in range(1, messages_per_cycle + 1):
                        broadcast_message(
                            'STOP_SERVER',
                            f'新 Server instance 啟動通知_{messages_per_cycle * cycle_count + i}!'
                        )
                        await asyncio.sleep(0.5)
                cycle_count += 1
                last_exec_time = current_time

            await asyncio.sleep(1)  # 保持主迴圈節奏不變

    except Exception as e:
        logging.error(f"致命錯誤: {e}")
        traceback.print_exc()
    finally:
        logging.error("cmb-caller-frontend 結束")
        await ws_server.stop()  # 停止Server
        await ws_client.close()  # 關閉 WebSocket 連接
        ws_server_task.cancel()  # 取消Server任務
        periodic_task.cancel()  # 取消定時任務


if __name__ == '__main__':
    # Set up logger to log to both console and file
    # setup_logger(log_to_console=True, log_to_file=True, log_level=logging.DEBUG)
    setup_logger(log_to_console=True, log_to_file=True, log_level=logging.INFO)
    asyncio.run(main())
