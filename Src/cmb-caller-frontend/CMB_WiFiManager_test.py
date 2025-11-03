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
    # cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='
    # message = f'{client.client_id},AUTH,{cmb_password}'
    # await client.send_message_auth(message)
    # await asyncio.sleep(1)

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
                    if True:
                        print('模擬定時自動斷線啟動', flush=True)
                        self.disconnect_task = asyncio.create_task(
                            self.auto_disconnect())
                    self.is_connected = True
            except Exception as e:
                print(f"[{self.client_id}] 連接失敗: {e}")
                self.is_connected = False
            await asyncio.sleep(0.1)

    async def listen(self):
        """處理接收到的訊息"""
        global msg_count, latest_wifi_status_OK, current_ssid

        while self.is_connected:
            try:
                async for message in self.ws:
                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [收到訊息] 來源: {self.client_id}, 內容: {message}", flush=True)
                    msg_count += 1
                    # 追蹤最後一次 wifi_xxx 的回應
                    try:
                        msg_json = json.loads(message)
                        self.last_message_json = msg_json
                        if msg_json.get("action") == "wifi_get_status":
                            if msg_json.get("result") == "OK":
                                latest_wifi_status_OK = True
                                current_ssid = msg_json['data']['current_ssid']
                            else:
                                latest_wifi_status_OK = False
                    except Exception:
                        pass
                    # await self.handle_websocket_message(message)
            except websockets.exceptions.ConnectionClosed:
                print(f"[{self.client_id}] 連接中斷，嘗試重新連接...")
                self.is_connected = False
                break
            except Exception as e:
                print(f"[{self.client_id}] 接收消息時發生未預期的錯誤: {e}")
                self.is_connected = False
                break
        print(f"[{self.client_id}] listen:結束")

    async def send_message_auth(self, message: str):
        re_connect = False
        while not self.is_connected:
            re_connect = True
            print(f"[{self.client_id}] 尚未連接，無法發送消息_AU")
            await asyncio.sleep(2)
        if re_connect:
            print(f"[{self.client_id}] 已成功連接")
        try:
            await self.ws.send(message)
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [發送訊息] 目的: {self.client_id} (認證), 內容: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.client_id}] 發送時連接已關閉，嘗試重新連接...")
            self.is_connected = False
        except Exception as e:
            print(f"[{self.client_id}] 發送失敗: {e}")
            self.is_connected = False

    async def send_message(self, message: str, is_response: bool = False):
        if self.reconnect and not is_response:
            print('先重新登入', flush=True)
            self.reconnect = False
            await authentication(self)
            await asyncio.sleep(1)

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

    def generate_next_value(self):
        self.last_value = self.last_value + random.randint(1, 1)
        if (self.last_value > 999):
            self.last_value = self.last_value - 999
        return self.last_value

    async def auto_disconnect(self):
        print(f"[{self.client_id}] 自動斷線:計時開始")
        await asyncio.sleep(900)
        if self.is_connected:
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [{self.client_id}] 自動斷線,開始測試自動重連")
            await self.ws.close()
            self.is_connected = False
        print(f"[{self.client_id}] 自動斷線:結束")


async def wait_for_wifi_get_status(client: WebSocketClient, timeout=1200):   # 60/0.1
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


async def wifi_add_profile_exec(client, add_profile_cmd):
    """
    1. 發送 wifi_add_profile
    2. 收到回應不是 "result":"OK" 則直接 return
    3. 若 "result":"OK" 則繼續等待 "action":"wifi_get_status" 才 return
    4. 顯示整體花費時間
    """
    # global msg_count, latest_wifi_status_OK
    global current_ssid
    msg_count = 0
    # print('\n')

    start_time = time.time()  # 記錄開始時間

    print('\n發送 wifi_add_profile 指令')
    await client.send_message(json.dumps(add_profile_cmd))

    # 等待 wifi_add_profile 回應
    for _ in range(1000):   # 1000 * 0.01 = 10
        if client.last_message_json and client.last_message_json.get("action") == "wifi_add_profile":
            result = client.last_message_json.get("result")
            client.last_message_json = None
            print(f"收到 wifi_add_profile 回應: {result}")
            if result != "OK":
                print("wifi_add_profile 失敗，提前結束")
                end_time = time.time()  # 記錄結束時間
                elapsed = end_time - start_time
                print(f"✅ 完成 wifi_add_profile 流程，總花費時間：{elapsed:.2f} 秒\n")
                return
            else:
                print("wifi_add_profile 成功，等待 wifi_get_status ...")
                break
        await asyncio.sleep(0.01)

    # 等待 wifi_get_status
    await wait_for_wifi_get_status(client)

    if (add_profile_cmd['data']['ssid'] == current_ssid):
        print(
            f"{client.last_message_json.get('action')}: {add_profile_cmd['data']['ssid']} 成功!")
    else:
        print(
            f"{client.last_message_json.get('action')}: {add_profile_cmd['data']['ssid']},{current_ssid} 失敗!")
    end_time = time.time()  # 記錄結束時間
    elapsed = end_time - start_time
    print(f"✅ 完成 wifi_add_profile 流程，總花費時間：{elapsed:.2f} 秒\n")


