'''
websockets 14 板以上有相容性問題
pip uninstall websockets -y
pip install websockets==13.1
pip show websockets

'''



import time
from datetime import datetime
import platform
import os
import requests
import json
import asyncio
import websockets
# import random
# from typing import Optional, List
import logging
from logging.handlers import RotatingFileHandler


class Logger:
    @staticmethod
    def log(message):
        """顯示帶時間戳的狀態訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{timestamp} {message}")


def setup_logger(log_to_console=True, log_to_file=True, log_level=logging.DEBUG, max_bytes=1000*1024, backup_count=1):
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
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Create a formatter and set it for all handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
            return self.clients


client_manager = ClientManager()


# 連結 CMB Server
class WebSocketClient:
    def __init__(self, ws_url):
        """初始化 WebSocket 客戶端"""
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws = None  # CMB Server
        self.retry_delay = 5

    async def connect(self):
        """設置 WebSocket 連接"""
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    self.retry_delay = 5  # 重置重試延遲
                    logging.info(f"已連接到 CMB 伺服器 {self.ws_url}")
                    await self.listen()
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"WebSocket 錯誤: {e}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)  # 最大延遲 60 秒
            except Exception as e:
                logging.error(f"連接失敗: {e}")
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
        """初始化 WebSocket 伺服器"""
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None   # 連結 CMB Server
        self.server = None      # 連結 Caller

    async def start(self):
        """啟動伺服器"""
        self.server = await websockets.serve(self.handler, self.host, self.port)
        logging.info(f"WebSocket 伺服器已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()  # 保持伺服器運行

    async def stop(self):
        """停止伺服器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handler(self, websocket, path):
        """處理新客戶端連接"""
        try:
            async for message in websocket:
                # 解析訊息內容
                if message == 'ping':
                    return
                caller_id, call_num = self.parse_message(message)

                # 檢查 caller_id 是否存在於 client_manager 中
                clients = await client_manager.get_all_clients()

                if caller_id not in clients:
                    client_info = {
                        'connect_time': datetime.now(),
                        'disconnect_time': None,
                        'ip': websocket.remote_address[0],
                        'port': websocket.remote_address[1],
                        'messages': []
                    }
                    await client_manager.add_client(caller_id, client_info)
                    # logging.info(f"新客戶端 {caller_id}, {client_info} 已連接")
                    print()
                    logging.info(f"新客戶端 {caller_id} 已連接")

                # 處理訊息
                await self.on_message(caller_id, message, websocket)
        except websockets.exceptions.ConnectionClosedError as e:
            logging.info(f"客戶端連線斷開:  {caller_id}, {e}")
            clients = await client_manager.get_all_clients()
            if caller_id in clients:
                await client_manager.update_client(caller_id, 'disconnect_time', datetime.now())
                # await asyncio.sleep(60 * 60)  # 保留斷線資料1小時
                await asyncio.sleep(24 * 60 * 60)  # 保留斷線資料24小時
                await client_manager.remove_client(caller_id)

    async def on_message(self, caller_id, message, websocket):
        """處理接收到的訊息"""
        try:
            # Logger.log(f"收到(Caller {caller_id}): {message}")
            print(f'  收:{message} ', end='', flush=True)
            clients = await client_manager.get_all_clients()
            # clients[caller_id]['messages'].append(
            #     {'timestamp': datetime.now(), 'message': message})
            # 置換而不是追加 'messages'
            clients[caller_id]['messages'] = {
                'timestamp': datetime.now(), 'message': message}
            if clients[caller_id]['disconnect_time'] != None:
                clients[caller_id]['disconnect_time'] = None
                clients[caller_id]['connect_time'] = datetime.now()
                print()
                logging.info(f"舊客戶端 {caller_id} 重新連接")

            caller_id, call_num = self.parse_message(message)

            # CMB Server 回覆有與client對應不上的問提，暫不使用
            if True:
                if websocket.open:
                    print(f'  發:{caller_id}, OK, {caller_id} ', end='', flush=True)
                    await websocket.send(f'OK, {caller_id}')
                await self.handle_message(caller_id, call_num, caller_id)
            else:
                response = await self.handle_message(caller_id, call_num, caller_id)
                if response:
                    # Logger.log(f"發送(Caller {caller_id}): {response}")
                    print(f'  發:{caller_id},(CMB) {response} ', end='', flush=True)
                    await websocket.send(f'(CMB) {response}')

        except Exception as e:
            logging.error(f"訊息處理失敗 (錯誤: {e})")

    def parse_message(self, message):
        """解析接收到的訊息"""
        try:
            parts = message.split(',')
            if len(parts) != 2:
                raise ValueError("訊息格式無效，預期格式為 'caller_id,call_num'")

            caller_id, call_num = parts
            if not call_num.isdigit():
                raise ValueError("呼叫編號必須為數字")

            return caller_id, call_num
        except Exception as e:
            logging.error(f"parse_message 處理失敗 (錯誤: {e})")

    async def handle_message(self, caller_id, call_num, client_id):
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
                await self.ws_client.send(json_data)    # 至 CMB Server

                # 等待回應，設定超時
                start_time = time.time()
                while not self.ws_client.cmb_msg and time.time() - start_time < 2:
                    await asyncio.sleep(0.1)

                clients = await client_manager.get_all_clients()
                # response = f"{clients[client_id]['ip']} {caller_id},{call_num}, (CMB) {self.ws_client.cmb_msg}"
                # print(f"(CMB) {self.ws_client.cmb_msg}")
                response = f"{self.ws_client.cmb_msg}"
                self.ws_client.cmb_msg = ''
                return response

            return None
        except Exception as e:
            logging.error(f"handle_message 處理失敗 (錯誤: {e})")


