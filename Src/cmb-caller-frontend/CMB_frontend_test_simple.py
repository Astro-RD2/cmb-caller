'''

此一程式同一時間執行多個，ex:10,是否會有干擾或同步的問題?

windows:
for /L %%i in (1,1,%runCount%) do (
    echo [啟動] 正在啟動第 %%i 個執行個體...
    
    :: 使用唯一的視窗標題啟動Python程序
    start "CMB_Instance_%%i" python CMB_frontend_test_simple.py
   
)

'''



import asyncio
import websockets
import random
from datetime import datetime
import json
import threading
import time
import logging
from typing import List, Dict, Any, Optional
import nest_asyncio
import signal
import sys

# 應用 nest_asyncio 以允許在 Jupyter 等環境中運行
nest_asyncio.apply()

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全域變數
current_number = 0
auth_count = 0
running = True


class WebSocketClient:
    def __init__(self, ws_url: str, client_id: str):
        self.ws_url = ws_url
        self.client_id = client_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.last_value = 0
        self.reconnect = False
        self.listen_task: Optional[asyncio.Task] = None
        self.connect_task: Optional[asyncio.Task] = None
        self.reconnect_delay = 1  # 重連延遲（秒）

    async def connect(self):
        """連接到 WebSocket 伺服器並保持連接"""
        while running:
            try:
                if not self.is_connected:
                    logger.info(f"[{self.client_id}] 嘗試連接到 WebSocket...")
                    self.ws = await websockets.connect(self.ws_url)
                    self.is_connected = True
                    self.reconnect = True
                    self.reconnect_delay = 1  # 重置重連延遲
                    logger.info(f"[{self.client_id}] WebSocket 連接成功")

                    # 啟動監聽任務
                    if self.listen_task is None or self.listen_task.done():
                        self.listen_task = asyncio.create_task(self.listen())
                        logger.debug(f"[{self.client_id}] 啟動消息監聽任務")

                # 保持連接狀態檢查
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"[{self.client_id}] 連接失敗: {e}")
                self.is_connected = False
                await asyncio.sleep(self.reconnect_delay)
                
                # 指數退避策略
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    async def listen(self):
        """處理接收到的消息"""
        global current_number
        
        while self.is_connected and self.ws and running:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                try:
                    message_str = message
                    if isinstance(message, bytes):
                        message_str = message.decode('utf-8')
                    
                    logger.info(f"[{self.client_id}] 接收: {message_str}")
                    
                    # 解析消息
                    if message_str.startswith('{') and message_str.endswith('}'):
                        # JSON 格式消息
                        await self.handle_json_message(message_str)
                    else:
                        # 文本格式消息
                        await self.handle_text_message(message_str)
                        
                except Exception as e:
                    logger.error(f"[{self.client_id}] 消息處理錯誤: {e}")
                    
            except asyncio.TimeoutError:
                # 超時是正常的，繼續迴圈
                continue
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"[{self.client_id}] 連接中斷，嘗試重新連接...")
                self.is_connected = False
                break
            except Exception as e:
                logger.error(f"[{self.client_id}] 接收消息時發生錯誤: {e}")
                self.is_connected = False
                break
                
        logger.info(f"[{self.client_id}] 消息監聽任務結束")

    async def handle_json_message(self, message: str):
        """處理 JSON 格式消息"""
        global current_number
        
        try:
            data = json.loads(message)
            action = data.get("action", "")
            
            if action == "update":
                call_num = data.get("call_num", "")
                if call_num.isdigit():
                    current_number = int(call_num)
                    logger.info(f"更新當前號碼: {current_number}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"[{self.client_id}] JSON 解析錯誤: {e}")

    async def handle_text_message(self, message: str):
        """處理文本格式消息"""
        global current_number
        
        parts = message.split(',')
        if len(parts) >= 2:
            if parts[-1] == 'get' and parts[-2].isdigit():
                current_number = int(parts[-2])
                logger.info(f"獲取當前號碼: {current_number}")
            elif parts[-1] == 'update' and parts[-2].isdigit():
                current_number = int(parts[-2])
                logger.info(f"更新當前號碼: {current_number}")

    async def send_message(self, message: str):
        """發送消息到伺服器"""
        # 重新連接時需要重新認證
        if self.reconnect:
            logger.info(f"[{self.client_id}] 重新連接，需要重新認證")
            self.reconnect = False
            await auth_diff(self)
            await asyncio.sleep(1)

        # 等待連接
        wait_count = 0
        while not self.is_connected and wait_count < 10 and running:
            logger.warning(f"[{self.client_id}] 未連接，等待連接...")
            await asyncio.sleep(2)
            wait_count += 1
        
        if not self.is_connected:
            logger.error(f"[{self.client_id}] 無法連接，消息發送失敗: {message}")
            return

        # 發送消息
        try:
            await self.ws.send(message)
            logger.info(f"[{self.client_id}] 發送: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.error(f"[{self.client_id}] 發送時連接已關閉")
            self.is_connected = False
        except Exception as e:
            logger.error(f"[{self.client_id}] 發送失敗: {e}")
            self.is_connected = False

    def generate_next_value(self):
        """生成下一個號碼"""
        global current_number
        self.last_value = current_number + 1
        
        if self.last_value > 999:
            self.last_value -= 999
            
        logger.debug(f"生成新號碼: {self.last_value}")
        return self.last_value

    async def close(self):
        """關閉連接"""
        self.is_connected = False
        if self.ws:
            await self.ws.close()
        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
        logger.info(f"[{self.client_id}] 連接已關閉")


async def authentication(client: WebSocketClient):
    """使用文本格式進行認證"""
    cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='  # SOFT CMB Caller
    message = f'{client.client_id},AUTH,{cmb_password}'
    await client.send_message(message)
    await asyncio.sleep(1)


async def authentication_json(client: WebSocketClient):
    """使用 JSON 格式進行認證"""
    cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='  # SOFT CMB Caller
    # cmb_password = 'YV7X+xUEsMckopbXpp5s'  # SOFT CMB Caller, BAD

    send_command = {
        "action": "login",
        "vendor_id": "tawe",
        "caller_id": f"{client.client_id}",
        "password": f"{cmb_password}",
        "uuid": hex(id(client))
    }
    message = json.dumps(send_command)
    await client.send_message(message)
    await asyncio.sleep(1)


async def auth_diff(client: WebSocketClient):
    """交替使用兩種認證方式"""
    # global auth_count
    # if auth_count % 2 == 0:
    #     await authentication(client)
    # else:
    #     await authentication_json(client)
    # auth_count += 1

    await authentication_json(client)


def wait_with_timeout(timeout: int = 60):
    """等待用戶輸入或超時"""
    def wait_for_enter(event):
        input()
        event.set()

    event = threading.Event()
    thread = threading.Thread(target=wait_for_enter, args=(event,), daemon=True)
    thread.start()

    print(f"程式暫停中，按 Enter 鍵繼續，或等待 {timeout} 秒自動繼續...")
    
    for remaining in range(timeout, 0, -1):
        if event.is_set():
            break
        print(f"\r剩餘時間：{remaining:2d} 秒  ", end="")
        time.sleep(1)

    print("\n繼續執行程式")



# import time

# import asyncio


async def auth_test(clients: List[WebSocketClient]):
    """認證測試"""
    await asyncio.sleep(5)
    
    for client in clients:
        if client.is_connected:
            client.reconnect = False
            await auth_diff(client)

async def create_clients(ws_url: str, num_clients: int) -> List[WebSocketClient]:
    """創建多個 WebSocket 用戶端"""
    logger.info(f"創建 {num_clients} 個用戶端連接到 {ws_url}")
    
    clients = []
    # for i in range(num_clients):
    #     client_id = f'z{i+1:04d}'  # 示例: z0001, z0002, ...
    #     client_id = 'z0002'
    #     client = WebSocketClient(ws_url, client_id)
    #     clients.append(client)
    #     # 為每個用戶端創建連接任務
    #     client.connect_task = asyncio.create_task(client.connect())
    #     await asyncio.sleep(0.1)  # 稍微延遲以避免同時連接

    client_id = 'z0002'
    # client_id = 'a010p'
    # client_id = 'a010x'
    # client_id = 'z000s'

    
    client = WebSocketClient(ws_url, client_id)
    clients.append(client)
    client.connect_task = asyncio.create_task(client.connect())

    
    return clients


async def shutdown(clients: List[WebSocketClient]):
    """優雅關閉所有用戶端"""
    global running
    running = False
    
    logger.info("正在關閉所有連接...")
    for client in clients:
        await client.close()
    
    # 等待所有任務完成
    await asyncio.sleep(1)
    logger.info("程式關閉完成")


def signal_handler(signum, frame, clients: List[WebSocketClient]):
    """處理信號"""
    logger.info(f"收到信號 {signum}, 正在關閉...")
    asyncio.create_task(shutdown(clients))


async def simulate_client_behavior(clients: List[WebSocketClient], message_interval: int):
    await asyncio.sleep(5)
    print("",flush=True)
    logger.info("開始模擬用戶端行為...")

    loop = asyncio.get_event_loop()
    start_time = loop.time()
    iteration = 0

    if not True:        # 先設 0
        logger.info("先設 0")
        for client in clients:
            if client.is_connected:
                next_value = 0
                send_command = {
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "call_num": f'{next_value}',
                    "change": True,
                    "last_update": 0,
                    "uuid": "JSON_SEND"
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(10)

    while running:
        target_time = start_time + iteration * message_interval

        for client in clients:
            if client.is_connected:
                logger.info(f"\n============== 第 {iteration+1} 次測試 ==============")

                message = f'{client.client_id},get'
                await client.send_message(message)
                await asyncio.sleep(1)

                if True:
                    next_value = client.generate_next_value()
                    send_command = {
                        "vendor_id": "tawe",
                        "caller_id": f"{client.client_id}",
                        "call_num": f'{next_value}',
                        "change": True,
                        "last_update": 0,
                        "uuid": "JSON_SEND"
                    }
                    message = json.dumps(send_command)
                    await client.send_message(message)


                # await asyncio.sleep(1)
                # # 發送命令 get_num_switch, 8. 取號開關：
                # send_command = {
                #     "action": "set_params",
                #     "vendor_id": "tawe",
                #     "caller_id": f"{client.client_id}",
                #     "params": {"get_num_max": "15"},
                #     "uuid": hex(id(client))
                # }
                # message = json.dumps(send_command)
                # await client.send_message(message)
                # await asyncio.sleep(1)



        iteration += 1
        adj = 0
        adj = message_interval * (random.uniform(-0.1, 0.1))
        now = loop.time()
        sleep_time = max(0, target_time + message_interval - now + adj)     # 讓時間前後變動
        print(f"Sleep {sleep_time:.3f} Sec")
        await asyncio.sleep(sleep_time)


async def main():
    """主函數"""
    global running
    
    # WebSocket 伺服器地址
    ws_urls = {
        "local": "ws://localhost:38000",
        "trial": "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/",
        "live": "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"
    }
    
    # 選擇伺服器
    target_env = "local"
    target_env = "trial"
    target_env = "live"
    
    # 檢查是否有命令列參數
    if len(sys.argv) > 1:
        param = sys.argv[1].lower()
        if param in ws_urls:
            target_env = param
            logger.info(f"從參數取得 '{param}'，使用對應的 WebSocket URL。")
            logger.info(f"使用 '{target_env}'。")
        else:
            logger.warning(f"無效的參數 '{param}'。將使用預設值 '{target_env}'。")
    else:
        logger.info(f"未提供參數，使用預設值 '{target_env}'。")
    
    ws_url = ws_urls[target_env]
    logger.info(f"程式啟動，連接到: {ws_url}")


    # 配置參數
    message_interval = 60  # 消息間隔（秒）- 縮短以便測試
    num_clients = 1        # 用戶端數量
    
    # 創建用戶端
    clients = await create_clients(ws_url, num_clients)
    
    # 註冊信號處理
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: signal_handler(s, f, clients))
    
    try:
        # 等待用戶端連接
        await asyncio.sleep(3)
        
        # 檢查連接狀態
        connected_clients = [client for client in clients if client.is_connected]
        if not connected_clients:
            logger.error("沒有用戶端成功連接，程式退出")
            return
        
        logger.info(f"成功連接 {len(connected_clients)} 個用戶端")
        
        # 運行測試
        await auth_test(connected_clients)
        
        # 開始模擬用戶端行為
        # behavior_task = asyncio.create_task(simulate_client_behavior(connected_clients, message_interval))
        asyncio.create_task(simulate_client_behavior(connected_clients, message_interval))
        
        # 保持程式運行
        while running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("程式被使用者中斷")
    except Exception as e:
        logger.error(f"程式運行錯誤: {e}")
    finally:
        await shutdown(clients)





if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程式被使用者中斷")
    except Exception as e:
        logger.error(f"程式運行錯誤: {e}")

    

    