async def wifi_delete_profile_exec(client, delete_profile_cmd, caller_id):
    """
    1. 發送 wifi_delete_profile
    2. 收到回應不是 "result":"OK" 則直接 return
    3. 若 "result":"OK" 則繼續等待 "action":"wifi_get_status" 才 return
    """
    # global  latest_wifi_status_OK

    start_time = time.time()  # 記錄開始時間
    print('\n發送 wifi_delete_profile 指令')
    await client.send_message(json.dumps(delete_profile_cmd))
    # 等待回應
    for _ in range(1000):    # 1000 * 0.01 = 10
        if client.last_message_json and client.last_message_json.get("action") == "wifi_delete_profile":
            result = client.last_message_json.get("result")
            client.last_message_json = None
            print(f"收到 wifi_delete_profile 回應: {result}")
            if result != "OK":
                print("wifi_delete_profile 失敗，提前結束")
                end_time = time.time()  # 記錄結束時間
                elapsed = end_time - start_time
                print(
                    f"✅ 完成 wifi_delete_profile_exec 流程，總花費時間：{elapsed:.2f} 秒\n")
                return
            else:
                print("wifi_delete_profile 成功，等待 wifi_get_status ...")
                break
        await asyncio.sleep(0.01)

    req_uuid_1 = str(uuid.uuid4())
    status_request = {
        "action": "wifi_get_status",
        "caller_id": caller_id,
        "uuid": req_uuid_1
    }
    await client.send_message(json.dumps(status_request))
    # await asyncio.sleep(2)

    # 等待 wifi_get_status
    await wait_for_wifi_get_status(client)
    end_time = time.time()  # 記錄結束時間
    elapsed = end_time - start_time
    print(f"✅ 完成 wifi_delete_profile_exec 流程，總花費時間：{elapsed:.2f} 秒\n")


