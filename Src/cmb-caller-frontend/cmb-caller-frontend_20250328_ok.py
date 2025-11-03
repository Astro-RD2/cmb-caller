'''
websockets 14 板以上有相容性問題
pip uninstall websockets -y
pip install websockets==13.1
pip show websockets

'''


'''
2025/0x/xx  Roy Ching    支援 GCE
2025/03/03  Roy Ching    傳送至 sever 之 call_num 由 string 改為 int
2025/03/24  Roy Ching    支援 GCR & GCE

'''

# import random
# from typing import Optional, List


import time
from datetime import datetime
import platform
import os
import requests
import json
import asyncio
import websockets
import logging
from logging.handlers import RotatingFileHandler
import nest_asyncio
from google.auth import default
nest_asyncio.apply()


VER = "2025032413"


class Logger:
    @staticmethod
    def log(message):
        """顯示帶時間戳的狀態訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{timestamp} {message}", flush=True)


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
    for handler in logger.handlers:
        handler.setFormatter(formatter)


class ClientManager:
    def __init__(self):
        self.clients = {}
        self.lock = asyncio.Lock()

    async def add_client(self, caller_id, client_info):
        async with self.lock:
            self.clients[caller_id] = client_info

    async def remove_client(self, caller_id):
        async with self.lock:
            if caller_id in self.clients:
                del self.clients[caller_id]

    async def update_client(self, caller_id, key, value):
        async with self.lock:
            if caller_id in self.clients:
                self.clients[caller_id][key] = value

    async def cleanup_clients(self):
        async with self.lock:
            now = datetime.now()
            to_remove = [caller_id for caller_id, info in self.clients.items() if (
                now - info['disconnect_time']).total_seconds() > 3600]
            for caller_id in to_remove:
                del self.clients[caller_id]

    async def get_all_clients(self):
        async with self.lock:
            # return self.clients
            sorted_clients = dict(sorted(self.clients.items()))
            return sorted_clients


client_manager = ClientManager()


# 連結 CMB Main Server
class WebSocketClient:
    def __init__(self, ws_url):
        """初始化 WebSocket Client"""
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws = None  # CMB Main Server
        self.retry_delay = 5

    async def connect(self):
        """設置 WebSocket 連接"""
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    self.retry_delay = 5  # 重置重試延遲
                    logging.info(f"已連接到 CMB Main Server {self.ws_url}")
                    await self.listen()
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"WebSocket {self.ws_url} 錯誤: {e}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)  # 最大延遲 60 秒
            except Exception as e:
                logging.error(f"連接失敗  {self.ws_url} : {e}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)  # 最大延遲 60 秒

    async def listen(self):
        """處理接收到的訊息"""
        try:
            async for message in self.ws:
                # Logger.log(f"收到(CMB): {message}")
                self.cmb_msg = message
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"WebSocket 連接中斷: {e}")
            raise e  # 重新引發異常以便重新連接

    async def send(self, message):
        """發送訊息"""
        # Logger.log(f"發送訊息至 CMB {message}")
        if self.ws:
            await self.ws.send(message)

    async def close(self):
        """關閉 WebSocket 連接"""
        if self.ws:
            await self.ws.close()
            self.ws = None


# 連結 Caller
class WebSocketServer:
    def __init__(self, host, port):
        """初始化 WebSocket Server"""
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None   # 連結 CMB Main Server
        self.server = None      # 連結 Caller
        self.last_num = 0

    async def start(self):
        """啟動Server"""
        # self.server = await websockets.serve(self.handler, self.host, self.port, ping_interval=None)
        # self.server = await websockets.serve(self.handler, self.host, self.port, ping_interval=60)
        # self.server = await websockets.serve(self.handler, self.host, self.port, ping_interval=5, ping_timeout=5)
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,      # xx 秒，減少資源消耗
            ping_timeout=10,       # xx 秒，給予寬裕的回應時間
            max_size=4096,        # 限制訊息大小，避免記憶體問題
            compression=None       # ESP32 不需要壓縮，可提高效能
        )
        logging.info(f"WebSocket Server已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()  # 保持Server運行

    async def stop(self):
        """停止Server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handler(self, websocket, path):
        """處理新Client連接"""
        try:
            async for message in websocket:
                # 解析訊息內容
                if message == 'ping':       # 早期版本用
                    return

                caller_id, ping, call_num = self.parse_message(message)
                # 檢查 caller_id 是否存在於 client_manager 中
                clients = await client_manager.get_all_clients()
                new_client = False
                if caller_id not in clients:
                    print("", flush=True)
                    logging.info(f"新Client {caller_id} 已連接")
                    client_info = {
                        'connect_time': datetime.now(),
                        'disconnect_time': None,
                        'ip': websocket.remote_address[0],
                        'port': websocket.remote_address[1],
                        'messages': []
                    }
                    await client_manager.add_client(caller_id, client_info)
                    new_client = True
                await self.on_message(caller_id, message, websocket, new_client)
        except websockets.exceptions.ConnectionClosedError as e:
            # logging.info(f"Client連線斷開: {caller_id}, {e}")
            # logging.info(f"Client連線斷開: {e}")
            clients = await client_manager.get_all_clients()
            # disconnect_timeout = 15
            if caller_id in clients:
                print("", flush=True)
                logging.info(f"Client連線斷開: {caller_id}, {e}")
                await client_manager.update_client(caller_id, 'disconnect_time', datetime.now())

    async def on_message(self, caller_id, message, websocket, new_client):
        """處理接收到的訊息"""
        try:
            # Logger.log(f"收到(Caller {caller_id}): {message}")
            print(f'  收:{message} ', end='', flush=True)
            caller_id, ping, call_num = self.parse_message(message)
            client_msg = (f'{caller_id},{ping},{call_num}')
            clients = await client_manager.get_all_clients()
            # if ping != 'ping' or new_client:
            if (call_num != 0 and ping != 'ping') or (self.last_num == 0 and ping == 'ping'):
                clients[caller_id]['messages'] = {
                    'timestamp': datetime.now(), 'message': client_msg}
                self.last_num = call_num
            if clients[caller_id]['disconnect_time'] != None:
                clients[caller_id]['disconnect_time'] = None
                clients[caller_id]['connect_time'] = datetime.now()
                print("", flush=True)
                logging.info(f"舊Client {caller_id} 重新連接")

            if True:
                if websocket.open:
                    # if ping != 'ping':
                    if (ping != 'ping' and call_num != 0):
                        # if (ping != 'ping' and call_num != 0):
                        self.last_num = call_num
                        # print(f'  發:{caller_id}, OK, {caller_id} ', end='', flush=True)
                        # print(f'  發:{caller_id} ', end='', flush=True)
                        # print(f' 回OK_0 ', end='', flush=True)
                        await websocket.send(f'OK, {caller_id}')
                        await self.handle_message(caller_id, call_num)
                    # elif call_num == 0:
                    elif (ping != 'ping' and call_num == 0):
                        # print(f' 回OK_1 ', end='', flush=True)
                        print(f'\n', end='', flush=True)
                        logging.info(f"Websocket 連線資訊 {message}")
                        await websocket.send(f'OK, {caller_id}')
                        # call_num = self.last_num
                    elif ping == 'ping':
                        await websocket.send('pong')
                    else:
                        pass
            else:   # CMB Main Server 回覆有與client對應不上的問提，暫不使用
                # response = await self.handle_message(caller_id, call_num)
                # if response:
                #     # Logger.log(f"發送(Caller {caller_id}): {response}")
                #     print(f'  發:{caller_id},(CMB) {response} ', end='', flush=True)
                #     await websocket.send(f'(CMB) {response}')
                pass

        except Exception as e:
            logging.error(f"訊息處理失敗 (錯誤: {e})")

    def parse_message(self, message):
        """解析接收到的訊息"""
        info = ""
        ping = ""
        try:
            parts = message.split(',')
            if len(parts) < 2:
                raise ValueError(
                    "訊息格式無效，預期格式為 'caller_id,call_num' 或 'caller_id,ping,call_num'")
            if len(parts) == 2:
                caller_id, call_num = parts
            if len(parts) == 3:
                if parts[1] == 'ping':
                    caller_id, ping, call_num = parts
                else:
                    caller_id, call_num, info = parts
            call_num = int(call_num)
            return caller_id, ping, call_num
        except Exception as e:
            logging.error(f"parse_message 處理失敗 (錯誤: {e})")

    async def handle_message(self, caller_id, call_num):
        """處理訊息並生成回應"""
        # Logger.log("handle_message")
        try:
            data = {
                "vendor_id": self.vendor_id,
                "caller_id": caller_id,
                "call_num": call_num,
                "change": True,
                "last_update": 0
            }

            json_data = json.dumps(data, indent=2)
            # Logger.log(f"發送訊息至 CMB: {json_data}")
            # Logger.log(f"發送訊息至 CMB: {caller_id}, {call_num}")

            if self.ws_client:
                await self.ws_client.send(json_data)    # 至 CMB Main Server

                # 等待回應，設定超時
                start_time = time.time()
                while not self.ws_client.cmb_msg and time.time() - start_time < 2:
                    await asyncio.sleep(0.1)

                # print(f"(CMB) {self.ws_client.cmb_msg}")
                response = f"{self.ws_client.cmb_msg}"
                self.ws_client.cmb_msg = ''
                return response

            return None
        except Exception as e:
            logging.error(f"handle_message 處理失敗 (錯誤: {e})")


