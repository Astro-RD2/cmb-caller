# 2025/03/20 常用


import asyncio
import websockets
import random
from datetime import datetime
import json
import threading
import time

import nest_asyncio
nest_asyncio.apply()

current_number = 0

async def authentication(client):
    cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='   # SOFT CMB Caller
    # cmb_password = 'liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ='   # CMB Caller
    # cmb_password = 'user_get_num'   # user_get_num
    # cmb_password = 'Fail_Password'   # Fail
    message = f'{client.client_id},AUTH,{cmb_password}'   # CMB Caller
    await client.send_message_auth(message)
    await asyncio.sleep(1)


async def authentication_json(client):
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


class WebSocketClient:
    def __init__(self, ws_url: str, client_id: str):
        self.ws_url = ws_url
        self.client_id = client_id
        self.ws = None
        self.is_connected = False
        # self.last_value = random.randint(1, 999)
        self.last_value = 0
        self.reconnect_task = None
        self.reconnect = False
        self.listen_task = None
        self.disconnect_task = None

    async def connect(self):
        while True:  # 持續嘗試重連
            try:
                if not self.is_connected:
                    self.reconnect = True
                    self.ws = await websockets.connect(self.ws_url)
                    # print(f"[{self.client_id}] WebSocket 已連接")
                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] WebSocket 已連接")

                    # if self.listen_task is None and not self.listen_task.done():
                    # if self.listen_task is None:
                    if True:
                        print('開始監聽回傳資料', flush=True)
                        self.listen_task = asyncio.create_task(
                            self.listen())  # 開始監聽回傳資料

                    # if self.disconnect_task is None and not self.disconnect_task.done():
                    # if self.disconnect_task is None:
                    # if True:
                    #     print('模擬定時自動斷線啟動', flush=True)
                    #     self.disconnect_task = asyncio.create_task(
                    #         self.auto_disconnect())

                    self.is_connected = True
            except Exception as e:
                print(f"[{self.client_id}] 連接失敗: {e}")
                self.is_connected = False
            await asyncio.sleep(1)  # 無論成功或失敗，都等待5秒再嘗試

    async def listen(self):
        """處理接收到的訊息"""
        global current_number
        while self.is_connected:
            try:
                async for message in self.ws:
                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] 接收: {message.encode('utf-8').decode('unicode_escape')}")
                    message_uni = message.encode('utf-8').decode('unicode_escape')
                    parts = message_uni.split(',')
                    if parts[-1] == 'get':
                        current_number = int(parts[-2])
                    if parts[-1] == 'update':
                        current_number = int(parts[-2])

                    
            except websockets.exceptions.ConnectionClosed:
                print(f"[{self.client_id}] 連接中斷，嘗試重新連接...")
                self.is_connected = False
                break  # 跳出迴圈，讓 connect() 方法處理重連
            except Exception as e:
                print(f"[{self.client_id}] 接收消息時發生未預期的錯誤: {e}")
                self.is_connected = False
                break  # 跳出迴圈，讓 connect() 方法處理重連
        print(f"[{self.client_id}] listen:結束")

    async def send_message_auth(self, message: str):

        re_connect = False
        while not self.is_connected:
            re_connect = True
            print(f"[{self.client_id}] 尚未連接，無法發送消息_AU")
            await asyncio.sleep(2)  # 每隔x秒重试一次连接
        if re_connect:
            print(f"[{self.client_id}] 已成功連接")
        try:
            await self.ws.send(message)
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] 發送: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.client_id}] 發送時連接已關閉，嘗試重新連接...")
            self.is_connected = False
        except Exception as e:
            print(f"[{self.client_id}] 發送失敗: {e}")
            self.is_connected = False

    async def send_message(self, message: str):

        if self.reconnect:    # 重新連接先重新登入
            print('先重新登入', flush=True)
            self.reconnect = False

            # await authentication(self)
            await auth_diff(self)

            await asyncio.sleep(1)

        re_connect = False
        while not self.is_connected:
            re_connect = True
            print(f"[{self.client_id}] 尚未連接，無法發送消息")
            await asyncio.sleep(2)  # 每隔x秒重试一次连接
        if re_connect:
            print(f"[{self.client_id}] 已成功連接")

        try:
            await self.ws.send(message)
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] 發送: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.client_id}] 發送時連接已關閉，嘗試重新連接...")
            self.is_connected = False
        except Exception as e:
            print(f"[{self.client_id}] 發送失敗: {e}")
            self.is_connected = False

    def generate_next_value(self):
        global current_number
        # self.last_value = current_number
        # self.last_value = self.last_value + random.randint(1, 1)
        self.last_value = current_number + 1
        print(f"--- self.last_value:{self.last_value} ---")
        if (self.last_value > 999):
            self.last_value = self.last_value - 999
        return self.last_value

    async def auto_disconnect(self):
        """模擬自動斷線"""
        print(f"[{self.client_id}] 自動斷線:計時開始")
        await asyncio.sleep(600)  # 等待
        if self.is_connected:
            # print(f"[{self.client_id}] 自動斷線,開始測試自動重連")
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] 自動斷線,開始測試自動重連")
            await self.ws.close()
            self.is_connected = False
        print(f"[{self.client_id}] 自動斷線:結束")


