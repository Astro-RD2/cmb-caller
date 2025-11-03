'''
websockets 14 板以上有相容性問題
pip uninstall websockets -y
pip install websockets==13.1
pip show websockets
'''

'''
2025/03/03 傳送至 sever 之 call_num 由 string 改為 int
'''

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
nest_asyncio.apply()

VER = "2025031313"

class Logger:
    @staticmethod
    def log(message):
        """顯示帶時間戳的狀態訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{timestamp} {message}")

def setup_logger(log_to_console=True, log_to_file=True, log_level=logging.DEBUG, max_bytes=5*1000*1024, backup_count=1):
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_file = f"{script_name}.log"

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    if log_to_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

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
            sorted_clients = dict(sorted(self.clients.items()))
            return sorted_clients

client_manager = ClientManager()

class WebSocketClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws = None
        self.retry_delay = 5

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    self.retry_delay = 5
                    logging.info(f"已連接到 CMB Main Server {self.ws_url}")
                    await self.listen()
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"WebSocket {self.ws_url} 錯誤: {e}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)
            except Exception as e:
                logging.error(f"連接失敗  {self.ws_url} : {e}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)

    async def listen(self):
        try:
            async for message in self.ws:
                self.cmb_msg = message
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"WebSocket 連接中斷: {e}")
            raise e

    async def send(self, message):
        if self.ws:
            await self.ws.send(message)

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None

class WebSocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None
        self.server = None
        self.last_num = 0

    async def start(self):
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            max_size=4096,
            compression=None
        )
        logging.info(f"WebSocket Server已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handler(self, websocket, path):
        try:
            async for message in websocket:
                if message == 'ping':
                    return

                caller_id, ping, call_num = self.parse_message(message)
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
            clients = await client_manager.get_all_clients()
            if caller_id in clients:
                print("", flush=True)
                logging.info(f"Client連線斷開: {caller_id}, {e}")
                await client_manager.update_client(caller_id, 'disconnect_time', datetime.now())

    async def on_message(self, caller_id, message, websocket, new_client):
        try:
            print(f'  收:{message} ', end='', flush=True)
            caller_id, ping, call_num = self.parse_message(message)
            client_msg = (f'{caller_id},{ping},{call_num}')
            clients = await client_manager.get_all_clients()
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
                    if (ping != 'ping' and call_num != 0):
                        self.last_num = call_num
                        await websocket.send(f'OK, {caller_id}')
                        await self.handle_message(caller_id, call_num)
                    elif (ping != 'ping' and call_num == 0):
                        print(f'\n', end='', flush=True)
                        logging.info(f"Websocket 連線資訊 {message}")
                        await websocket.send(f'OK, {caller_id}')
                    elif ping == 'ping':
                        await websocket.send('pong')
                    else:
                        pass
        except Exception as e:
            logging.error(f"訊息處理失敗 (錯誤: {e})")

    def parse_message(self, message):
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
        try:
            data = {
                "vendor_id": self.vendor_id,
                "caller_id": caller_id,
                "call_num": call_num,
                "change": True,
                "last_update": 0
            }

            json_data = json.dumps(data, indent=2)
            if self.ws_client:
                await self.ws_client.send(json_data)

                start_time = time.time()
                while not self.ws_client.cmb_msg and time.time() - start_time < 2:
                    await asyncio.sleep(0.1)

                response = f"{self.ws_client.cmb_msg}"
                self.ws_client.cmb_msg = ''
                return response

            return None
        except Exception as e:
            logging.error(f"handle_message 處理失敗 (錯誤: {e})")

async def periodic_send_frame(ws_server):
    while True:
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
        await asyncio.sleep(60)

def get_platform_config():
    os_name = platform.system()

    if os_name == 'Windows':
        return 38000, "ws://cmb-front-end.callmeback.com.tw:8765", 'Windows'
    
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
        return 8765, "ws://localhost:8080", 'Linux'
    return 8765, "ws://localhost:8080", 'Unknown'

'''
async def main():
    try:
        logging.info(f"cmb-caller-frontend 開始運行 {VER}")

        port, ws_url, platform_name = get_platform_config()
        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')

        ws_client = WebSocketClient(ws_url)
        asyncio.create_task(ws_client.connect())

        ws_server = WebSocketServer('0.0.0.0', port)
        ws_server.ws_client = ws_client
        ws_server_task = asyncio.create_task(ws_server.start())

        periodic_task = asyncio.create_task(periodic_send_frame(ws_server))

        while True:
            await asyncio.sleep(2)

    except Exception as e:
        logging.error(f"致命錯誤: {e}")
    finally:
        logging.error("cmb-caller-frontend 結束")
        await ws_server.stop()
        await ws_client.close()
        ws_server_task.cancel()
        periodic_task.cancel()
'''

async def main():
    try:
        logging.info(f"cmb-caller-frontend 開始運行 {VER}")

        # 從環境變數中獲取端口，如果未設置則使用默認值 8080
        PORT = int(os.environ.get("PORT", 8080))
        # ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"
        ws_url = "wss://callnum-receiver-306511771181.asia-east1.run.app/"  # CMB Trying
        #ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"  # CMB Live
        
        platform_name = "Cloud_Run"

        logging.info(
            f'platform: {platform_name}, port: {PORT}, WebSocket URL: {ws_url}')

        ws_client = WebSocketClient(ws_url)
        asyncio.create_task(ws_client.connect())

        ws_server = WebSocketServer('0.0.0.0', PORT)
        ws_server.ws_client = ws_client
        ws_server_task = asyncio.create_task(ws_server.start())

        periodic_task = asyncio.create_task(periodic_send_frame(ws_server))

        while True:
            await asyncio.sleep(2)

    except Exception as e:
        logging.error(f"致命錯誤: {e}")
    finally:
        logging.error("cmb-caller-frontend 結束")
        await ws_server.stop()
        await ws_client.close()
        ws_server_task.cancel()
        periodic_task.cancel()




if __name__ == '__main__':
    setup_logger(log_to_console=True, log_to_file=True, log_level=logging.INFO)
    asyncio.run(main())