# async def periodic_send_frame(ws_server):
#     """每分鐘發送現有之caller_id"""
#     # Logger.log("每分鐘發送現有之caller_id")
#     while True:
#         disconnect_timeout = 60
#         clients = await client_manager.get_all_clients()
#         print("", flush=True)
#         for caller_id, info in clients.items():
#             try:
#                 # 檢查 disconnect_time 是否為 None
#                 if info['disconnect_time'] is not None:
#                     last_update = int(
#                         ((datetime.now() - info['disconnect_time']).total_seconds()) / 60)
#                     if last_update >= disconnect_timeout:
#                         logging.info(
#                             f"離線{disconnect_timeout}分鐘,移除Client連線!: {caller_id}")
#                         await client_manager.remove_client(caller_id)
#             except Exception as e:
#                 logging.error(f"移除離線超時之Client連線時發生錯誤: {e}")

#         print("", flush=True)
#         Logger.log("發送例行資料:")
#         active_client = 0
#         connected_client = 0
#         clients = await client_manager.get_all_clients()
#         for caller_id, info in clients.items():
#             try:
#                 # 檢查 messages 是否存在
#                 if 'messages' not in info or 'message' not in info['messages']:
#                     # logging.info(f" {caller_id} messages 不存在")
#                     continue
#                 message_parts = info['messages']['message'].split(',')
#                 # 如果 call_num == 0 則不傳送
#                 # if message_parts[2] == '0':
#                 #     print(
#                 #         f"{caller_id}資料無效({message_parts[2]}) ", end='', flush=True)
#                 #     continue
#                 # print(f'message_parts[1]: {message_parts[1]}')
#                 data = {
#                     "vendor_id": "tawe",
#                     "caller_id": caller_id,
#                     "call_num": message_parts[2],
#                     "change": False,
#                     "last_update": 0
#                 }
#                 # if message_parts[1]=='ping':
#                 #     print(f'{caller_id}: message_parts[1]: {message_parts[1]}, data["change"]: {data["change"]}')
#                 last_update = 0
#                 # 檢查 disconnect_time 是否為 None
#                 if info['disconnect_time'] is not None:
#                     last_update = int(
#                         ((datetime.now() - info['disconnect_time']).total_seconds()) / 60) + 1
#                     # 確保 last_update 不超過 10
#                     data["last_update"] = min(last_update, 10)
#                     data["change"] = True
#                 json_data = json.dumps(data, indent=2)
#                 # Logger.log(f"發送例行資料: {json_data}")
#                 # Logger.log(f'發送例行資料: {data["caller_id"]}, {data["call_num"]}, {data["last_update"]}')
#                 if last_update == 0:
#                     connected_client = connected_client + 1
#                 if last_update <= 10:
#                     active_client = active_client + 1
#                     if message_parts[2] == '0':
#                         print(
#                             f"{caller_id}資料無效({message_parts[2]}) ", end='', flush=True)
#                     else:
#                         print(
#                             f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]} ', end='', flush=True)
#                         await ws_server.ws_client.send(json_data)
#             except Exception as e:
#                 logging.error(f"發送例行資料時發生錯誤: {e}")
#         clients = await client_manager.get_all_clients()
#         print("", flush=True)
#         # Logger.log(f"總共有 {len(clients)} 個紀錄中Client")       # 連線中或離線60分鐘內
#         # Logger.log(f"總共有 {active_client} 個有效的Client")       # 連線中或離線10分鐘內
#         # Logger.log(f"總共有 {connected_client} 個連線中Client")   # 連線中
#         Logger.log(
#             f"總共有 {len(clients)} 個紀錄中Client, 總共有 {active_client} 個有效的Client, 總共有 {connected_client} 個連線中Client")
#         print("", flush=True)
#         await asyncio.sleep(60)