async def simulate_client_behavior(clients, message_interval):

    await asyncio.sleep(5)
    # print('開始模擬客戶端行為...')
    print('')
    i = -1
    next_value = 0
    while True:
        for client in clients:
            i = i + 1
            if client.is_connected:

                print('\n========================================')
                await asyncio.sleep(1)
                # 發送命令 get_num_switch, 8. 取號開關：
                send_command = {
                    "action": "get_num_switch",
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "switch": "off",
                    "uuid": hex(id(client))
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                message = f'{client.client_id},ping,{next_value}'
                await client.send_message(message)
                await asyncio.sleep(1)

                message = f'{client.client_id},get'
                await client.send_message(message)
                await asyncio.sleep(1)

                # next_value = client.generate_next_value_xxx()
                # message = f'{client.client_id},SEND,{next_value}'   # 'send'
                # await client.send_message(message)
                next_value = client.generate_next_value()
                send_command = {        # 'send'
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "call_num": f'{next_value}',
                    "change": True,
                    "last_update": 0,
                    "uuid": "JSON_SEND"
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                message = f'{client.client_id},ping,{next_value}'
                await client.send_message(message)
                await asyncio.sleep(1)

                # 發送命令 get_num_switch, 8. 取號開關：
                send_command = {
                    "action": "get_num_switch",
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "switch": "on",
                    "uuid": hex(id(client))
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                if i % 5 == 0:
                    await asyncio.sleep(1)
                    print('\n--------------------------')
                    # 發送命令 user_get_num, 9. 使用者取號
                    send_command = {
                        "action": "user_get_num",
                        "vendor_id": "tawe",
                        "caller_id": f"{client.client_id}",
                        "user_id": "ASD7QEZ3XCT5FG",
                        "get_num_item_id": "2",
                        "uuid": hex(id(client))
                    }
                    message = json.dumps(send_command)
                    await client.send_message(message)
                    await asyncio.sleep(1)
                    print('--------------------------\n')

                message = f'{client.client_id},get'
                await client.send_message(message)
                await asyncio.sleep(1)

                message = f'{client.client_id},get_num_info'    # ~~~~
                await client.send_message(message)
                await asyncio.sleep(1)

                send_command = {
                    "action": "get_num_info",
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "user_id": "ASD7QEZ3XCT5FG",
                    "uuid": hex(id(client))
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                # 發送命令 get_num_status, 10. 取號服務狀態：
                send_command = {
                    "action": "get_num_status",
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "uuid": hex(id(client))
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                # 發送命令 set_params, 16.參數設定：
                send_command = {
                    "action": "set_params",
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "params": {
                        "get_num_max": "15",              # 取號上限 ("0"表示無上限)
                        "hidden": True                    # (true/false) 是否隱藏此叫號機，不顯示在 Line 及 訪客網頁
                        }, 
                    "uuid": hex(id(client))
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

                message = f'{client.client_id},get'
                await client.send_message(message)
                await asyncio.sleep(1)

                # await asyncio.sleep(5)
                # 發送命令 send, 傳送叫號號碼
                next_value = client.generate_next_value()
                send_command = {        # 'send'
                    "vendor_id": "tawe",
                    "caller_id": f"{client.client_id}",
                    "call_num": f'{next_value}',
                    "change": True,
                    "last_update": 0,
                    "uuid": "JSON_SEND"
                }
                message = json.dumps(send_command)
                await client.send_message(message)
                await asyncio.sleep(1)

        await asyncio.sleep(message_interval * (1 + random.uniform(-0.1, 0.1)))





# def wait_with_timeout(timeout=60):
#     def wait_for_enter(event):
#         input()
#         event.set()

#     event = threading.Event()
#     threading.Thread(target=wait_for_enter, args=(event,), daemon=True).start()

#     print(f"程式暫停中，按 Enter 鍵繼續，或等待 {timeout} 秒自動繼續...")
#     event.wait(timeout=timeout)
#     print("繼續執行程式")


def wait_with_timeout(timeout=60):
    def wait_for_enter(event):
        input()
        event.set()

    event = threading.Event()
    threading.Thread(target=wait_for_enter, args=(event,), daemon=True).start()

    print(f"程式暫停中，按 Enter 鍵繼續，或等待 {timeout} 秒自動繼續...")
    for remaining in range(timeout, 0, -1):
        if event.is_set():
            break
        print(f"\r剩餘時間：{remaining:2d} 秒  ", end="")
        time.sleep(1)

    print("\n繼續執行程式")

auth_count = 0

async def auth_diff(client):   # select
    global auth_count
    if auth_count % 2 == 0:
        await authentication(client)
    else:
        await authentication_json(client)
    auth_count += 1


async def auth_test(clients):
    await asyncio.sleep(5)
    for client in clients:
        if client.is_connected:
            client.reconnect = False

            # await authentication(client)
            await auth_diff(client)

            wait_with_timeout(10)  # 等 xx 秒

            # await asyncio.sleep(1)
            # # 發送命令 get_num_switch, 8. 取號開關：
            # send_command = {
            #     "action": "get_num_switch",
            #     "vendor_id": "tawe",
            #     "caller_id": f"{client.client_id}",
            #     "switch": "on",
            #     "uuid": hex(id(client))
            # }
            # message = json.dumps(send_command)
            # await client.send_message(message)
            # await asyncio.sleep(1)

            # 發送命令 user_get_num, 9. 使用者取號
            send_command = {
                "action": "user_get_num",
                "vendor_id": "tawe",
                "caller_id": f"{client.client_id}",
                "user_id": "ASD7QEZ3XCT5FG",
                "get_num_item_id": "1",
                "uuid": hex(id(client))
            }
            message = json.dumps(send_command)
            await client.send_message(message)
            await asyncio.sleep(1)

            # 發送命令 get_num_status, 10. 取號服務狀態：
            send_command = {
                "action": "get_num_status",
                "vendor_id": "tawe",
                "caller_id": f"{client.client_id}",
                "uuid": hex(id(client))
            }
            message = json.dumps(send_command)
            await client.send_message(message)
            await asyncio.sleep(1)

            # # 發送命令 get_num_status, 10. 取號服務狀態：
            # send_command = {
            #     "action": "new_action",
            #     "vendor_id": "tawe",
            #     "caller_id": f"{client.client_id}",
            #     "uuid": hex(id(client))
            # }
            # message = json.dumps(send_command)
            # await client.send_message(message)
            # await asyncio.sleep(1)

            message = f'{client.client_id},get'
            await client.send_message(message)
            await asyncio.sleep(2)

            wait_with_timeout(5)  # 等 xx 秒

            # await asyncio.sleep(1)
            # message = f'{client.client_id},SEND,2'
            # await client.send_message(message)

            # await asyncio.sleep(1)
            # message = f'{client.client_id},get_num_info'
            # await client.send_message(message)

            # await asyncio.sleep(3)
            # message = f'{client.client_id},SEND,1'
            # await client.send_message(message)

            # await asyncio.sleep(1)
            # message = f'{client.client_id},get_num_info'
            # await client.send_message(message)
            # await asyncio.sleep(3)

            message = f'{client.client_id},SEND,0'
            await client.send_message(message)
            await asyncio.sleep(3)

            message = f'{client.client_id},SEND,1'
            await client.send_message(message)
            await asyncio.sleep(1)

            message = f'{client.client_id},get'
            await client.send_message(message)
            await asyncio.sleep(1)

            wait_with_timeout(10)  # 等 xx 秒

            # await asyncio.sleep(1)
            # message = f'{client.client_id},get_num_info'
            # await client.send_message(message)
            # await asyncio.sleep(1)

            # message = f'{client.client_id},get'
            # await client.send_message(message)
            # await asyncio.sleep(1)

            # message = f'{client.client_id},SEND,888'
            # await client.send_message(message)
            # await asyncio.sleep(1)

            # message = f'{client.client_id},get'
            # await client.send_message(message)
            # await asyncio.sleep(1)

            message = f'{client.client_id},ping,123'
            await client.send_message(message)
            await asyncio.sleep(1)

            # 發送命令 get_num_switch, 8. 取號開關：
            send_command = {
                "action": "get_num_switch",
                "vendor_id": "tawe",
                "caller_id": f"{client.client_id}",
                "switch": "off",
                "uuid": hex(id(client))
            }
            message = json.dumps(send_command)
            await client.send_message(message)
            await asyncio.sleep(1)

            message = f'{client.client_id},PING'
            await client.send_message(message)
            await asyncio.sleep(1)

            message = f'{client.client_id},ping'
            await client.send_message(message)
            await asyncio.sleep(1)

            # 發送命令 get_num_switch, 8. 取號開關：
            send_command = {
                "action": "get_num_switch",
                "vendor_id": "tawe",
                "caller_id": f"{client.client_id}",
                "switch": "on",
                "uuid": hex(id(client))
            }
            message = json.dumps(send_command)
            await client.send_message(message)
            await asyncio.sleep(1)

            # message = f'{client.client_id},info,test'
            # await client.send_message(message)

            # await asyncio.sleep(1)
            # message = f'{client.client_id},get_num_info'
            # await client.send_message(message)


async def create_clients(ws_url: str, num_clients: int):
    print(f'連線至 {ws_url}')
    clients = []
    for i in range(num_clients):
        # client_id = f'v{i+5:04d}'
        # client_id = f'V{i+5:04d}'
        # client_id = f'v{i+2:04d}'
        # client_id = f'v{0+5:04d}'
        # client_id = f'z{i+5:04d}'
        # client_id = f'z{i+2:04d}'
        client_id = 'z0002'
        # client_id = 'z0001'
        # client_id = 'a011l'

        client = WebSocketClient(ws_url, client_id)
        clients.append(client)
        asyncio.create_task(client.connect())  # 啟動連接任務
        await asyncio.sleep(0.01)
    return clients


async def main():
    ws_url = "ws://localhost:38000"                                          # Local
    # ws_url = "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"   # Trial
    # ws_url = "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"   # Live

    message_interval = 30
    num_clients = 1

    clients = await create_clients(ws_url, num_clients)

    for _ in range(1):
        await auth_test(clients)        # 登錄及簡單執行
        await asyncio.sleep(1)

    await simulate_client_behavior(clients, message_interval)

if __name__ == "__main__":
    asyncio.run(main())
