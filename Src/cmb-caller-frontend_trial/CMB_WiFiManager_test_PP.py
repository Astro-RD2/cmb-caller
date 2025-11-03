import asyncio
import websockets
import random
from datetime import datetime
import json
import uuid

import nest_asyncio
nest_asyncio.apply()

from typing import Optional

# ---- 附件D的 WebSocketClient 略作調整 ----

class WiFiWebSocketClient(WebSocketClient):
    def __init__(self, ws_url: str, client_id: str):
        super().__init__(ws_url, client_id)
        self.device_id = client_id

    async def listen(self):
        """處理接收到的訊息"""
        while self.is_connected:
            try:
                async for message in self.ws:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [前端B] 接收: {message}")
                    try:
                        data = json.loads(message)
                        action = data.get("action")
                        print(f"[前端B] action={action}, 內容={data}")
                    except Exception as e:
                        print(f"[前端B] 回應解析錯誤: {e}")
            except websockets.exceptions.ConnectionClosed:
                print(f"[前端B] 連接中斷，嘗試重新連接...")
                self.is_connected = False
                break
            except Exception as e:
                print(f"[前端B] 接收消息時發生未預期的錯誤: {e}")
                self.is_connected = False
                break
        print(f"[前端B] listen:結束")

    async def send_wifi_action(self, action: str, data: Optional[dict]=None):
        # 產生唯一uuid
        msg = {
            "action": action,
            "device_id": self.device_id,
            "uuid": str(uuid.uuid4())
        }
        if data:
            msg["data"] = data
        await self.send_message(json.dumps(msg))

    async def simulate_wifi_commands(self):
        await asyncio.sleep(2)  # 等待登入
        # 1. 要求上傳狀態
        await self.send_wifi_action("wifi_get_status")
        await asyncio.sleep(1)
        # 2. 要求WiFi掃描
        await self.send_wifi_action("wifi_scan_list")
        await asyncio.sleep(1)
        # 3. 要求已儲存WiFi憑證
        await self.send_wifi_action("wifi_get_profiles")
        await asyncio.sleep(1)
        # 4. 新增WiFi憑證
        await self.send_wifi_action("wifi_add_profile", {
            "ssid": "New-WiFi-Network",
            "password": "password_123",
            "priority": 1
        })
        await asyncio.sleep(1)
        # 5. 刪除WiFi憑證
        await self.send_wifi_action("wifi_delete_profile", {
            "ssid": "Office-Network"
        })
        await asyncio.sleep(1)
        print("[前端B] 測試指令已全部發送完畢")

async def main():
    client = WiFiWebSocketClient("ws://localhost:8765", "b0001")
    asyncio.create_task(client.connect())
    await asyncio.sleep(2)
    await authentication(client)  # 登入
    await asyncio.sleep(2)
    await client.simulate_wifi_commands()

if __name__ == "__main__":
    asyncio.run(main())
