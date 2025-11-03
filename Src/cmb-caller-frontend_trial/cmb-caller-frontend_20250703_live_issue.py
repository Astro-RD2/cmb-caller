
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
2025/04/16  Roy Ching    加入叫號資料更新通知 (update)功能.
2025/04/16  Roy Ching    修復斷線重連後叫號資料更新通知失效問題(add_connection) (2025/04/16 取消).
2025/04/16  Roy Ching    斷線重連需要衝新認證(auth).
2025/04/16  Roy Ching    加入 'get_num_info' 及 'info' 呼叫支援
2025/04/17  Roy Ching    修復斷線重連號碼歸零問題.
2025/04/17  Roy Ching    支援 get_num_info 新舊規格
2025/04/18  Roy Ching    handle_auth 加 auth_lock:
2025/04/22  Roy Ching    斷線時間 0~9 改 1~10
2025/04/25  Roy Ching    加入 LockWithNotification & TracedLock
2025/04/28  Roy Ching    修正 CMB Caller 登入錯誤問題
2025/05/14  Roy Ching    auth_lock 改為 ws_cmd_lock
2025/05/14  Roy Ching    增加 new_get_num 命令.
2025/05/14  Roy Ching    auth 命令 增加 "user_get_num" 登入, 增加 wait_time_avg、new_get_num、get_num_switch及user_get_num 命令.
2025/05/14  Roy Ching    get_num_switch 增加主動通知功能, user_get_num 增加 "user_id" 欄位, 增加 get_num_status 命令.
2025/05/14  Roy Ching    改為主動通知 user_get_num
2025/05/14  Roy Ching    "user_get_num",限定權限,user_get_num(Server 不主動通知)、get_num_switch(僅接收),且無 send、new_get_num  功能.
2025/05/14  Roy Ching    json send 資料去除 []
2025/05/14  Roy Ching    'update' 不傳送給發送端
2025/06/06  Roy Ching    加入login(auth) json 執行
2025/06/06  Roy Ching    加入get_num_info json  執行
2025/06/06  Roy Ching    CMB Main 資料未 remove_matched 錯誤處理
2025/06/06  Roy Ching    加入 CMB Main 資料 及 登入類別 顯示
2025/06/12  Roy Ching    修復 user_get_num 未回覆 get_num_item_id 之問題.
2025/06/20  Roy Ching    handle_send_message retry 加入 delay.
2025/06/24  Roy Ching    傳入 Maim Server 的資料皆加入 Retrt 3次 功能.
2025/06/24  Roy Ching    新加入之 ID 會查詢 Main Server 取得最後的叫號號碼.
2025/06/24  Roy Ching    加入 RESET 叫號號碼的功能.
2025/07/02  Roy Ching    加入踢除上一版本的功能.
2025/07/02  Roy Ching    WiFi 傳送 Caller 斷線廣播.
2025/07/02  Roy Ching    加入 login 提供 hardware 參數.
'''

VER = "20250702"


from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta
import platform
import os
import requests
import json
import asyncio
import websockets
import logging
from logging.handlers import RotatingFileHandler
from google.auth import default
import traceback
from flask import Flask
import threading
import functools

try:
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None
    print("警告：無法匯入 google.cloud.pubsub_v1，請確認是否已安裝相關套件。")


import nest_asyncio
nest_asyncio.apply()



# 讓所有 print 都即時輸出
print = functools.partial(print, flush=True)

import uuid
instance_uuid = str(uuid.uuid4())

app = Flask(__name__)

# Caller 傳入 json file 需等待 Server 回覆時使用, login 另外處理.
client_wait_reply_actions_to_check = {
    "user_get_num", "get_num_status", "get_num_info"}
# client_wait_reply_actions_to_check = {"get_num_status"}

# servsr_transmit_servsr_replay_active_actions_to_check = {"wait_time_avg", "new_get_num", "get_num_switch", "user_get_num"}       # async def listen(self):     # CMB Main Server
# servsr_replay_active_actions_to_check = {"wait_time_avg", "new_get_num", "get_num_switch"}       # send 至 CMB Main 不等待, 於 listen CMB Main Server 時直接轉發
# 2025/06/20 去掉 "wait_time_avg"
# listen Main Server 回覆 或 主動通知, 直接轉發 或 處理後續.
servsr_replay_active_actions_to_check = {
    "new_get_num", "get_num_switch", "reset_caller"}


# 定義 Caller CSV 需要處理的指令
CALLER_CSV_COMMANDS_TO_PROCESS = {'send', 'auth', 'get_num_info', 'info'}





# 全局變數
if pubsub_v1 != None:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id'), 'cross-instance-comms')
subscriber = None
is_subscribed = False
streaming_pull_future = None
ws_server = None

# import os
# import asyncio
# import json
# import logging
# from google.cloud import pubsub_v1

# subscriber = None
# is_subscribed = False
# streaming_pull_future = None
# ws_server = None
# topic_path = None  # 你必須在外部先正確設定好 topic_path



async def delayed_subscribe():
    """延遲訂閱 Pub/Sub 並處理訊息，包含完整錯誤處理和資源清理"""
    global subscriber, is_subscribed, streaming_pull_future, ws_server, topic_path

    revision = os.getenv('K_REVISION', 'local')
    try:
        print(f"#{revision} [啟動] 等待90秒後開始訂閱...", flush=True)
        await asyncio.sleep(90)

        if subscriber is None:
            subscriber = pubsub_v1.SubscriberClient()
            print(f"#{revision} [訂閱] SubscriberClient 初始化完成", flush=True)

        subscription_name = f"version-sub-{revision}-{os.getenv('CLOUD_RUN_EXECUTION', 'local')}"
        subscription_path = subscriber.subscription_path(
            os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id'),
            subscription_name
        )

        try:
            subscriber.create_subscription(
                name=subscription_path,
                topic=topic_path,
                ack_deadline_seconds=30
            )
            print(f"#{revision} [訂閱] 訂閱建立成功: {subscription_path}", flush=True)
        except Exception as e:
            if "already exists" in str(e):
                print(f"#{revision} [訂閱] 使用現有訂閱: {subscription_path}", flush=True)
            else:
                raise

        shutdown_event = asyncio.Event()

        def callback(message):
            try:
                data = json.loads(message.data.decode('utf-8'))
                sender_revision = data.get('sender', 'unknown').split('/')[0]
                # print(f"0#{revision} [訊息] 來自 {data.get('sender')}: {message}", flush=True)
                print(f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')}, {data.get('message')}", flush=True)
                print(f"#{revision} sender_revision,revision:{sender_revision},{revision}", flush=True)

                if sender_revision == revision:
                    print(f"#{revision} [過濾] 忽略自身訊息", flush=True)
                    # message.ack()         # !!!@@@ 保留此訊息給其它 Instance 使用
                    return

                if data.get('content') == 'STOP_SERVER':
                    print(f"#{revision} [指令] 收到停止服務請求", flush=True)
                    shutdown_event.set()
                    message.ack()
                    return

                # print(f"#{revision} [訊息] 來自 {data.get('sender')}: {data.get('content')}", flush=True)
                message.ack()
            except Exception as e:
                print(f"#{revision} [錯誤] 處理訊息失敗: {e}", flush=True)
                message.nack()

        print(f"#{revision} [訂閱] 開始監聽訊息...", flush=True)
        streaming_pull_future = subscriber.subscribe(
            subscription_path,
            callback=callback,
            await_callbacks_on_shutdown=True
        )
        is_subscribed = True

        await shutdown_event.wait()
        print(f"#{revision} [訂閱] 收到停止訊號，開始清理...", flush=True)

    except Exception as e:
        print(f"#{revision} [錯誤] 訂閱流程異常: {type(e).__name__}: {e}", flush=True)
        logging.exception(e)

    finally:
        print(f"#{revision} 安全釋放資源", flush=True)

        if streaming_pull_future and not streaming_pull_future.done():
            print(f"#{revision} [清理] 取消訂閱任務", flush=True)
            streaming_pull_future.cancel()

        if subscriber is not None:
            print(f"#{revision} [清理] 關閉 SubscriberClient", flush=True)
            try:
                # await subscriber.close()    # 
                subscriber.close()    # !!!@@@
            except Exception as e:
                print(f"#{revision} [清理] 關閉 SubscriberClient 錯誤: {e}", flush=True)
            subscriber = None

        if ws_server is not None:
            print(f"#{revision} [清理] 停止 WebSocket 服務", flush=True)
            try:
                await ws_server.stop()
            except Exception as e:
                print(f"#{revision} [清理] 停止 WebSocket 服務錯誤: {e}", flush=True)
            ws_server = None

        print(f"#{revision} 訂閱 & Websocket 服務已完全停止", flush=True)

def broadcast_message(content,message):
    """廣播訊息到所有實例"""
    message = {
        "content": content,
        "message": message,
        "sender": f"{os.getenv('K_REVISION', 'local')}/{instance_uuid}/{os.getenv('CLOUD_RUN_EXECUTION', 'local')}",
        "timestamp": time.time()
    }

    future = publisher.publish(
        topic_path,
        json.dumps(message).encode('utf-8')
    )
    print(
        f"#{os.getenv('K_REVISION', 'local')} [廣播] 已發送訊息:{content},{message},ID:{future.result()}")


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "websocket": "running" if ws_server else "stopped"}

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




@app.route('/', methods=['GET', 'POST'])
def my_help():
    routes = """
    ('/help', methods=['GET', 'POST'])
    ('/', methods=['GET', 'POST'])
    ('/complete_shop_list', methods=['GET', 'POST'])    # 重建 shop_list
    ('/garbage_collection', methods=['GET', 'POST'])
    ('/generate_shop_list', methods=['GET', 'POST'])    # 重建 shop_list
    ('/hello', methods=['GET', 'POST'])
    ('/info', methods=['GET', 'POST'])
    ('/last_updated_time', methods=['GET', 'POST'])
    ('/no_sleep', methods=['GET', 'POST'])
    ('/restart', methods=['GET', 'POST'])
    ('/stay_awake', methods=['GET', 'POST'])
    ('/system_info', methods=['GET', 'POST'])
    ('/update_json_file', methods=['GET', 'POST'])      # 強制更新 shop_list
    ('/update_shop_list', methods=['GET', 'POST'])      # 每分鐘檢查 eMail
    """
    return "<pre>" + routes.replace('\n', '<br>') + "</pre>"




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


class LockWithNotification:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._waiting_messages: Dict[int, Dict[str, Any]] = {}
        self._lock_stats = {
            'total_acquires': 0,
            'total_wait_time': 0.0,
            'max_wait_time': 0.0,
            'immediate_acquires': 0
        }
        self._last_acquired_time = None

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

        try:
            # 嘗試非阻塞獲取鎖
            if not self._lock.locked():
                await self._lock.acquire()
                acquired = True
                self._lock_stats['immediate_acquires'] += 1
                self._lock_stats['total_acquires'] += 1
                self._last_acquired_time = time.monotonic()
                debug_info['status'] = 'immediate_acquire'
                # print(f"🔓 [立即獲取] {context or '無上下文'} ", flush=True)
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

                    # print(f"🔓 [獲取成功] {context or '無上下文'} 等待時間: {wait_time:.3f}秒", flush=True)
                except asyncio.TimeoutError:
                    current_time = time.monotonic()
                    wait_time = current_time - start_time
                    debug_info['wait_time'] = wait_time

                    # 定期打印等待狀態
                    if current_time - last_print_time >= print_interval:
                        last_print_time = current_time
                        waiting_tasks = len(self._waiting_messages)
                        print(
                            f"⏳ [等待中] {context or '無上下文'} "
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
            # print(f"🔓 [釋放鎖定] {context or '手動操作'} (持有時間: {hold_time:.3f}秒)", flush=True)
            return True
        # print(f"⚠️ 釋放失敗: {context or '手動操作'} 鎖定未被持有", flush=True)
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


class TracedLock:
    """追蹤等待時間的鎖"""

    def __init__(self, name="unnamed_lock"):
        self._lock = asyncio.Lock()
        self.name = name

    async def __aenter__(self):
        task = asyncio.current_task()
        task_id = id(task)
        start_wait = time.time()

        # 立即檢查鎖狀態
        if self._lock.locked():
            wait_start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"等待 {self.name} 鎖... [開始時間: {wait_start_time}]", end='', flush=True)

            # 實際獲取鎖
            await self._lock.acquire()

            # 計算等待時間並顯示
            wait_duration = time.time() - start_wait
            wait_end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"取得 {self.name} 鎖，等待了 {wait_duration:.3f} 秒 [結束時間: {wait_end_time}]", end='', flush=True)
        else:
            # 沒有等待，直接獲取鎖
            await self._lock.acquire()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()

class PreciseTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            if "%F" in datefmt:  # 自訂 %F 表示秒數帶2位小數
                s = datetime.fromtimestamp(record.created).strftime("%S.%f")[:8]  # 取 .xx
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


class ClientManager:        # 管理 caller 連線
    global ws_server

    def __init__(self):
        self.clients = {}
        # self.lock = asyncio.Lock()
        self.lock = TracedLock("ClM_lock")

    async def remove_client(self, caller_id):
        async with self.lock:
            if caller_id in self.clients:
                del self.clients[caller_id]

    async def add_connection(self, caller_id, websocket, ws_type):
        """添加一個新的WebSocket連接到指定caller_id"""

        # clients = await client_manager.get_all_clients()
        clients = await self.get_all_clients()
        # print(f'add_connection clients:{clients}')
        # 取得 caller_id 的 caller_num，如果不存在則預設 0，並確保是 int
        existing_num = clients.get(caller_id, {}).get(
            'caller_num', 0)      # 無效，由 get_num_info 取代
        caller_num = int(existing_num)  # 確保是 int
        # print(f'add_connection caller_num:{caller_num}')

        new_add = False
        async with self.lock:
            if caller_id not in self.clients:   # !!!@@@ 加入一新的 caller_id
                new_add = True
                print('加入一新的 caller_id')
                self.clients[caller_id] = {
                    # 'connections': set(),
                    'connections': {},    # 原本是 set()，現在改成 dict
                    # 'caller_num': 0,
                    'caller_num': caller_num,
                    'caller_name': '',
                    'connect_time': datetime.now(),
                    'disconnect_time': None
                }

            self.clients[caller_id]['connections'][websocket] = ws_type
            self.clients[caller_id]['disconnect_time'] = None

        if new_add:
            print('add_connection: get_num_info frontend', flush=True)
            data = {             # 設定叫號機
                "action": "get_num_info",
                "vendor_id": "tawe",
                "caller_id": caller_id,
                "user_id": "_frontend",
                "uuid": hex(id(websocket))
            }
            await ws_server.process_message(json.dumps(data), websocket, is_new_connection=False)

    async def remove_connection(self, caller_id, websocket):
        """從指定caller_id移除一個WebSocket連接"""
        async with self.lock:
            if caller_id in self.clients:
                if caller_id in self.clients and websocket in self.clients[caller_id]['connections']:
                    del self.clients[caller_id]['connections'][websocket]
                    # print(f'0_discard({websocket}):{caller_id}',
                    #       end='\n', flush=True)
                else:
                    logging.warning(
                        f"0_discard WebSocket not found for caller_id {caller_id}")

                # 如果沒有連接了，記錄斷開時間
                if not self.clients[caller_id]['connections']:
                    print(f'記錄斷開時間:{caller_id}', end='\n', flush=True)
                    self.clients[caller_id]['disconnect_time'] = datetime.now()

    async def update_caller_info(self, caller_id, caller_num=None, caller_name=None):
        """更新caller的號碼或名稱"""
        async with self.lock:
            if caller_id in self.clients:
                if caller_num is not None:
                    self.clients[caller_id]['caller_num'] = caller_num
                    # print(
                    #     f"update_caller_info set clients[{caller_id}][{caller_num}] = {caller_num}")

    # ws_type_enable 1:CMB Caller, 2:SOFT CMB Caller, 4:user_get_num, 8:Setup WiFi
    async def notify_clients(self, caller_id, message, ws_type_enable, ws_bypass=None):
        """通知指定caller_id的所有連接"""
        # print(f'notify_clients:{caller_id},{message},{ws_type_enable},{ws_bypass} ', end='', flush=True)
        # print(f'notify_clients:{caller_id},{message},{ws_type_enable}... ', end='', flush=True)
        async with self.lock:
            # print('na ', end='', flush=True)
            if caller_id in self.clients:   # 如未連線則不廣播
                # print('nb ', end='', flush=True)
                disconnected = set()
                # print(f'clients:{self.clients}')

                notify_count = 0
                for websocket, ws_type in self.clients[caller_id]['connections'].items():
                    # print('nc ', end='', flush=True)
                    try:
                        if websocket.open:
                            if ws_type & ws_type_enable:
                                if websocket != ws_bypass:
                                    # print('nd ', end='', flush=True)
                                    # EX: v0005,696,update
                                    # logging.info(f"通知客戶端:{message}")
                                    notify_count += 1
                                    # 至 caller
                                    await websocket.send(message)
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
                        logging.error(f"通知Client失敗: {e}")
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
                #         print(f'2_discard:{ws}:{caller_id}',
                #               end='\n', flush=True)
                #         # print(f'2_discard:{ws}:{caller_id}    *** BYPASS ***', end='\n', flush=True)
                #     else:
                #         logging.warning(
                #             f"2_discard:{ws} not found for caller_id {caller_id}")

    async def get_caller_num(self, caller_id):
        """獲取指定caller_id的當前號碼"""
        async with self.lock:
            # print(
            #     f"get_caller_num:{caller_id},{self.clients[caller_id]['caller_num']}", end='\n', flush=True)
            if caller_id in self.clients:
                return self.clients[caller_id]['caller_num']
            return 0

    async def cleanup(self):
        """清理長時間無連接的caller記錄"""
        async with self.lock:
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
        async with self.lock:
            return {k: v for k, v in sorted(self.clients.items())}


client_manager = ClientManager()

# from threading import Lock
# class JSONMemoryManager_new:
#     def __init__(self, max_capacity=100):
#         if not isinstance(max_capacity, int) or max_capacity <= 0:
#             raise ValueError("max_capacity 必須是正整數")

#         self.data = {"records": []}
#         self.max_capacity = max_capacity
#         self.lock = Lock()  # 用於執行緒安全

#     def add_data(self, new_record):
#         try:
#             with self.lock:  # 確保執行緒安全
#                 new_record_1 = json.loads(new_record)
#                 self.data["records"].append(new_record_1)

#                 # 如果超過最大容量，移除最舊的資料
#                 if len(self.data["records"]) > self.max_capacity:
#                     to_remove = self.data["records"][0]
#                     logging.info(f"即將移除最舊資料: {to_remove}")
#                     self.data["records"].pop(0)

#         except json.JSONDecodeError:
#             logging.error("加入資料失敗：不是合法的 JSON 格式")
#             raise  # 可以選擇重新拋出異常或處理

#     def count_data(self):
#         with self.lock:
#             return len(self.data["records"])

#     def search_data(self, condition):
#         """根據條件搜索資料"""
#         with self.lock:
#             return [record for record in self.data["records"] if condition(record)]

#     def remove_matched(self, matched):
#         """自動整理剩餘資料"""
#         with self.lock:
#             # 假設 matched 中的每個記錄都有唯一的 'id' 欄位
#             matched_ids = {record.get('id') for record in matched}
#             self.data["records"] = [
#                 record for record in self.data["records"]
#                 if record.get('id') not in matched_ids
#             ]

#     def clear_all(self):
#         """清空所有資料"""
#         with self.lock:
#             self.data["records"].clear()


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


# manager = JSONMemoryManager()
manager = JSONMemoryManager(max_capacity=5)    # 限制最多 xx 筆資料

# 連結 CMB Main Server


class WebSocketClient:
    def __init__(self, ws_url):     # CMB Main Server
        """初始化 WebSocket Client"""
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws = None  # CMB Main Server
        self.retry_delay = 5
        # self.send_lock = asyncio.Lock()
        self.send_lock = TracedLock("send_lock")
        print("初始化 WebSocket Client 完成!")

    async def connect(self):     # CMB Main Server
        while True:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=30,  # 從 15 秒增加到 30 秒
                    ping_timeout=10,   # 從 5 秒增加到 10 秒
                ) as ws:

                    self.ws = ws
                    self.retry_delay = 1
                    logging.info(f"已連接到 CMB Main Server {self.ws_url}")

                    # 使用重試機制發送連接數據
                    max_retries = 3
                    retry_delay = 3
                    for attempt in range(max_retries):
                        if attempt >= 1:
                            logging.info(
                                f'傳送 source Retry {attempt+1}/{max_retries}')
                        if self.ws:
                            try:
                                connect_data = {
                                    "source": "tawe"
                                }
                                # 至 Main Server , 連線時要傳
                                await self.ws.send(json.dumps(connect_data))
                                break  # 發送成功則跳出重試循環
                            except Exception as e:
                                logging.error(
                                    f"傳送 source 傳送至Server失敗 (嘗試 {attempt+1}/{max_retries}): {e}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                continue

                    await self.listen()
                    await asyncio.sleep(self.retry_delay)    # !!!@@@

            except websockets.exceptions.ConnectionClosed as e:
                logging.error(
                    f"CMB Main Server 連接關閉，代碼: {e.code}, 原因: '{e.reason}'")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)

            except Exception as e:
                logging.error(f"CMB Main Server 未知錯誤: {e}")
                await asyncio.sleep(self.retry_delay)

    async def process_reset(self, input_data):      # 將 Caller 叫號號碼歸零
        # 判斷是單一還是全部
        data = json.loads(input_data)
        new_num = 0

        if data["caller_id"] != "all":
            # 單一 - 直接印出 caller_id
            # print(data["caller_id"], flush=True)
            caller_id = data["caller_id"]
            print(f'reset caller_id: {caller_id}')
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
                    await client_manager.update_caller_info(caller_id, new_num)
                    # 傳送給全部
                    await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff)

    async def listen(self):     # CMB Main Server
        """處理接收到的訊息"""
        try:
            async for message in self.ws:
                try:
                    # logging.info(f"CMB接收: {message}")
                    if not is_json(message):
                        logging.warning(f"收到非 JSON 訊息，略過: {message}")
                        continue

                    self.cmb_msg = message  # 儲存原始訊息
                    manager.add_data(message)

                    # 優先找出符合直接廣播的 action 的資料
                    cmb_msg = manager.search_data(
                        lambda x: x.get("action") in servsr_replay_active_actions_to_check)

                    # 若找不到符合直接廣播的 action 的資料，嘗試找 wait_time_avg, ( *** send 回覆 ***)
                    if not cmb_msg and not manager.search_data(lambda x: "action" in x):
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

                    if cmb_msg:             # CMB Main Server
                        # Logger.log(f"收到 JSON 訊息: {message}")
                        # print(f'2_cmb_msg:{cmb_msg}')
                        manager.remove_matched(cmb_msg)
                        caller_id = cmb_msg[0].get('caller_id', '')

                        if not caller_id and cmb_msg[0]["action"] != 'reset_caller':
                            logging.error(f"回覆資料錯誤，缺少 caller_id: {cmb_msg}")
                            continue

                        # CMB Main Server
                        # 只群發至店家
                        if "action" in cmb_msg[0] and cmb_msg[0]["action"] == 'new_get_num':
                            # logging.info(f"群發訊息至 SOFT cmb-caller 的 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', 0x2)
                        elif "action" in cmb_msg[0] and cmb_msg[0]["action"] == 'reset_caller':
                            logging.info(
                                f"收到 reset_caller 訊息: {json.dumps(cmb_msg)}")
                            await self.process_reset(json.dumps(cmb_msg[0]))
                        # 群發至全部
                        elif "action" in cmb_msg[0] and cmb_msg[0]["action"] == 'get_num_switch':
                            # logging.info(f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', 0xff)
                        else:   # *** 'send' *** , 群發至全部
                            # logging.info(f"群發訊息至 caller_id={caller_id}: {json.dumps(cmb_msg)}")
                            # await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', 0xff)
                            # await websocket.send(f"{json.dumps(cmb_msg[0])}")
                            pass

                    else:
                        # Logger.log(f"收到 JSON 訊息:{json.loads(message)['action']} 未處理!!!!!, {json.loads(message)}" )
                        # Logger.log(f"收到 JSON 訊息:{json.loads(message)['action']} 廣播未處理." )
                        pass

                except Exception as inner_e:
                    logging.error(
                        f"處理單一訊息時發生錯誤: {inner_e}\n訊息內容: {message}", exc_info=True)
                    continue  # 明確表示繼續下一輪循環

        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"CMB Main Server 連接中斷: {e}")
            await asyncio.sleep(1)
            # 這裡可以選擇重新連接或退出
            raise  # 如果是連接問題，可能需要重新建立連接

        except Exception as e:
            logging.error(f"CMB Main Server 發生未預期錯誤: {e}", exc_info=True)
            await asyncio.sleep(1)
            # 對於其他未預期錯誤，可以選擇繼續運行
            # 移除 raise 以繼續執行
            # raise e

    async def send(self, message):      # CMB 主伺服器
        """發送訊息"""
        async with self.send_lock:
            try:
                # Logger.log(f"發送訊息至 CMB {message}")
                if self.ws:
                    await self.ws.send(message)         # 至 Main Server
            except Exception as e:
                Logger.log(f"[ws.send] 傳送至Server失敗 {message}, {str(e)}")
                raise  # 向上拋出,異常則保留

    async def close(self):     # CMB Main Server
        """關閉 WebSocket 連接"""
        if self.ws:
            await self.ws.close()
            self.ws = None


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


class WebSocketServer:
    def __init__(self, host, port):             # Caller
        """初始化 WebSocket Server"""
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None   # 連結 CMB Main Server
        self.server = None      # 連結 Caller
        self.last_num = 0
        # self.ws_type = -1
        self.server_timeout = 5
        self.ws_cmd_lock = LockWithNotification()

    async def start(self):                      # Caller
        """啟動Server"""
        self.server = await websockets.serve(   # !!!@@@@
            self.handler,
            self.host,
            self.port,
            # ping_interval=30,      # xx 秒，減少資源消耗
            # ping_timeout=10,       # xx 秒，給予寬裕的回應時間
            ping_interval=5,      # xx 秒，減少資源消耗
            ping_timeout=5,       # xx 秒，給予寬裕的回應時間
            max_size=4096,        # 限制訊息大小，避免記憶體問題
            compression=None       # ESP32 不需要壓縮，可提高效能
        )
        logging.info(
            f"cmb-caller-frontend WebSocket Server 已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()  # 保持Server運行

    async def stop(self):                           # Caller
        """停止Server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print(
                f"\n***** #{os.getenv('K_REVISION', 'local')} Websocket Server 已關閉!!! *****\n", flush=True)

    async def handler(self, websocket, path):       # Caller
        """處理新Client連接"""
        new_connect = True
        # response_auth = False
        caller_id = None
        remove_socket = False

        try:
            async for message in websocket:
                try:
                    # print(f'handler:{message}', flush=True)
                    await self.process_message(message, websocket, new_connect)
                    new_connect = False  # 第一次處理後設為False
                except Exception as e:
                    logging.error(f"處理訊息時發生錯誤: {e}", exc_info=True)
                    await websocket.send(json.dumps({"result": "Fail, 005:處理訊息錯誤"}))

        except websockets.exceptions.ConnectionClosed as e:
            def get_caller_id_by_websocket(websocket, clients):
                for caller_id, info in clients.items():
                    if websocket in info.get('connections', {}):
                        return caller_id
                return None
            clients = await client_manager.get_all_clients()    # !!!@@@
            caller_id = get_caller_id_by_websocket(websocket, clients)
            caller_type = clients['z0002']['connections'][websocket]
            logging.warning(
                f"客戶端 {caller_id or '未知'},{websocket},{caller_type} 斷開連接 (code: {e.code}, reason: {e.reason})")
            remove_socket = True
            json_data = {
                "action": "wifi_get_status",
                "caller_id": caller_id,
                "result": "Fail, 002:device not found",
                "uuid": hex(id(websocket))
            }
            
            if(caller_type & 1):
                print(f' 傳送斷線廣播!{caller_type} ', flush=True)
                await client_manager.notify_clients(caller_id, f'{json.dumps(json_data)}', 0x8)
            else:
                # print(f'不傳送斷線廣播!{caller_type} ', flush=True)
                pass

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

    async def process_json_message(self, json_data, websocket, is_new_connection):
        """處理JSON格式訊息"""
        # print('process_json_message')
        caller_id = json_data.get('caller_id') or json_data.get('device_id')

        # 處理登入動作
        if json_data.get("action") == 'login':
            return await self.handle_auth_json(caller_id, json_data, websocket)

        # 檢查是否已驗證
        if not await self.check_authentication(caller_id, websocket):
            logging.info(f"1_尚未登入:{json_data}")
            await websocket.send(json.dumps({"result": "Fail,004:not logged in"}))
            return

        # 處理WiFi指令
        if "action" in json_data and json_data["action"].startswith("wifi_"):
            await self.handle_wifi_command(caller_id, json_data, websocket)
            return

        # 處理其他JSON指令
        if json_data.get("action") in client_wait_reply_actions_to_check:
            # print('handle_json_cmd_with_reply')
            await self.handle_json_cmd_with_reply(caller_id, json_data, websocket)
        else:
            # print('handle_json_cmd_no_reply')
            await self.handle_json_cmd_no_reply(caller_id, json_data, websocket)

    async def process_non_json_message(self, message, websocket, is_new_connection):
        """處理非JSON格式訊息"""
        caller_id, m_cmd, m_info = self.parse_message(message)

        if is_new_connection:
            print(f'\n新Client連接:{caller_id},{m_cmd},{m_info} ', end='', flush=True)

        # 處理特殊指令
        # if m_cmd in CALLER_CSV_COMMANDS_TO_PROCESS:
        #     self.print_command_info(caller_id, m_cmd, m_info)
        if m_cmd in CALLER_CSV_COMMANDS_TO_PROCESS:
            # 印出接收到的指令資訊
            if m_cmd != 'auth' and m_info:  # 如果指令不是 'auth' 且 m_info 不為空
                print(f'0_收:{caller_id},{m_cmd},{m_info} ',
                      end='', flush=True)
            else:
                print(f'1_收:{caller_id},{m_cmd} ', end='', flush=True)
            if m_cmd == 'info':     # info
                print('\n發送 WiFi 狀態查詢請求')
                json_data = {
                    "action": "wifi_get_status",
                    "caller_id": caller_id,
                    # Caller 之 websocket ID
                    "uuid": hex(id(websocket))
                }
                await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x1)

        # 處理驗證
        if m_cmd == 'auth':
            return await self.handle_auth(caller_id, message.split(','), websocket)

        # 檢查是否已驗證
        if not await self.check_authentication(caller_id, websocket):
            logging.info(f"3_尚未登入:'{caller_id},{m_cmd},{m_info}'")
            await websocket.send(f"Fail,004:not logged in,{m_cmd}")
            return

        # 處理各種指令
        if m_cmd == 'get_num_info':
            await self.handle_get_num_info(caller_id, message.split(','), websocket)
        elif m_cmd == 'ping':
            await self.handle_ping(caller_id, m_info, websocket)
        elif m_cmd == 'info':
            await websocket.send(f'OK,{caller_id},info')
        elif m_cmd == 'get':
            await self.handle_get(caller_id, websocket)
        # elif m_cmd in ('send', '') and m_info != '0':   # !!!@@@
        elif m_cmd in ('send', ''):   # !!!@@@
            await self.handle_send(caller_id, m_info, websocket)
        else:
            print(f"錯誤的命令! {caller_id},{m_cmd},{m_info}")
            await websocket.send(f'OK,{caller_id},{self.last_num},{m_cmd}')

    async def check_authentication(self, caller_id, websocket):
        """檢查是否已通過驗證"""
        clients = await client_manager.get_all_clients()
        return has_websocket(clients, websocket)

    async def handle_wifi_command(self, caller_id, json_data, websocket):
        """處理WiFi相關指令"""
        clients = await client_manager.get_all_clients()

        if 'result' not in json_data:  # 詢問
            print(f'WiFi 傳送至C:{json_data}')
            clients[caller_id]['connections'][websocket] |= 0x8
            result = await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x1, websocket)
            if result <= 0:     # 沒有實體機
                json_data["result"]= "Fail, 002:device not found"
                await websocket.send(json.dumps(json_data))
        else:  # 回應
            print(f'WiFi 接收從C:{json_data}')
            await client_manager.notify_clients(caller_id, json.dumps(json_data), 0x8, websocket)

    async def handle_ping(self, caller_id, m_info, websocket):
        """處理ping指令"""
        await websocket.send('pong')
        clients = await client_manager.get_all_clients()
        existing_num = clients.get(caller_id, {}).get('caller_num', 0)
        if existing_num == 0 and m_info.isdigit() and int(m_info) != 0:
            clients[caller_id]['caller_num'] = int(m_info)

    async def handle_get(self, caller_id, websocket):

        # await asyncio.sleep(2)
        # print('2_取得叫號機號碼: get_num_info frontend',flush=True)
        # data =  {             # 設定叫號機
        #     "action": "get_num_info",
        #     "vendor_id": "tawe",
        #     "caller_id": caller_id,
        #     "user_id": "_frontend",
        #     "uuid": hex(id(websocket))
        # }
        # await asyncio.sleep(2)
        # await ws_server.ws_client.send(json.dumps(data))    # 至 Main Server

        """處理get指令"""
        current_num = await client_manager.get_caller_num(caller_id)
        await websocket.send(f'OK,{caller_id},{current_num},get')

    async def handle_send(self, caller_id, m_info, websocket):
        """處理send指令"""
        clients = await client_manager.get_all_clients()
        if clients[caller_id]['connections'][websocket] == 4:  # user_get_num
            logging.info(f"5_尚未登入:'{caller_id},send,{m_info}'")
            await websocket.send(f"Fail,004:not logged in,send")
            return

        new_num = int(m_info)
        await client_manager.update_caller_info(caller_id, new_num)
        await websocket.send(f'OK,{caller_id},{new_num},send')
        await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff, websocket)
        # 至 Main SErver
        await self.handle_send_message(caller_id, new_num, websocket)

    def print_command_info(self, caller_id, m_cmd, m_info):
        """列印指令資訊"""
        if m_cmd != 'auth' and m_info:
            print(f'0_收:{caller_id},{m_cmd},{m_info} ', end='', flush=True)
        else:
            print(f'1_收:{caller_id},{m_cmd} ', end='', flush=True)

        if m_cmd == 'info':
            print('\n發送 WiFi 狀態查詢請求', flush=True)

    async def cleanup_connection(self, caller_id, websocket):
        """清理斷開的連接"""
        try:
            clients = await client_manager.get_all_clients()
            if caller_id in clients and websocket in clients[caller_id]['connections']:
                print(next((f"1_discard: {ws}, 类型: {ws_type}"
                            for ws, ws_type in clients[caller_id]['connections'].items()
                            if ws == websocket), "未找到 websocket"))
                await client_manager.remove_connection(caller_id, websocket)
        except Exception as cleanup_error:
            logging.error(f"清理資源時發生錯誤: {cleanup_error}", exc_info=True)

    # Caller
    async def handle_json_cmd_no_reply(self, caller_id, json_data, websocket):
        async with self.ws_cmd_lock.acquire(f'ws_cmd_lock json_cmd:{caller_id}'):
            # print(f"handle_json_cmd_no_reply {json_data}!!!")
            # action_value = json_data.get("action")
            max_retries = 3
            retry_delay = 3
            for attempt in range(max_retries):
                if attempt >= 1:
                    print(
                        f'handle_json_cmd_no_reply Retry {attempt+1}/{max_retries}')
                if self.ws_client:
                    try:

                        # 若是 send 則先 發送 update 再傳至 Main Server.
                        if not "action" in json_data:           # json 'send'
                            if not "call_num" in json_data:
                                logging.warning("找不到 call_num 資料，略過處理")
                                return
                            new_num = json_data.get('call_num')
                            print(
                                f'2_收:{caller_id},send,{new_num},JSON ', end='', flush=True)
                            await client_manager.update_caller_info(caller_id, new_num)
                            # 'update' 不傳送給發送端
                            await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update', 0xff, websocket)
                        # 至 Main Server
                        await self.ws_client.send(json.dumps(json_data))
                        return

                    except Exception as e:
                        logging.error(
                            f"handle_json_cmd_no_reply 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}, {json.dumps(json_data)} ")
                        # traceback.print_exc()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            # 至 caller
            await websocket.send("Fail,001:不支援此功能,auth")

    # Caller
    async def handle_json_cmd_with_reply(self, caller_id, json_data, websocket):
        # print(f"0_handle_json_cmd_with_reply {json_data}!!!")
        async with self.ws_cmd_lock.acquire(f'ws_cmd_lock json_cmd:{caller_id}'):
            # print(f"1_handle_json_cmd_with_reply {json_data}!!!")
            action_value = json_data.get("action")
            pass
            max_retries = 3
            retry_delay = 3
            for attempt in range(max_retries):
                if attempt >= 1:
                    print(
                        f'handle_json_cmd_with_reply Retry {attempt+1}/{max_retries}')
                if self.ws_client:
                    try:
                        # 至 Main Server
                        await self.ws_client.send(json.dumps(json_data))
                        # 等待回應
                        # print('handle_json_cmd_with_reply 等待回應')
                        start_time = time.time()

                        cmb_msg = []
                        while not cmb_msg and time.time() - start_time < self.server_timeout:
                            cmb_msg = manager.search_data(
                                lambda x: x.get("action") in client_wait_reply_actions_to_check)
                            if cmb_msg:
                                # print(f'找到資料{action_value}:{cmb_msg}')
                                break
                            else:
                                # print(f"num_info:{caller_id} 尚未找到資料 {action_value}，繼續等待...")
                                pass
                            await asyncio.sleep(0.001)
                            # await asyncio.sleep(2)

                        # print(f'handle_json_cmd_with_reply {action_value} 找到 json 回覆資料:{cmb_msg}')
                        if cmb_msg:             # Caller, JSON
                            manager.remove_matched(cmb_msg)     # 移除已匹配資料
                            # 'user_get_num' 需群發
                            if cmb_msg[0].get("action") == 'user_get_num':
                                # clients = await client_manager.get_all_clients()
                                # # 因為群發時不發至 user
                                # if clients[caller_id]['connections'][websocket] == 4:
                                #     # 發送至取號之 Client user
                                #     # print(f'發送至Client:{json.dumps(cmb_msg[0])}')
                                #     await websocket.send(f"{json.dumps(cmb_msg[0])}")               # 至 caller

                                # 因為群發時不發至取號端，"action" 不同
                                # 發送至取號之 Client
                                # print(f'發送至Client:{json.dumps(cmb_msg[0])}')
                                # 至 caller
                                await websocket.send(f"{json.dumps(cmb_msg[0])}")

                                # print(f'不發送至 USER 的裝置:{cmb_msg} ', flush=True)
                                # logging.info(f"群發訊息至 SOFT cmb-caller 的 caller_id={caller_id}: {cmb_msg}")
                                # await client_manager.notify_clients(caller_id, f'{json.dumps(cmb_msg[0])}', 0x2) # 只發到店家
                                new_msg = {
                                    "action": 'new_get_num',
                                    'vendor_id': cmb_msg[0]['vendor_id'],
                                    'caller_id': cmb_msg[0]['caller_id'],
                                    # user_get_num get_num 對應
                                    'curr_num': cmb_msg[0]['get_num'],
                                    'get_num_item_id': cmb_msg[0]['get_num_item_id']
                                }
                                # logging.info(f"群發訊息至 SOFT cmb-caller 的 caller_id={caller_id}: {json.dumps(new_msg)}")
                                # 只發到店家，但不傳送給發送端之店家
                                await client_manager.notify_clients(caller_id, f'{json.dumps(new_msg)}', 0x2, websocket)
                            else:   # get_num_status & get_num_info, 不廣播
                                if cmb_msg[0].get("action") == 'get_num_info':
                                    # print(f'設定叫號機 {caller_id}:{cmb_msg[0].get("call_num")}')
                                    await client_manager.update_caller_info(caller_id, cmb_msg[0].get("call_num"))
                                try:
                                    # 發送至詢問之 Client
                                    # print(f'發送至Client:{json.dumps(cmb_msg[0], ensure_ascii=False)}')
                                    # 至 caller
                                    await websocket.send(f"{json.dumps(cmb_msg[0])}")
                                except:
                                    logging.info(
                                        f"handle_json_cmd_with_reply 回覆至 user_get_num caller 發生錯誤! caller_id={caller_id}: {cmb_msg}")
                            return
                        else:
                            print(
                                f'handle_json_cmd_with_reply 逾時重送! (嘗試 {attempt+1}/{max_retries})')
                    except Exception as e:
                        logging.error(
                            f"handle_json_cmd_with_reply 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}")
                        # traceback.print_exc()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            # 至 caller
            await websocket.send("Fail,001:不支援此功能,auth")

    # Caller, 會等待, CSV
    async def handle_get_num_info(self, caller_id, parts, websocket):
        # async with self.ws_cmd_lock:  # 使用鎖來確保一次只有一個驗證過程
        async with self.ws_cmd_lock.acquire(f'ws_cmd_lock get_num:{caller_id}'):
            if len(parts) != 2:
                logging.info("無效的 get_num_info 格式!")
                # 至 caller
                await websocket.send("Fail,006:無效的CMD指令")
                return

            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                if attempt >= 1:
                    print(
                        f'handle_get_num_info Retry {attempt+1}/{max_retries}')
                login_data = {
                    "action": "get_num_info",         # 動作指令
                    "vendor_id": self.vendor_id,      # 叫號機廠商 id
                    "caller_id": caller_id,          # 叫號機 id
                    "uuid": "CSV"  # 封包識別碼
                }

                if not self.ws_client:
                    print('handle_get_num_info: ws_client 已斷線!')
                    pass
                else:
                    try:
                        # print(f'ws_client.send: {json.dumps(login_data)}')
                        # 至 Main Server
                        await self.ws_client.send(json.dumps(login_data))
                        # 等待回應
                        start_time = time.time()
                        self.ws_client.cmb_msg = ''

                        cmb_msg = []
                        while not cmb_msg and time.time() - start_time < self.server_timeout:
                            cmb_msg = manager.search_data(
                                lambda x: x.get("action") == "get_num_info")
                            if cmb_msg:
                                # print(f'找到資料:{found_data}')
                                break
                            else:
                                # print(f"num_info:{caller_id} 尚未找到資料，繼續等待...")
                                pass
                            await asyncio.sleep(0.001)

                        # print(f'找到資料:{cmb_msg}')
                        manager.remove_matched(cmb_msg)     # 移除已匹配資料
                        # cmb_msg = json.dumps(cmb_msg)
                        if cmb_msg:
                            # response = json.loads(cmb_msg)
                            response = dict(cmb_msg[0])
                        # if self.ws_client.cmb_msg:
                        #     response = json.loads(self.ws_client.cmb_msg)
                            if response.get("result") == "OK":
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
                                # print(
                                #     f"handle_get_num_info:OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                # ===============================  !!!@@@
                                # 至 caller
                                await websocket.send(f"OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                # self.ws_client.cmb_msg = ''
                                return
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
                                msg = msg_map.get(code, '001,驗證失敗')
                                # 至 caller
                                await websocket.send(f"Fail,{msg},get_num_info")
                                return
                        else:
                            print(
                                f'handle_get_num_info 逾時重送! (嘗試 {attempt+1}/{max_retries})')

                    except Exception as e:
                        logging.error(
                            f"handle_get_num_info 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}")
                        # traceback.print_exc()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            # 至 caller
            await websocket.send("Fail,001:不支援此功能,auth")

    # Caller, json 呼叫專用
    async def handle_auth_json(self, caller_id, json_data, websocket):      # JSON
        """處理驗證請求"""
        async with self.ws_cmd_lock.acquire(f'ws_cmd_lock auth:{caller_id}'):
            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                if attempt >= 1:
                    print(f'handle_auth_json Retry {attempt+1}/{max_retries}')
                if self.ws_client:               # JSON
                    try:
                        start_time = time.time()
                        ws_type = -1
                        # ASTRO_cmb-caller
                        # if (encrypted_password == 'liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='):
                        if False:
                            # print(
                            #     f' *** CMB Caller:{caller_id} *** ', end='', flush=True)
                            # clients = await client_manager.get_all_clients()
                            # # print(f'get clients:{clients}')
                            # existing_num = clients.get(
                            #     caller_id, {}).get('caller_num', 0)
                            # current_num = int(existing_num)  # 確保是 int
                            # # cmb_msg = f'{{"action":"login","result":"OK","caller_name":"{caller_id} caller","curr_num":{current_num}}}'
                            # cmb_msg = f'{{"action":"login","vendor_id":"tawe","caller_id":"{caller_id}","uuid":"","caller_name":"{caller_id}_caller","curr_num":"{current_num}","result":"OK"}}'
                            # manager.add_data(cmb_msg)
                            # ws_type = 1
                            # # print(f'handle_auth cmb_msg:{cmb_msg}')
                            pass
                        else:       # 至 CMB Main Server
                            # 至 Main Server
                            await self.ws_client.send(json.dumps(json_data))
                            if json_data.get('password') == 'user_get_num':
                                print(
                                    f' *** user_get_num:{caller_id} *** ', end='', flush=True)
                                ws_type = 4
                            else:
                                print(
                                    f' *** SOFT CMB Caller:{caller_id} *** ', end='', flush=True)
                                ws_type = 2

                        # self.ws_type = ws_type
                        # 等待回應
                        cmb_msg = []
                        while not cmb_msg and time.time() - start_time < self.server_timeout:
                            cmb_msg = manager.search_data(
                                lambda x: x.get("action") == "login")
                            if cmb_msg:
                                # print(f'找到資料:{found_data}')
                                break
                            else:
                                # print("AUTH:{caller_id} 尚未找到資料，繼續等待...")
                                pass
                            await asyncio.sleep(0.0001)

                        # print(f'找到資料:{cmb_msg}')
                        manager.remove_matched(cmb_msg)     # 移除已匹配資料
                        if cmb_msg:                         # Json
                            response = dict(cmb_msg[0])

                            if response.get("result") == "OK":          # Json
                                # 驗證成功
                                self.ws_cmd_lock.release()  # 解除鎖定!!!
                                await client_manager.add_connection(caller_id, websocket, ws_type)
                                self.ws_client.cmb_msg = ''
                                print(f'{caller_id},1_驗證成功! ',
                                      end='', flush=True)
                                # print(f'{caller_id},{cmb_msg[0]}')
                                try:
                                    if websocket.open:
                                        # 至 caller
                                        msg = cmb_msg[0]
                                        if "hardware" not in msg:   # 如未設就加入
                                            if msg.get("caller_id", "").startswith("v"):
                                                msg["hardware"] = False
                                            else:                                        
                                                msg["hardware"] = True
                                        # await websocket.send(f"{json.dumps(cmb_msg[0])}")
                                        await websocket.send(f"{json.dumps(msg)}")
                                    else:
                                        logging.warning(
                                            f"WebSocket 已關閉，無法回傳成功訊息給 {caller_id}")
                                except Exception as e:
                                    logging.error(f"傳送成功訊息失敗: {e}")

                                # await asyncio.sleep(2)
                                # print('1_取得叫號機號碼: get_num_info frontend',flush=True)
                                # data =  {             # 設定叫號機
                                #     "action": "get_num_info",
                                #     "vendor_id": "tawe",
                                #     "caller_id": caller_id,
                                #     "user_id": "_frontend",
                                #     "uuid": hex(id(websocket))
                                # }
                                # await ws_server.ws_client.send(json.dumps(data))    # 至 Main Server

                                return True
                            else:
                                # 驗證失敗
                                print(f'驗證失敗 {caller_id},{cmb_msg[0]}')
                                try:
                                    if websocket.open:
                                        # 至 caller
                                        await websocket.send(f"{json.dumps(cmb_msg[0])}")
                                    else:
                                        logging.warning(
                                            f"WebSocket 已關閉，無法回傳失敗訊息給 {caller_id}")
                                except Exception as e:
                                    logging.error(f"傳送失敗訊息失敗: {e}")
                                return False
                        else:
                            print(
                                f'handle_auth 逾時重送! (嘗試 {attempt+1}/{max_retries})')

                    except Exception as e:
                        # logging.error(
                        #     f"handle_auth 傳送至Server失敗 (嘗試 {attempt+1}/{max_retries}): {e}")
                        logging.error(
                            f"handle_auth_json 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}, {caller_id}")
                        # traceback.print_exc()
                        print(
                            f'self.ws_client.cmb_msg:{self.ws_client.cmb_msg}')
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            await websocket.send("Fail,001:驗證失敗,auth")       # 至 Caller
            return False

    async def handle_auth(self, caller_id, parts, websocket):       # Caller
        """處理驗證請求"""
        # print(f'handle_auth:{parts} ', end='', flush=True)
        # async with self.ws_cmd_lock:  # 使用鎖來確保一次只有一個驗證過程
        async with self.ws_cmd_lock.acquire(f'ws_cmd_lock auth:{caller_id}'):

            # print(f'{caller_id},處理驗證請求')
            if len(parts) != 3:
                logging.info("無效的驗證格式!")
                await websocket.send("Fail,004:無效的驗證格式")   # 至 Caller
                return False

            encrypted_password = parts[2]
            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                if attempt >= 1:
                    print(f'handle_auth Retry {attempt+1}/{max_retries}')
                login_data = {
                    "action": "login",
                    "vendor_id": self.vendor_id,
                    "caller_id": caller_id,
                    "password": encrypted_password,
                    "uuid": "CSV"
                }

                if self.ws_client:                  # CSV
                    try:
                        start_time = time.time()
                        ws_type = -1
                        # ASTRO_cmb-caller
                        if (encrypted_password == 'liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='):
                            print(
                                f' *** CMB Caller:{caller_id} *** ', end='', flush=True)
                            clients = await client_manager.get_all_clients()
                            # print(f'get clients:{clients}')
                            existing_num = clients.get(
                                caller_id, {}).get('caller_num', 0)
                            current_num = int(existing_num)  # 確保是 int
                            # cmb_msg = f'{{"action":"login","result":"OK","caller_name":"{caller_id} caller","curr_num":{current_num}}}'
                            cmb_msg = f'{{"action":"login","vendor_id":"tawe","caller_id":"{caller_id}","uuid":"Null","caller_name":"{caller_id}_caller","curr_num":"{current_num}","result":"OK"}}'
                            manager.add_data(cmb_msg)
                            ws_type = 1
                            # print(f'handle_auth cmb_msg:{cmb_msg}')

                        else:       # 至 CMB Main Server
                            # 至 Main Server
                            await self.ws_client.send(json.dumps(login_data))
                            if encrypted_password == 'user_get_num':
                                print(
                                    f' *** user_get_num:{caller_id} *** ', end='', flush=True)
                                ws_type = 4
                            else:
                                print(
                                    f' *** SOFT CMB Caller:{caller_id} *** ', end='', flush=True)
                                ws_type = 2

                        # self.ws_type = ws_type
                        # 等待回應
                        cmb_msg = []
                        while not cmb_msg and time.time() - start_time < self.server_timeout:
                            cmb_msg = manager.search_data(
                                lambda x: x.get("action") == "login")
                            if cmb_msg:
                                # print(f'找到資料:{found_data}')
                                break
                            else:
                                # print("AUTH:{caller_id} 尚未找到資料，繼續等待...")
                                pass
                            await asyncio.sleep(0.0001)

                        # print(f'找到資料:{cmb_msg}')
                        manager.remove_matched(cmb_msg)     # 移除已匹配資料

                        if cmb_msg:                         # CSV
                            # response = json.loads(cmb_msg)
                            response = dict(cmb_msg[0])
                            if response.get("result") == "OK":
                                # 驗證成功
                                self.ws_cmd_lock.release()  # 解除鎖定!!!
                                await client_manager.add_connection(caller_id, websocket, ws_type)
                                # print('auth: ', end='', flush=True)
                                await client_manager.update_caller_info(
                                    caller_id,
                                    caller_num=await client_manager.get_caller_num(caller_id),
                                    caller_name=response.get('caller_name', '')
                                )
                                # print(f'{caller_id},驗證成功', end='\n', flush=True)
                                print(f'{caller_id},0_驗證成功! ',
                                      end='', flush=True)
                                # 至 Caller
                                # 至 caller
                                await websocket.send(f"OK,{response.get('caller_name','')},auth")
                                self.ws_client.cmb_msg = ''

                                # await asyncio.sleep(2)
                                # print('0_取得叫號機號碼: get_num_info frontend',flush=True)
                                # data =  {             # 設定叫號機
                                #     "action": "get_num_info",
                                #     "vendor_id": "tawe",
                                #     "caller_id": caller_id,
                                #     "user_id": "_frontend",
                                #     "uuid": hex(id(websocket))
                                # }
                                # await ws_server.ws_client.send(json.dumps(data))    # 至 Main Server

                                return True
                            else:
                                # 處理錯誤回應
                                code = response.get("result").split(
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
                                await websocket.send(f"Fail,{msg},auth")
                                return False
                        else:
                            print(
                                f'handle_auth 逾時重送! (嘗試 {attempt+1}/{max_retries})')

                    except Exception as e:
                        logging.error(
                            f"handle_auth 傳送至Server失敗:(嘗試 {attempt+1}/{max_retries}): {e}, {caller_id}")
                        # traceback.print_exc()
                        print(
                            f'self.ws_client.cmb_msg:{self.ws_client.cmb_msg}')
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            await websocket.send("Fail,001:驗證失敗,auth")      # 至 Caller
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
            return caller_id, m_cmd.lower(), m_info
        except Exception as e:
            logging.error(f"parse_message 處理失敗 {e}")
            traceback.print_exc()

    # caller 'send' 命令使用       # Caller
    # SEND CMD, CSV
    async def handle_send_message(self, caller_id, call_num, websocket):
        """處理訊息並生成回應"""
        call_num = int(call_num)
        max_retries = 3
        retry_delay = 3
        for attempt in range(max_retries):
            if attempt >= 1:
                print(f'handle_send_message Retry {attempt+1}/{max_retries}')
            try:
                # 1. 準備數據
                data = {
                    "vendor_id": self.vendor_id,
                    "caller_id": caller_id,
                    "call_num": call_num,
                    "change": True,
                    "last_update": 0,
                    "uuid": "CSV_SEND"
                    # "uuid": hex(id(websocket))      # Caller 之 websocket ID
                }

                # 2. 檢查WebSocket連接
                if not self.ws_client or not self.ws_client.connect:
                    logging.error("WebSocket連接不可用")
                    await asyncio.sleep(retry_delay)
                    continue

                # 3. 發送消息
                try:
                    # 至 Main Server
                    await self.ws_client.send(json.dumps(data))
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
    global ws_server
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
                for websocket, ws_type in client_info['connections'].items():
                    # print(f"  WebSocket: {websocket}, Type: {ws_type}")
                    # print(f"  WebSocket:{ websocket.open }")
                    if not websocket.open:
                        # print(f'3_discard{websocket}:{caller_id}', end='\n', flush=True)
                        disconnected.add((caller_id, websocket))

            # print("發送例行資料_1: ", end='', flush=True)
            for caller_id, ws in disconnected:
                # print(f'移除已斷開的連接:{caller_id} ', end='', flush=True)
                # print(f'disconnected:{disconnected}', end='\n', flush=True)
                print(next((f"3_discard: {ws}, 类型: {ws_type}" for ws0, ws_type in clients[caller_id]['connections'].items(
                ) if ws0 == ws), "未找到 websocket"))
                # found = "未找到 websocket"
                # for ws0, ws_type in clients[caller_id]['connections'].items():
                #     if ws0 == ws:
                #         found = f"3_discard: {ws}, 类型: {ws_type}"
                #         break
                # print(found)
                # print(f'3_discard:{caller_id},{ws}', end='\n', flush=True)
                await client_manager.remove_connection(caller_id, ws)

        # print("發送例行資料_2: ", end='', flush=True)
        # 發送狀態更新
        clients = await client_manager.get_all_clients()
        active_client = 0
        connected_client = 0
        # print("發送例行資料_3: ", end='', flush=True)
        print("", flush=True)
        # Logger.log("發送例行資料:")
        # print('發送例行資料:', end='\n', flush=True)
        print(f"#{os.getenv('K_REVISION', 'local')} 發送例行資料:", end='\n', flush=True)
        print('例行資料: ', end='', flush=True)

        # if not ws_server.is_serving():
        # if not ws_server:
        # print(f"ws_server_2:{ws_server}", flush=True)
        if ws_server == None:
            # print("Websocket Server 已關閉!",flush=True)
            print(f"#{os.getenv('K_REVISION', 'local')} Websocket Server 早已關閉!\n", flush=True)
            
        else:
            issue = False
            for caller_id, info in clients.items():
                try:
                    is_connected = bool(info['connections'])
                    is_active = info['disconnect_time'] is None or (
                        datetime.now() - info['disconnect_time']).total_seconds() < 600     # 有效連線(斷線10分鐘內)
    
                    # datetime.now() - info['disconnect_time']).total_seconds() < 3600
    
                    if is_connected:
                        connected_client += 1
                    if is_active:
                        active_client += 1
    
                        def calculate_last_update(is_connected, disconnect_time):
                            if is_connected:
                                return 0
                            if disconnect_time is None:
                                return 1  # 預設值，代表「未知斷線時間」
                            time_since_disconnect = datetime.now() - disconnect_time
                            minutes_offline = max(
                                0, int(time_since_disconnect.total_seconds() / 60))
                            return minutes_offline + 1
    
                        # # 使用 calculate_last_update 函數
                        # last_update = calculate_last_update(is_connected, info['disconnect_time'])
    
                        # 發送更新到CMB主伺服器
                        data = {
                            "vendor_id": "tawe",
                            "caller_id": caller_id,
                            "call_num": info['caller_num'],
                            "change": not is_connected,
                            "last_update": calculate_last_update(is_connected, info['disconnect_time']),
                            "uuid": hex(id(ws_server.ws_client))    # frontend 之 ID
                        }
    
                        if info['caller_num'] == '0':
                            print(
                                f"{caller_id}資料無效(info['caller_num']) ", end='', flush=True)
                        else:
                            print(
                                f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]} ', end='', flush=True)
                        # print(f'DEPLOY_TIMESTAMP:{int(os.getenv("DEPLOY_TIMESTAMP", "0"))}')
                        # print(f" 發送例行資料:{data} ",end='', flush=True)
                        # 至 Main Server
                        await ws_server.ws_client.send(json.dumps(data))
                        # print("發送例行資料_4: ",end='', flush=True)
    
                except Exception as e:
                    # print("發送例行資料_5: ", end='', flush=True)
                    logging.error(f"發送例行資料 傳送至Server失敗:{e}, 10秒後繼續發送例行資料!!!")
                    # print("10秒後繼續發送例行資料!!!", flush=True)
                    # traceback.print_exc()
                    # 出錯後將 start_time 設為xx秒前
                    # 離開 periodic_send_frame ， 10秒後重新進入
                    start_time = datetime.now() - timedelta(seconds=(60-10))
                    issue = True
                    break   # 離開 for 迴圈
            if not issue:
                # print("發送例行資料_6: ",end='', flush=True)
                print("", flush=True)
                # 記錄狀態
                # print(f'記錄狀態 clients:{clients}')
                total_websockets = sum(len(client['connections'])
                                       for client in clients.values())
                Logger.log(
                    f"總共有 {len(clients)} 個紀錄中 ID, "
                    f"{active_client} 個有效的 ID, "
                    f"{connected_client} 個連線中 ID, "
                    f"{total_websockets} 個連線中 Client, "
                    f"{manager.count_data()} 個 Server 回覆暫存資料"
                )
        
                # type_counter = Counter()
                # for caller_id, client_info in clients.items():
                #     # print(f"Caller ID: {caller_id}")
                #     for websocket, ws_type in client_info['connections'].items():
                #         # print(f"  WebSocket: {websocket}, Type: {ws_type}")
                #         type_counter[ws_type] += 1
                # # 印出各類型的統計結果
                # for t in [1, 2, 4, 8]:
                #     print(f"type_{t}:{type_counter[t]} ",end='',flush=True)
                # print('',flush=True)
        
                # 使用字典來動態統計各類型數量，避免多個獨立變數
                type_counts = {1: 0, 2: 0, 4: 0, 8: 0}
        
                for caller_id, client_info in clients.items():
                    # print(f"Caller ID: {caller_id}")
                    for websocket, ws_type in client_info['connections'].items():
                        # print(f"  WebSocket: {websocket}, Type: {ws_type}")
                        # 使用位元運算檢查所有可能的類型
                        for type_flag in type_counts.keys():
                            if ws_type & type_flag:
                                type_counts[type_flag] += 1
                # 最終輸出統計結果
                # print("\nConnection Type Summary:")
                for type_flag, count in type_counts.items():
                    # print(f"Type {type_flag}: {count} connections")
                    print(f"Type_{type_flag}:{count} ", end='', flush=True)
                print('', flush=True)

        # 確保每60秒執行一次
        execution_time = (datetime.now() - start_time).total_seconds()
        await asyncio.sleep(max(60 - execution_time, 0))


        # disconnected = set()        # ~~~~~~~~~~~~~~~
        # for caller_id, client_info in clients.items():
        #     # print(f"Caller ID: {caller_id}")
        #     for websocket, ws_type in client_info['connections'].items():
        #         if not websocket.open:
        #             disconnected.add((caller_id, websocket))
        # for caller_id, ws in disconnected:
        #     print(next((f"4_discard: {ws}, 类型: {ws_type}" for ws0, ws_type in clients[caller_id]['connections'].items(
        #     ) if ws0 == ws), "未找到 websocket"))
        #     await client_manager.remove_connection(caller_id, ws)
        # await asyncio.sleep(20)

        # disconnected = set()
        # for caller_id, client_info in clients.items():
        #     # print(f"Caller ID: {caller_id}")
        #     for websocket, ws_type in client_info['connections'].items():
        #         if not websocket.open:
        #             disconnected.add((caller_id, websocket))
        # for caller_id, ws in disconnected:
        #     print(next((f"5_discard: {ws}, 类型: {ws_type}" for ws0, ws_type in clients[caller_id]['connections'].items(
        #     ) if ws0 == ws), "未找到 websocket"))
        #     await client_manager.remove_connection(caller_id, ws)
        # await asyncio.sleep(20)


# async def check_client_connection(caller_id=None, websocket=None):
#     """檢查特定 client 或所有 client 的連線狀態"""
#     clients = await client_manager.get_all_clients()

#     if caller_id and websocket:
#         # 檢查特定連接
#         if caller_id in clients:
#             return websocket in clients[caller_id]['connections']
#         return False

#     # 返回所有活躍連接資訊
#     return {
#         caller_id: {
#             'connection_count': len(connections),
#             'last_active': client.get('last_active', 'unknown')
#         }
#         for caller_id, client in clients.items()
#     }

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


# from datetime import datetime

# import pytz

async def main():
    global ws_server
    """主程式入口"""
    try:
        # # 設定台北時區
        # taipei_tz = pytz.timezone('Asia/Taipei')
        # # 取得目前時間（台北時間）
        # taipei_time = datetime.now(taipei_tz)
        # print("台北時間：", taipei_time.strftime('%Y-%m-%d %H:%M:%S'))

        # （選擇性）設定程式內預設時區為台北
        # 注意：這不會改變作業系統的時區，只影響程式邏輯
        datetime.now(ZoneInfo("Asia/Taipei"))
        # print("預設為台北時間：", now.strftime("%Y-%m-%d %H:%M:%S"))

        # 列出所有環境變數
        # print("\n列出所有環境變數")
        # for key, value in os.environ.items():
        #     print(f"{key} = {value}")

        print(".\n", flush=True)
        print(".\n", flush=True)
        await asyncio.sleep(1)
        logging.info(
            f"***** cmb-caller-frontend Ver.{VER} (GCE & GCR) 開始執行! #{os.getenv('K_REVISION', 'local')} *****")
        print(".\n", flush=True)
        print(".\n", flush=True)



        port, ws_url, platform_name = get_platform_config()
        if platform_name == 'Cloud_Run':
            # 啟動 Pub/Sub 訂閱
            # sub_task = asyncio.create_task(delayed_subscribe())
            # await asyncio.create_task(delayed_subscribe())      # ~~~~~
            # asyncio.create_task(delayed_subscribe())      # ~~~~~
            # asyncio.create_task(delayed_subscribe())      # ~~~~~
    
            # broadcast_message('STOP_SERVER','新 Server instance 啟動通知_1!')
            # await asyncio.sleep(0.5)
            # broadcast_message('STOP_SERVER','新 Server instance 啟動通知_2!')
            # await asyncio.sleep(0.5)
            # broadcast_message('STOP_SERVER','新 Server instance 啟動通知_3!')
            # await asyncio.sleep(1)

            # 啟動 Pub/Sub 訂閱（非阻塞）
            sub_task = asyncio.create_task(delayed_subscribe())
            
            # 發送初始化通知（3次確保送達）
            for i in range(1, 4):
                broadcast_message('STOP_SERVER', f'新 Server instance 啟動通知_{i}!')
                await asyncio.sleep(0.5)

            CREDENTIALS, PROJECT_ID = default()
            print(
                f"CREDENTIALS: {CREDENTIALS}, Project ID: {PROJECT_ID}", flush=True)
            if PROJECT_ID == 'callme-398802':                                       # CallMe Beta
                ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"  # 強制設定至 CMB Live
                logging.info("CMB Live Server!")
            else:
                logging.info("CMB Trial Server!")

        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')
        # 初始化並啟動 WebSocket Client, 連接至 CMB Main Server
        ws_client = WebSocketClient(ws_url)
        asyncio.create_task(ws_client.connect())

        # 初始化並啟動 WebSocket Server
        ws_server = WebSocketServer('0.0.0.0', port)
        ws_server.ws_client = ws_client
        ws_server_task = asyncio.create_task(ws_server.start())

        # 每分鐘發送現有之caller_id
        periodic_task = asyncio.create_task(periodic_send_frame(ws_server))

        # 保持主執行緒運行
        while True:
            await asyncio.sleep(2)

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