async def periodic_send_frame(ws_server):
    """每分鐘發送現有之caller_id"""
    # Logger.log("每分鐘發送現有之caller_id")
    while True:
        # Logger.log("每分鐘發送現有之caller_id")
        print()
        Logger.log("發送例行資料:")
        clients = await client_manager.get_all_clients()
        for client_id, info in clients.items():
            try:

                # 檢查 messages 是否存在
                if 'messages' not in info or 'message' not in info['messages']:
                    logging.info(f" {client_id} messages 不存在")
                    continue
                message_parts = info['messages']['message'].split(',')
                data = {
                    "vendor_id": "tawe",
                    "caller_id": client_id,
                    "call_num": message_parts[1] if len(message_parts) > 1 else "xxxx",
                    "change": False,
                    "last_update": 0
                }
                # data["call_num"] = message_parts[1] if len(
                #     message_parts) > 1 else "xxxx"
                # 檢查 disconnect_time 是否為 None
                if info['disconnect_time'] is not None:
                    last_update = int(((datetime.now() - info['disconnect_time']).total_seconds()) / 60 + 1)
                    last_update = min(last_update, 10)  # 確保 last_update 不超過 10
                    data["last_update"] = last_update
                    data["change"] = True
                else:
                    data["last_update"] = 0
                    data["change"] = False
                json_data = json.dumps(data, indent=2)
                # Logger.log(f"client_id, info, {client_id}, {info}")
                # Logger.log(f"發送例行資料: {json_data}")
                # Logger.log(f'發送例行資料: {data["caller_id"]}, {data["call_num"]}, {data["last_update"]}')
                print(f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]} ', end='', flush=True)
                await ws_server.ws_client.send(json_data)
            except Exception as e:
                logging.error(f"發送例行資料時發生錯誤: {e}")
        print()
        await asyncio.sleep(60)


def get_platform_config():
    """判斷 platform 並返回相應配置"""
    os_name = platform.system()

    if os_name == 'Windows':
        return 38000, "ws://localhost:8080", 'Windows'      # Local
        # return 38000, "ws://35.185.131.62:4000", 'Windows'  # Jando VM

    if os_name == 'Linux':
        if 'K_SERVICE' in os.environ:
            return 8765, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Cloud_Run'

        try:
            response = requests.get(
                'http://metadata.google.internal/computeMetadata/v1/',
                timeout=15,
                headers={'Metadata-Flavor': 'Google'}
            )
            if response.status_code == 200:
                return 8765, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Compute_Engine'
        except:
            pass

        # return 38000, "ws://localhost:8080", 'Linux'
        return 8765, "ws://localhost:8080", 'Linux'

    return 8765, "ws://localhost:8080", 'Unknown'


async def main():
    """主程式入口"""
    try:
        logging.info("cmb-caller-frontend 開始運行 2025020609")

        port, ws_url, platform_name = get_platform_config()
        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')

        # 初始化並啟動 WebSocket 客戶端
        ws_client = WebSocketClient(ws_url)
        asyncio.create_task(ws_client.connect())

        # 初始化並啟動 WebSocket 伺服器
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
        await ws_server.stop()  # 停止伺服器
        await ws_client.close()  # 關閉 WebSocket 連接
        ws_server_task.cancel()  # 取消伺服器任務
        periodic_task.cancel()  # 取消定時任務


if __name__ == '__main__':
    # Set up logger to log to both console and file
    # setup_logger(log_to_console=True, log_to_file=True, log_level=logging.DEBUG)
    setup_logger(log_to_console=True, log_to_file=True, log_level=logging.INFO)
    asyncio.run(main())
