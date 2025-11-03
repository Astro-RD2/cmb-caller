
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
'''

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
import nest_asyncio
from google.auth import default
import traceback
nest_asyncio.apply()

VER = "2025042310"


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

    async def remove_client(self, caller_id):
        async with self.lock:
            if caller_id in self.clients:
                del self.clients[caller_id]

    async def add_connection(self, caller_id, websocket):
        """添加一個新的WebSocket連接到指定caller_id"""

        clients = await client_manager.get_all_clients()
        # print(f'add_connection clients:{clients}')
        # 取得 caller_id 的 caller_num，如果不存在則預設 0，並確保是 int
        existing_num = clients.get(caller_id, {}).get('caller_num', 0)
        caller_num = int(existing_num)  # 確保是 int
        # print(f'add_connection caller_num:{caller_num}')

        async with self.lock:
            if caller_id not in self.clients:
                self.clients[caller_id] = {
                    'connections': set(),
                    # 'caller_num': 0,
                    'caller_num': caller_num,
                    'caller_name': '',
                    'connect_time': datetime.now(),
                    'disconnect_time': None
                }
            self.clients[caller_id]['connections'].add(websocket)
            self.clients[caller_id]['disconnect_time'] = None
        # clients = await client_manager.get_all_clients()
        # print(f'add_connection_1 clients:{clients}')

    async def remove_connection(self, caller_id, websocket):
        """從指定caller_id移除一個WebSocket連接"""
        async with self.lock:
            if caller_id in self.clients:
                print(f'discard(websocket):{caller_id}', end='\n', flush=True)
                self.clients[caller_id]['connections'].discard(websocket)
                # 如果沒有連接了，記錄斷開時間
                if not self.clients[caller_id]['connections']:
                    print(f'記錄斷開時間:{caller_id}', end='\n',
                          flush=True)      # !!!@@@
                    self.clients[caller_id]['disconnect_time'] = datetime.now()

    async def update_caller_info(self, caller_id, caller_num=None, caller_name=None):
        """更新caller的號碼或名稱"""
        async with self.lock:
            if caller_id in self.clients:
                if caller_num is not None:
                    self.clients[caller_id]['caller_num'] = caller_num
                    # print(
                    #     f"update_caller_info set clients[{caller_id}][{caller_num}] = {caller_num}")

    async def notify_clients(self, caller_id, message):
        """通知指定caller_id的所有連接"""
        # print(f'notify_clients:{caller_id},{message} ', end='', flush=True)
        async with self.lock:
            # print('na ', end='', flush=True)
            if caller_id in self.clients:
                # print('nb ', end='', flush=True)
                disconnected = set()
                # print(f'clients:{self.clients}')
                for websocket in self.clients[caller_id]['connections']:
                    # print('nc ', end='', flush=True)
                    try:
                        if websocket.open:
                            # print('nd ', end='', flush=True)
                            # EX: v0005,696,update
                            # logging.info(f"通知客戶端:{message}")
                            await websocket.send(message)
                        else:
                            # print('ne ', end='', flush=True)
                            logging.info("add(websocket)")
                            disconnected.add(websocket)
                    except Exception as e:
                        print('nf ', end='', flush=True)
                        logging.error(f"通知客戶端失敗: {e}")
                        traceback.print_exc()
                        disconnected.add(websocket)

                # 移除已斷開的連接
                for ws in disconnected:
                    print(f'移除已斷開的連接:{caller_id}', end='\n', flush=True)
                    self.clients[caller_id]['connections'].discard(ws)

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

    async def get_all_clients(self):
        """獲取所有客戶端資訊"""
        async with self.lock:
            return {k: v for k, v in sorted(self.clients.items())}


client_manager = ClientManager()


# 連結 CMB Main Server
class WebSocketClient:
    def __init__(self, ws_url):
        """初始化 WebSocket Client"""
        print("初始化 WebSocket Client")
        self.ws_url = ws_url
        self.cmb_msg = ''
        self.ws = None  # CMB Main Server
        self.retry_delay = 5

    async def connect(self):
        while True:
            try:
                # async with websockets.connect(
                #     self.ws_url,
                #     ping_interval=15,  # 客戶端也發送 ping
                #     ping_timeout=5,
                # ) as ws:

                async with websockets.connect(
                    self.ws_url,
                    ping_interval=30,  # 從 15 秒增加到 30 秒
                    ping_timeout=10,   # 從 5 秒增加到 10 秒
                ) as ws:

                    self.ws = ws
                    self.retry_delay = 5
                    logging.info(f"已連接到 CMB Main Server {self.ws_url}")
                    await self.listen()
            except websockets.exceptions.ConnectionClosed as e:
                logging.error(
                    f"CMB Main Server 連接關閉，代碼: {e.code}, 原因: {e.reason}")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 60)

            except Exception as e:
                logging.error(f"CMB Main Server 未知錯誤: {e}")
                await asyncio.sleep(self.retry_delay)

    async def listen(self):
        """處理接收到的訊息"""
        try:
            async for message in self.ws:
                # Logger.log(f"收到(CMB): {message}")
                self.cmb_msg = message

                if not is_json(message):
                    # return
                    continue  # 改為 continue 而不是 return *****

                parsed_message = json.loads(message)
                if isinstance(parsed_message, dict):
                    if parsed_message.get("action") == "new_get_num":
                        print(f'got new_get_num:{parsed_message}')
                        # caller_id = parsed_message.get("caller_id")
                        caller_id = parsed_message.get(
                            "caller_id", "").lower()     # 轉換為小寫
                        new_num = parsed_message.get("curr_num")
                        print(
                            f'notify_clients:{caller_id},OK,{caller_id},{new_num},new_get_num')
                        await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},new_get_num')
                else:
                    print(f'Unexpected message format: {parsed_message}')

                    # _manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update')

        # except websockets.exceptions.ConnectionClosedError as e:
        #     logging.error(f"CMB Main Server 連接中斷: {e}")
        #     # traceback.print_exc()
        #     raise e  # 重新引發異常以便重新連接
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"CMB Main Server 連接中斷: {e}")
            # 在重新拋出異常前添加小延遲
            await asyncio.sleep(2)  # 等待 2 秒後再重新連接
            raise e

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


def is_json(my_string):
    try:
        json.loads(my_string)
        return True
    except ValueError:
        return False

# cmb-caller-frontend WebSocket Server, 連結 Caller


class WebSocketServer:
    def __init__(self, host, port):
        """初始化 WebSocket Server"""
        self.host = host
        self.port = port
        self.vendor_id = "tawe"
        self.ws_client = None   # 連結 CMB Main Server
        self.server = None      # 連結 Caller
        self.last_num = 0
        self.auth_lock = asyncio.Lock()

    async def start(self):
        """啟動Server"""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,      # xx 秒，減少資源消耗
            ping_timeout=10,       # xx 秒，給予寬裕的回應時間
            max_size=4096,        # 限制訊息大小，避免記憶體問題
            compression=None       # ESP32 不需要壓縮，可提高效能
        )
        logging.info(
            f"cmb-caller-frontend WebSocket Server 已啟動: ws://{self.host}:{self.port}")
        await self.server.wait_closed()  # 保持Server運行

    async def stop(self):
        """停止Server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handler(self, websocket, path):
        """處理新Client連接"""
        new_connect = True
        executed_remove = False
        response_auth = False
        # print("處理新Client連接")
        caller_id = None
        try:
            await asyncio.sleep(1)
            async for message in websocket:  # 迴圈
                # print("處理新Client連接_1")

                # 解析訊息
                caller_id, m_cmd, m_info = self.parse_message(message)

                if new_connect:
                    new_connect = False
                    print(f'新Client連接:{caller_id},{m_cmd},{m_info}')

                # if m_cmd == 'ping':
                #     await websocket.send('pong')
                #     continue

                # 印出資訊
                if m_cmd == 'send' or m_cmd == 'auth' or m_cmd == 'get_num_info' or m_cmd == 'info':
                    if m_info != '':
                        print(f' 收:{caller_id},{m_cmd},{m_info} ',
                              end='', flush=True)
                    else:
                        print(f' 收:{caller_id},{m_cmd} ', end='', flush=True)

                # 處理驗證
                if m_cmd == 'auth':
                    # new_connect = False
                    # await self.handle_auth(caller_id, message.split(','), websocket)
                    response_auth = await self.handle_auth(caller_id, message.split(','), websocket)
                    continue

                # 檢查是否已驗證
                clients = await client_manager.get_all_clients()
                if caller_id not in clients:
                    # if caller_id.startswith('a0') or caller_id.startswith('z'):
                    if caller_id.startswith('z'):
                        print(f"*** 代加入授權! {caller_id},{m_cmd},{m_info} ***")
                        message_x = f'{caller_id},AUTH,liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='
                        response_auth = await self.handle_auth(caller_id, message_x.split(','), websocket)
                    else:
                        logging.info(f"未授權操作:{caller_id},{m_cmd},{m_info}")
                        await websocket.send("Fail,003,未授權操作")
                        continue

                if not response_auth:
                    # if caller_id.startswith('a0') or caller_id.startswith('z'):
                    if caller_id.startswith('z'):
                        print(f"*** 代加入授權!! {caller_id},{m_cmd},{m_info} ***")
                        message_x = f'{caller_id},AUTH,liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='
                        response_auth = await self.handle_auth(caller_id, message_x.split(','), websocket)
                    else:
                        logging.info(f"未授權操作:{caller_id},{m_cmd},{m_info}")
                        await websocket.send("Fail,003,未授權操作.")
                        continue

                # 處理其它指令

                # if new_connect:
                #     new_connect = False
                #     # 不應幫加入，須由 auth 加入
                #     print(f"加入新websocket! {caller_id},{m_cmd},{m_info}")
                #     await client_manager.add_connection(caller_id, websocket)

                if m_cmd == 'ping':
                    # print(f'ping:{caller_id},{m_cmd},{m_info}')
                    await websocket.send('pong')
                    existing_num = clients.get(
                        caller_id, {}).get('caller_num', 0)
                    current_num = int(existing_num)  # 確保是 int
                    # if (current_num == 0 and int(m_info) != 0):
                    if current_num == 0 and m_info.isdigit() and int(m_info) != 0:
                        print(f'set caller_num: {caller_id}:{int(m_info)}')
                        clients[f'{caller_id}']['caller_num'] = int(m_info)
                    continue

                if m_cmd == 'info':
                    await websocket.send(f'OK,{caller_id},info')
                    continue

                # 取得 '取號資訊'
                if m_cmd == 'get_num_info':
                    await self.handle_get_num_info(caller_id, message.split(','), websocket)
                    continue

                if m_cmd == 'get':
                    # 獲取當前號碼
                    # clients = await client_manager.get_all_clients()
                    # print(f'get clients:{clients}')
                    # existing_num = clients.get(
                    #     caller_id, {}).get('caller_num', 0)
                    # current_num = int(existing_num)  # 確保是 int
                    current_num = await client_manager.get_caller_num(caller_id)
                    # print(f'get current_num:{current_num}')
                    await websocket.send(f'OK,{caller_id},{current_num},get')
                    continue

                if m_cmd == 'send' or (m_cmd == '' and m_info != '0'):
                    # 更新號碼並通知所有客戶端

                    # if m_info != '':
                    #     print(f'send? 收:{caller_id},{m_cmd},{m_info} ',
                    #           end='', flush=True)
                    # else:
                    #     print(f'send? 收:{caller_id},{m_cmd} ',
                    #           end='', flush=True)

                    new_num = int(m_info)
                    # print('send: ', end='', flush=True)
                    await client_manager.update_caller_info(caller_id, new_num)
                    # print(f" 發:OK,{caller_id},{new_num},send ",
                    #       end='', flush=True)
                    await websocket.send(f'OK,{caller_id},{new_num},send')

                    await client_manager.notify_clients(caller_id, f'OK,{caller_id},{new_num},update')

                    # 通知CMB主伺服器
                    await self.handle_message(caller_id, new_num)
                    continue

                print(f"錯誤的命令! {caller_id},{m_cmd},{m_info}")
                await websocket.send(f'OK,{caller_id},{self.last_num},{m_cmd}')

        except websockets.exceptions.ConnectionClosed as e:
            if caller_id:
                await client_manager.remove_connection(caller_id, websocket)
                executed_remove = True
                logging.error(
                    f"客戶端 {caller_id} 斷開，代碼: {e.code}, 原因: {e.reason}")
        except Exception as e:
            logging.error(f"處理客戶端訊息時發生錯誤: {e}")
            traceback.print_exc()
            if caller_id:
                await client_manager.remove_connection(caller_id, websocket)
                executed_remove = True
        finally:
            # print("finally: remove_connection!!!")
            # if caller_id:
            if caller_id and not executed_remove:
                # 確保清理
                # print(f"finally:{caller_id},{clients[caller_id]['connections']}") # KeyError: 'v0005'
                await client_manager.remove_connection(caller_id, websocket)
            # print(f"finally: PASS remove_connection!!!")

    async def handle_get_num_info(self, caller_id, parts, websocket):
        async with self.auth_lock:  # 使用鎖來確保一次只有一個驗證過程
            if len(parts) != 2:
                logging.info("無效的 get_num_info 格式!")
                await websocket.send("Fail,006,無效的CMD指令")
                return

            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                login_data = {
                    "action": "get_num_info",         # 動作指令
                    "vendor_id": self.vendor_id,      # 叫號機廠商 id
                    "caller_id": caller_id,           # 叫號機 id
                }

                if self.ws_client:
                    try:
                        await self.ws_client.send(json.dumps(login_data))
                        # 等待回應
                        start_time = time.time()
                        self.ws_client.cmb_msg = ''
                        while not self.ws_client.cmb_msg and time.time() - start_time < 10:
                            await asyncio.sleep(0.1)

                        if self.ws_client.cmb_msg:
                            response = json.loads(self.ws_client.cmb_msg)
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
                                await websocket.send(f"OK,{caller_id},{curr_get_num},{wait_num},get_num_info")
                                self.ws_client.cmb_msg = ''
                                return
                            else:
                                # 處理錯誤回應
                                code = response.get("result").split(
                                    ',')[1].split(':')[0].strip()
                                msg_map = {
                                    '003': '007,不支援此功能',
                                    '002': '002,無效的CallerID',
                                    '001': '006,無效的CMD指令',
                                    '009': '007,文字錯誤/其它'
                                }
                                msg = msg_map.get(code, '001,驗證失敗')
                                await websocket.send(f"Fail,{msg},auth")
                                return

                    except Exception as e:
                        logging.error(
                            f"上層驗證失敗 (嘗試 {attempt+1}/{max_retries}): {e}")
                        traceback.print_exc()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            await websocket.send("Fail,001,不支援此功能,auth")

    async def handle_auth(self, caller_id, parts, websocket):
        """處理驗證請求"""
        async with self.auth_lock:  # 使用鎖來確保一次只有一個驗證過程
            # print(f'{caller_id},處理驗證請求')
            if len(parts) != 3:
                logging.info("無效的驗證格式!")
                await websocket.send("Fail,004,無效的驗證格式")
                return False

            encrypted_password = parts[2]
            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                login_data = {
                    "action": "login",
                    "vendor_id": self.vendor_id,
                    "caller_id": caller_id,
                    "password": encrypted_password
                }

                if self.ws_client:
                    try:
                        # if (encrypted_password == '9QjDqmbgodjbPinUa1BlN5QkqXMB1llYyKQ7BYzFN6g='):    # cmb-caller
                        # ASTRO_cmb-caller
                        if (encrypted_password == 'liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='):
                            print(f'\nCMB Caller:{caller_id}')
                            clients = await client_manager.get_all_clients()
                            # print(f'get clients:{clients}')
                            existing_num = clients.get(
                                caller_id, {}).get('caller_num', 0)
                            current_num = int(existing_num)  # 確保是 int
                            # self.ws_client.cmb_msg = f'{{"action":"login","result":"OK","caller_name":"{caller_id}","curr_num":{current_num}}}'
                            self.ws_client.cmb_msg = f'{{"action":"login","result":"OK","caller_name":"{caller_id} caller","curr_num":{current_num}}}'
                            # print(f'handle_auth ws_client.cmb_msg:{self.ws_client.cmb_msg}')
                        else:
                            print(f'\nSOFT CMB Caller:{caller_id}')
                            await self.ws_client.send(json.dumps(login_data))
                            # 等待回應
                            start_time = time.time()
                            self.ws_client.cmb_msg = ''
                            while not self.ws_client.cmb_msg and time.time() - start_time < 20:
                                await asyncio.sleep(0.1)

                        if self.ws_client.cmb_msg:
                            response = json.loads(self.ws_client.cmb_msg)
                            print(f'auth response:{response}')
                            if response.get("result") == "OK":
                                # 驗證成功
                                await client_manager.add_connection(caller_id, websocket)
                                # print('auth: ', end='', flush=True)
                                await client_manager.update_caller_info(
                                    caller_id,
                                    # caller_num=response.get('curr_num', 0),
                                    # !!!@@@
                                    caller_num=await client_manager.get_caller_num(caller_id),
                                    caller_name=response.get('caller_name', '')
                                )
                                print(f'{caller_id},驗證成功')
                                await websocket.send(f"OK,{response.get('caller_name','')},auth")
                                self.ws_client.cmb_msg = ''
                                return True
                            else:
                                # 處理錯誤回應
                                code = response.get("result").split(
                                    ',')[1].split(':')[0].strip()
                                msg_map = {
                                    '003': '001,驗證失敗',
                                    '002': '002,無效的CallerID',
                                    '001': '006,無效的CMD指令',
                                    '009': '007,文字錯誤/其它'
                                }
                                msg = msg_map.get(code, '001,驗證失敗')
                                print(f'{caller_id},{msg}')
                                await websocket.send(f"Fail,{msg},auth")
                                return False

                    except Exception as e:
                        logging.error(
                            f"上層驗證失敗 (嘗試 {attempt+1}/{max_retries}): {e}")
                        traceback.print_exc()
                        print(
                            f'self.ws_client.cmb_msg:{self.ws_client.cmb_msg}')
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
            await websocket.send("Fail,001,驗證失敗,auth")
            return False

    async def force_close_connection(self, websocket, caller_id, reason):
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

    def parse_message(self, message):       # m_cmd 一律變為小寫
        """解析接收到的訊息"""
        message = message.lower()
        info = ""
        m_cmd = ""
        try:
            parts = message.split(',')
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

    async def handle_message(self, caller_id, call_num):
        """處理訊息並生成回應"""
        call_num = int(call_num)
        while True:
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
                    # Logger.log(f"\n發送訊息至 CMB: {json_data}")
                    # Logger.log(f"發送訊息至 CMB: {caller_id}, {call_num}")
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
                logging.error(
                    f"handle_message 處理失敗 (錯誤: {e}), {caller_id}, {call_num}")
                # print('失敗後等待10秒再重試!!!')
                print("10秒後繼續發送資料!!!", flush=True)
                # traceback.print_exc()
                await asyncio.sleep(10)  # 失敗後等待10秒再重試
                print("繼續發送資料!!!", flush=True)


async def periodic_send_frame(ws_server):
    """定期發送狀態和清理無效連接"""
    await asyncio.sleep(30)
    while True:
        start_time = datetime.now()

        # 清理無效連接
        await client_manager.cleanup()

        # 發送狀態更新
        clients = await client_manager.get_all_clients()
        active_client = 0
        connected_client = 0
        print("", flush=True)
        Logger.log("發送例行資料:")
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

                    # 發送更新到CMB主伺服器
                    data = {
                        "vendor_id": "tawe",
                        "caller_id": caller_id,
                        "call_num": info['caller_num'],
                        "change": not is_connected,
                        "last_update": 0 if is_connected else (int((datetime.now() - info['disconnect_time']).total_seconds() / 60)+1)
                    }

                    if info['caller_num'] == '0':
                        print(
                            f"{caller_id}資料無效(info['caller_num']) ", end='', flush=True)
                    else:
                        print(
                            f'{data["caller_id"]},{data["call_num"]},{data["change"]},{data["last_update"]} ', end='', flush=True)
                    await ws_server.ws_client.send(json.dumps(data))

            except Exception as e:
                logging.error(f"發送例行資料時出錯: {e}")
                print("10秒後繼續發送例行資料!!!", flush=True)
                # traceback.print_exc()
                start_time = datetime.now() - timedelta(seconds=(60-10)
                                                        )     # 出錯後將 start_time 設為xx秒前
                break   # 離開 for 迴圈

        print("", flush=True)
        # 記錄狀態
        # print(f'記錄狀態 clients:{clients}')
        total_websockets = sum(len(client['connections'])
                               for client in clients.values())
        Logger.log(
            f"總共有 {len(clients)} 個紀錄中 ID, "
            f"{active_client} 個有效的 ID, "
            f"{connected_client} 個連線中 ID, "
            f"{total_websockets} 個連線中 Client"
        )

        # 確保每60秒執行一次
        execution_time = (datetime.now() - start_time).total_seconds()
        await asyncio.sleep(max(60 - execution_time, 0))


def get_platform_config():
    """判斷 platform 並返回相應配置"""
    os_name = platform.system()
    PORT = 8765
    if os_name == 'Windows':
        PORT = 38000
        # return PORT, "ws://localhost:8088", 'Windows'      # Local WIndows PC
        # return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Windows'  # CMB Trying
        return PORT, "wss://callnum-receiver-410240967190.asia-east1.run.app/", 'Windows'  # CMB Live
        # return PORT, "ws://35.185.131.62:4000", 'Windows'  # Jando VM

    if os_name == 'Linux':
        if 'K_SERVICE' in os.environ:
            PORT = int(os.environ.get("PORT", 8080))
            # return PORT, "wss://callnum-receiver-306511771181.asia-east1.run.app/", 'Cloud_Run'  # CMB Trying
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
        await asyncio.sleep(1)
        logging.info(
            f"***** cmb-caller-frontend {VER} (GCE & GCR) 開始執行! *****")
        print(".\n", flush=True)
        print(".\n", flush=True)

        port, ws_url, platform_name = get_platform_config()
        logging.info(
            f'platform: {platform_name}, port: {port}, WebSocket URL: {ws_url}')
        if platform_name == 'Cloud_Run':
            CREDENTIALS, PROJECT_ID = default()
            print(
                f"CREDENTIALS: {CREDENTIALS}, Project ID: {PROJECT_ID}", flush=True)
            if PROJECT_ID == 'callme-398802':
                ws_url = "wss://callnum-receiver-410240967190.asia-east1.run.app/"  # CMB Live
                logging.info("CMB Live Server!")
            else:
                logging.info("CMB Trial Server!")

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
