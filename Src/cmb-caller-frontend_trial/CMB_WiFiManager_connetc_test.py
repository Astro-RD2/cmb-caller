'''
2025/07/02
WiFi 觀察廣播訊息用!
持續接收訊息版本
'''

import time
import os
import asyncio
import websockets
import random
from datetime import datetime
import json
import uuid

import nest_asyncio
nest_asyncio.apply()

os.environ["PYTHONUNBUFFERED"] = "1"  # 設置為無緩衝模式

msg_count = 0
latest_wifi_status_OK = False  # 新增，用於追蹤是否收到 wifi_get_status OK 回應
current_ssid = 'xxx'


async def authentication(client):
    cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='   # SOFT CMB Caller

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

    req_uuid_1 = str(uuid.uuid4())
    status_request = {
        "action": "wifi_get_status",
        "caller_id": f"{client.client_id}",
        "uuid": req_uuid_1
    }
    await client.send_message(json.dumps(status_request))
    await asyncio.sleep(2)



class WebSocketClient:
    global current_ssid

    def __init__(self, ws_url: str, client_id: str):
        self.ws_url = ws_url
        self.client_id = client_id
        self.ws = None
        self.is_connected = False
        self.last_value = random.randint(1, 999)
        self.reconnect_task = None
        self.reconnect = False
        self.listen_task = None
        self.disconnect_task = None
        self.last_message_json = None  # 追蹤最後一個回應
        self.last_wifi_action = None   # 追蹤最近一次 wifi 相關 action

    async def connect(self):
        while True:
            try:
                if not self.is_connected:
                    self.reconnect = True
                    self.ws = await websockets.connect(self.ws_url)
                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] WebSocket 已連接")
                    if True:
                        print('開始監聽回傳資料', flush=True)
                        self.listen_task = asyncio.create_task(self.listen())
                    self.is_connected = True
                    # 連接成功後立即進行認證
                    await authentication(self)
            except Exception as e:
                print(f"[{self.client_id}] 連接失敗: {e}")
                self.is_connected = False
            await asyncio.sleep(5)  # 連接失敗時等待5秒再重試

    async def listen(self):
        """處理接收到的訊息"""
        global msg_count, latest_wifi_status_OK, current_ssid

        while self.is_connected:
            try:
                async for message in self.ws:
                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [收到訊息] 來源: {self.client_id}, 內容: {message}", flush=True)
                    msg_count += 1
                    # 解析JSON訊息
                    try:
                        msg_json = json.loads(message)
                        self.last_message_json = msg_json
                        if msg_json.get("action") == "wifi_get_status":
                            if msg_json.get("result") == "OK":
                                latest_wifi_status_OK = True
                                current_ssid = msg_json['data']['current_ssid']
                            else:
                                latest_wifi_status_OK = False
                    except Exception as e:  # 非 JSON 格式資料
                        # print(f"解析JSON訊息失敗: {e}")
                        pass
            except websockets.exceptions.ConnectionClosed:
                print(f"[{self.client_id}] 連接中斷，嘗試重新連接...")
                self.is_connected = False
                break
            except Exception as e:
                print(f"[{self.client_id}] 接收消息時發生未預期的錯誤: {e}")
                self.is_connected = False
                break
        print(f"[{self.client_id}] listen:結束")

    async def send_message(self, message: str, is_response: bool = False):
        # if self.reconnect and not is_response:
        #     print('先重新登入', flush=True)
        #     self.reconnect = False
        #     await authentication(self)
        #     await asyncio.sleep(1)

        re_connect = False
        while not self.is_connected:
            re_connect = True
            print(f"[{self.client_id}] 尚未連接，無法發送消息")
            await asyncio.sleep(2)
        if re_connect:
            print(f"[{self.client_id}] 已成功連接")

        try:
            await self.ws.send(message)
            if is_response:
                print(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [回覆訊息] 來源: {self.client_id}, 內容: {message}")
            else:
                print(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [發送訊息] 目的: {self.client_id}, 內容: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.client_id}] 發送時連接已關閉，嘗試重新連接...")
            self.is_connected = False
        except Exception as e:
            print(f"[{self.client_id}] 發送失敗: {e}")
            self.is_connected = False


async def wait_for_wifi_get_status(client: WebSocketClient, timeout=1200):
    """
    等待收到 action: wifi_get_status 的訊息
    """
    global latest_wifi_status_OK
    latest_wifi_status_OK = False
    for _ in range(timeout):
        if latest_wifi_status_OK:
            print("已收到 wifi_get_status OK 訊息")
            if latest_wifi_status_OK:
                return True
        await asyncio.sleep(0.1)
    print("等待 wifi_get_status 超時")
    return False


async def create_clients(ws_url: str, num_clients: int):
    clients = []
    for i in range(num_clients):
        client_id = f'z{i+2:04d}'
        client_id = 'z0005'  # 固定使用 z0005 作為測試ID
        # client_id = 'z0001'  #
        client_id = 'z0002'  #


        client = WebSocketClient(ws_url, client_id)
        clients.append(client)
        asyncio.create_task(client.connect())
        await asyncio.sleep(0.1)
    return clients


async def main():
    ws_url = "ws://localhost:38000"                                          # Local
    ws_url = "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"   # Trial
    # ws_url = "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"   # Live

    num_clients = 1
    clients = await create_clients(ws_url, num_clients)
    
    # 持續運行，只接收訊息不發送指令
    print("進入持續接收訊息模式...")
    while True:
        await asyncio.sleep(3600)  # 每小時打印一次狀態，保持程序運行

if __name__ == "__main__":
    asyncio.run(main())