async def periodic_send_frame(ws_server):
    """每分鐘發送現有之caller_id"""
    while True:
        start_time = datetime.now()  # 記錄開始時間

        disconnect_timeout = 60
        clients = await client_manager.get_all_clients()
        print("", flush=True)
        for caller_id, info in clients.items():
            try:
                if info['disconnect_time'] is not None:
                    last_update = int(
                        ((datetime.now() - info['disconnect_time']).total_seconds()) / 60)
                    if last_update >= disconnect_timeout:
                        logging.info(
                            f"離線{disconnect_timeout}分鐘,移除Client連線!: {caller_id}")
                        await client_manager.remove_client(caller_id)
            except Exception as e:
                logging.error(f"移除離線超時之Client連線時發生錯誤: {e}")

        print("", flush=True)
        Logger.log("發送例行資料:")
        active_client = 0
        connected_client = 0
        clients = await client_manager.get_all_clients()
        for caller_id, info in clients.items():
            try:
                if 'messages' not in info or 'message' not in info['messages']:
                    continue
                message_parts = info['messages']['message'].split(',')
                data = {
                    "vendor_id": "tawe",
                    "caller_id": caller_id,
                    "call_num": message_parts[2],
                    "change": False,
                    "last_update": 0
                }
                last_update = 0
                if info['disconnect_time'] is not None:
                    last_update = int(
                        ((datetime.now() - info['disconnect_time']).total_seconds()) / 60) + 1
                    data["last_update"] = min(last_update, 10)
                    data["change"] = True
                json_data = json.dumps(data, indent=2)
                if last_update == 0:
                    connected_client = connected_client + 1
                if last_update <= 10:
                    active_client = active_client + 1
                    if message_parts[2] == '0':
                        print(
                            f"{caller_id}資料無效({message_parts[2]}) ", end='', flush=True)
                    else:
                        print(
                            f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]} ', end='', flush=True)
                        await ws_server.ws_client.send(json_data)
            except Exception as e:
                logging.error(f"發送例行資料時發生錯誤: {e}")
        clients = await client_manager.get_all_clients()
        print("", flush=True)
        Logger.log(
            f"總共有 {len(clients)} 個紀錄中Client, 總共有 {active_client} 個有效的Client, 總共有 {connected_client} 個連線中Client")
        print("", flush=True)

        end_time = datetime.now()  # 記錄結束時間
        execution_time = (end_time - start_time).total_seconds()  # 計算執行時間
        sleep_time = max(60 - execution_time, 0)  # 計算剩餘的睡眠時間
        await asyncio.sleep(sleep_time)  # 確保總間隔時間為60秒