async def simulate_wifi_operations(client: WebSocketClient, caller_id: str):
    global msg_count
    ssid = "CMBz8888"
    password = "88888888"

    await asyncio.sleep(2)
    print(f"\n--- 開始模擬 {caller_id} 的 WiFi 操作 ---")

    # 1. B → A：請求上傳 ESP32 當前狀態 (wifi_get_status)
    req_uuid_1 = str(uuid.uuid4())
    status_request = {
        "action": "wifi_get_status",
        "caller_id": caller_id,
        "uuid": req_uuid_1
    }
    await client.send_message(json.dumps(status_request))
    await asyncio.sleep(2)

    # 2. B → A：請求上傳 WiFi 掃描結果 (wifi_scan_list)
    req_uuid_2 = str(uuid.uuid4())
    scan_request = {
        "action": "wifi_scan_list",
        "caller_id": caller_id,
        "uuid": req_uuid_2
    }
    await client.send_message(json.dumps(scan_request))
    await asyncio.sleep(2)

    # 3. B → A：請求上傳已儲存的 WiFi 憑證 (wifi_get_profiles)
    req_uuid_3 = str(uuid.uuid4())
    profiles_request = {
        "action": "wifi_get_profiles",
        "caller_id": caller_id,
        "uuid": req_uuid_3
    }
    await client.send_message(json.dumps(profiles_request))
    await asyncio.sleep(5)

    print('\n---------- Add ---------\n')

    # 4. B → A：傳送新的 WiFi 憑證 (wifi_add_profile) - 成功案例
    await asyncio.sleep(random.randint(5, 10))
    print('\n--- Add 1 ---')
    req_uuid_4 = str(uuid.uuid4())
    add_profile_success = {
        "action": "wifi_add_profile",
        "caller_id": caller_id,
        "uuid": req_uuid_4,
        "data": {
            "ssid": ssid,
            "password": password
        }
    }
    # add_profile_success = {
    #     "action": "wifi_add_profile",
    #     "caller_id": caller_id,
    #     "uuid": req_uuid_4,
    #     "data": {
    #         "ssid": "CMB00000",
    #         "password": "88888888"
    #     }
    # }
    await wifi_add_profile_exec(client, add_profile_success)

    # 4. B → A：傳送新的 WiFi 憑證 (wifi_add_profile) - 失敗案例：無效 SSID
    await asyncio.sleep(random.randint(5, 10))
    print('\n--- Add 2 ---')
    req_uuid_5 = str(uuid.uuid4())
    add_profile_fail_ssid = {
        "action": "wifi_add_profile",
        "caller_id": caller_id,
        "uuid": req_uuid_5,
        "data": {
            "ssid": "ooxx",
            "password": "valid_password"
        }
    }
    await wifi_add_profile_exec(client, add_profile_fail_ssid)

    # # 4. B → A：傳送新的 WiFi 憑證 (wifi_add_profile) - 失敗案例：無效密碼
    # await asyncio.sleep(random.randint(5, 10))
    # print('\n--- Add 3 ---')
    # req_uuid_6 = str(uuid.uuid4())
    # add_profile_fail_password = {
    #     "action": "wifi_add_profile",
    #     "caller_id": caller_id,
    #     "uuid": req_uuid_6,
    #     "data": {
    #         "ssid": "Conplus_CSD",
    #         "password": "fail_password"
    #     }
    # }
    # await wifi_add_profile_exec(client, add_profile_fail_password)

    print('\n---------- Delete ---------\n')

    # # 5. B → A：刪除指定的 WiFi 憑證 (wifi_delete_profile) - 失敗
    # await asyncio.sleep(random.randint(5, 10))
    # req_uuid_9 = str(uuid.uuid4())
    # delete_profile_success2 = {
    #     "action": "wifi_delete_profile",
    #     "caller_id": caller_id,
    #     "uuid": req_uuid_9,
    #     "data": {
    #         "ssid": "Conplus_CSD"
    #     }
    # }
    # await wifi_delete_profile_exec(client, delete_profile_success2, caller_id)

    # await asyncio.sleep(random.randint(5, 10))
    # req_uuid_8 = str(uuid.uuid4())
    # delete_profile_fail_not_found = {
    #     "action": "wifi_delete_profile",
    #     "caller_id": caller_id,
    #     "uuid": req_uuid_8,
    #     "data": {
    #         "ssid": "NonExistentWiFi"
    #     }
    # }
    # await wifi_delete_profile_exec(client, delete_profile_fail_not_found, caller_id)

    # 5. B → A：刪除指定的 WiFi 憑證 (wifi_delete_profile) - 成功
    await asyncio.sleep(random.randint(5, 10))
    req_uuid_7 = str(uuid.uuid4())
    delete_profile_success = {
        "action": "wifi_delete_profile",
        "caller_id": caller_id,
        "uuid": req_uuid_7,
        "data": {
            "ssid": ssid
        }
    }
    await wifi_delete_profile_exec(client, delete_profile_success, caller_id)

    await asyncio.sleep(random.randint(5, 10))
    req_uuid_9 = str(uuid.uuid4())
    delete_profile_success2 = {
        "action": "wifi_delete_profile",
        "caller_id": caller_id,
        "uuid": req_uuid_9,
        "data": {
            "ssid": "ooxx"
        }
    }
    await wifi_delete_profile_exec(client, delete_profile_success2, caller_id)

    print(f"--- 加強測試 ---")
    for i in range(10):
        print(f"--- 加強測試 第 {i+1} 次 ---")


        delay = random.randint(5, 10)
        print(f"等待 {delay} 秒後執行...")
        await asyncio.sleep(delay)

        print(f"執行加入...")
        req_uuid_6 = str(uuid.uuid4())
        add_profile_fail_password = {
            "action": "wifi_add_profile",
            "caller_id": caller_id,
            "uuid": req_uuid_6,
            "data": {
                # "ssid": "Conplus_CSD",
                "ssid": ssid,
                "password": password
            }
        }
        await wifi_add_profile_exec(client, add_profile_fail_password)

        delay = random.randint(5, 10)
        print(f"等待 {delay} 秒後執行...")
        await asyncio.sleep(delay)

        print(f"執行刪除...")
        req_uuid = str(uuid.uuid4())
        delete_profile_payload = {
            "action": "wifi_delete_profile",
            "caller_id": caller_id,
            "uuid": req_uuid,
            "data": {
                # "ssid": "NonExistentWiFi"
                "ssid": ssid
            }
        }
        await wifi_delete_profile_exec(client, delete_profile_payload, caller_id)

        print(f"第 {i+1} 次測試完成\n")

    print(f"\n--- 模擬 WiFi 操作結束 ---\n等待3600秒!")
    while True:
        await asyncio.sleep(3600)


async def create_clients(ws_url: str, num_clients: int):
    clients = []
    for i in range(num_clients):
        client_id = f'z{i+2:04d}'
        client_id = 'z0005'
        client_id = 'z0002'
        # client_id = 'a0103'
        # client_id = 'v0002'

        client = WebSocketClient(ws_url, client_id)
        clients.append(client)
        asyncio.create_task(client.connect())
        await asyncio.sleep(0.01)
    return clients


async def main():
    ws_url = "ws://localhost:38000"                                          # Local
    # ws_url = "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"   # Trial
    # ws_url = "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"   # Live

    num_clients = 1
    clients = await create_clients(ws_url, num_clients)
    if clients:
        await simulate_wifi_operations(clients[0], clients[0].client_id)

if __name__ == "__main__":
    asyncio.run(main())
