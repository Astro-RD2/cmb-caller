# ws_client_simulator.py
import asyncio
import websockets
import json
import uuid

device_id = "a0001"

async def simulate_frontend():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print(f"✅ 已連接到 WebSocket Server: {uri}")

        # 手動選擇要發送的 action
        while True:
            print("\n請選擇要發送的動作：")
            print("1. wifi_get_status")
            print("2. wifi_scan_list")
            print("3. wifi_get_profiles")
            print("4. wifi_add_profile")
            print("5. wifi_delete_profile")
            print("0. 離開")
            choice = input("輸入編號：")

            if choice == "0":
                break

            action_map = {
                "1": "wifi_get_status",
                "2": "wifi_scan_list",
                "3": "wifi_get_profiles",
                "4": "wifi_add_profile",
                "5": "wifi_delete_profile"
            }

            action = action_map.get(choice)
            if not action:
                print("無效選項")
                continue

            uuid_str = str(uuid.uuid4())

            data = {}
            if action == "wifi_add_profile":
                data = {
                    "ssid": "New-WiFi-Network",
                    "password": "password_123",
                    "priority": 1
                }
            elif action == "wifi_delete_profile":
                data = {
                    "ssid": "Office-Network"
                }

            message = {
                "action": action,
                "device_id": device_id,
                "uuid": uuid_str,
            }
            if data:
                message["data"] = data

            print(f"📤 發送訊息:\n{json.dumps(message, indent=2)}")
            await websocket.send(json.dumps(message))

            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"📥 收到回應:\n{response}")
            except asyncio.TimeoutError:
                print("⚠️ 逾時未收到回應")

if __name__ == "__main__":
    asyncio.run(simulate_frontend())
