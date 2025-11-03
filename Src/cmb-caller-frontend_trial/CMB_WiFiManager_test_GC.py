# test_client_wifi.py
# 以附件D架構為基礎，模擬B端前端，支援C規格WiFi所有 action，自動測試
import asyncio
import websockets
import json
import random
import uuid
from datetime import datetime

import nest_asyncio
nest_asyncio.apply()

class WebSocketClient:
    def __init__(self, ws_url: str, client_id: str):
        self.ws_url = ws_url
        self.client_id = client_id
        self.ws = None
        self.is_connected = False

    async def connect(self):
        while not self.is_connected:
            try:
                self.ws = await websockets.connect(self.ws_url)
                self.is_connected = True
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{self.client_id}] 已連接")
                asyncio.create_task(self.listen())
            except Exception as e:
                print(f"[{self.client_id}] 連線失敗: {e}")
                await asyncio.sleep(2)

    async def listen(self):
        while self.is_connected:
            try:
                async for message in self.ws:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [前端B][收到] {message}")
            except websockets.exceptions.ConnectionClosed:
                print(f"[{self.client_id}] 連線中斷")
                self.is_connected = False
                break

    async def send_message(self, msg: dict):
        try:
            msg_str = json.dumps(msg)
            await self.ws.send(msg_str)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [前端B][發送] {msg_str}")
        except Exception as e:
            print(f"[{self.client_id}] 發送失敗: {e}")

async def test_wifi_actions(client: WebSocketClient, device_id="a0001"):
    # 唯一識別碼
    uuid_str = lambda : str(uuid.uuid4())
    # 1. 要求狀態
    await client.send_message({
        "action": "wifi_get_status",
        "device_id": device_id,
        "uuid": uuid_str()
    })
    await asyncio.sleep(1)
    # 2. 要求WiFi掃描
    await client.send_message({
        "action": "wifi_scan_list",
        "device_id": device_id,
        "uuid": uuid_str()
    })
    await asyncio.sleep(1)
    # 3. 取得所有WiFi憑證
    await client.send_message({
        "action": "wifi_get_profiles",
        "device_id": device_id,
        "uuid": uuid_str()
    })
    await asyncio.sleep(1)
    # 4. 傳送新增WiFi憑證
    await client.send_message({
        "action": "wifi_add_profile",
        "device_id": device_id,
        "uuid": uuid_str(),
        "data": {
            "ssid": "Test-WiFi",
            "password": "test_123456",
            "priority": 3
        }
    })
    await asyncio.sleep(1)
    # 5. 刪除WiFi憑證
    await client.send_message({
        "action": "wifi_delete_profile",
        "device_id": device_id,
        "uuid": uuid_str(),
        "data": { "ssid": "Test-WiFi" }
    })
    await asyncio.sleep(1)
    # 6. 未定義指令（測試用）
    await client.send_message({
        "action": "wifi_custom_test",
        "device_id": device_id,
        "uuid": uuid_str(),
        "data": { "custom": "value" }
    })

async def main():
    ws_url = "ws://localhost:38000"
    client_id = "b0001"  # 代表 B 端
    client = WebSocketClient(ws_url, client_id)
    await client.connect()
    await asyncio.sleep(1)
    await test_wifi_actions(client)

    # 測試程式可持續運作
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())