def get_platform_config():
    """判斷 platform 並返回相應配置"""
    os_name = platform.system()
    PORT = 8765
    if os_name == 'Windows':
        PORT = 38000
        # return PORT, "ws://localhost:8088", 'Windows'      # Local WIndows PC
        return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Windows'  # CMB Trying
        # return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Windows'  # CMB Live
        # return PORT, "ws://35.185.131.62:4000", 'Windows'  # Jando VM
        # return PORT, "ws://cmb-front-end.callmeback.com.tw:4000", 'Windows'  # 勿用,測試轉址用，已關閉
        # return PORT, "ws://cmb-front-end.callmeback.com.tw:8765", 'Windows'  # 勿用,測試轉址至 cmb-caller-frontend.py

    if os_name == 'Linux':
        if 'K_SERVICE' in os.environ:
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
                return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Compute_Engine'
        except:
            pass
        return PORT, "ws://localhost:8088", 'Linux'
    return PORT, "ws://localhost:8088", 'Unknown'


async def main():
    """主程式入口"""
    try:
        print(".\n", flush=True)
        print(".\n", flush=True)
        print(".\n", flush=True)
        logging.info(
            f"***** cmb-caller-frontend {VER} (GCE & GCR) 開始運行! *****")
        print(".\n", flush=True)
        print(".\n", flush=True)

        port, ws_url, platform_name = get_platform_config()
        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')
        if platform_name == 'Cloud_Run':
            CREDENTIALS, PROJECT_ID = default()
            print(f"CREDENTIALS: {CREDENTIALS}, Project ID: {PROJECT_ID}", flush=True)
            if PROJECT_ID == 'callme-398802':
                ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"  # CMB Live
                logging.info("CMB Live Server!")
            else:
                logging.info("CMB Trial Server!")

        # 初始化並啟動 WebSocket Client
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
