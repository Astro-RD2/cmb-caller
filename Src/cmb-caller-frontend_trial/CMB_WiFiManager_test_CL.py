import asyncio
import websockets
import json
import uuid
from datetime import datetime

import nest_asyncio
nest_asyncio.apply()


class FrontendTestClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.is_connected = False

    async def connect(self):
        """連接到 WebSocket 伺服器"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            self.is_connected = True
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [前端] WebSocket 已連接")
            
            # 開始監聽回應
            asyncio.create_task(self.listen_responses())
            
        except Exception as e:
            print(f"[前端] 連接失敗: {e}")
            self.is_connected = False

    async def listen_responses(self):
        """監聽來自伺服器的回應"""
        try:
            async for message in self.ws:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [前端] 接收回應: {message}")
                
                # 嘗試解析 JSON 回應
                try:
                    json_data = json.loads(message)
                    await self.handle_response(json_data)
                except json.JSONDecodeError:
                    print(f"[前端] 收到非 JSON 格式回應: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("[前端] 連接已關閉")
            self.is_connected = False
        except Exception as e:
            print(f"[前端] 監聽回應時發生錯誤: {e}")
            self.is_connected = False

    async def handle_response(self, response):
        """處理 JSON 回應"""
        action = response.get("action", "")
        result = response.get("result", "")
        data = response.get("data", {})
        
        print(f"[前端] 處理回應: 動作={action}, 結果={result}")
        
        if result == "OK":
            if action == "wifi_get_status":
                status = data
                print(f"  WiFi 狀態: 連接={status.get('wifi_connected')}, SSID={status.get('current_ssid')}")
                print(f"  IP位址={status.get('ip_address')}, 信號強度={status.get('rssi')}")
                
            elif action == "wifi_scan_list":
                networks = data.get("networks", [])
                print(f"  掃描到 {len(networks)} 個網路:")
                for network in networks:
                    print(f"    - {network['ssid']} (信號: {network['rssi']}, 頻道: {network['channel']})")
                    
            elif action == "wifi_get_profiles":
                credentials = data.get("credentials", [])
                print(f"  已儲存 {len(credentials)} 個 WiFi 憑證:")
                for cred in credentials:
                    print(f"    - {cred['ssid']} (優先級: {cred['priority']})")
                    
            elif action == "wifi_add_profile":
                print("  WiFi 憑證新增成功")
                
            elif action == "wifi_delete_profile":
                print("  WiFi 憑證刪除成功")
        else:
            print(f"  操作失敗: {result}")

    async def send_command(self, command):
        """發送指令"""
        if not self.is_connected:
            print("[前端] 尚未連接，無法發送指令")
            return
        
        try:
            message = json.dumps(command, ensure_ascii=False)
            await self.ws.send(message)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]} [前端] 發送指令: {message}")
        except Exception as e:
            print(f"[前端] 發送指令失敗: {e}")

    async def test_wifi_get_status(self, device_id="a0001"):
        """測試取得 WiFi 狀態"""
        command = {
            "action": "wifi_get_status",
            "device_id": device_id,
            "uuid": str(uuid.uuid4())
        }
        await self.send_command(command)

    async def test_wifi_scan_list(self, device_id="a0001"):
        """測試 WiFi 掃描"""
        command = {
            "action": "wifi_scan_list",
            "device_id": device_id,
            "uuid": str(uuid.uuid4())
        }
        await self.send_command(command)

    async def test_wifi_get_profiles(self, device_id="a0001"):
        """測試取得 WiFi 憑證列表"""
        command = {
            "action": "wifi_get_profiles",
            "device_id": device_id,
            "uuid": str(uuid.uuid4())
        }
        await self.send_command(command)

    async def test_wifi_add_profile(self, device_id="a0001", ssid="Test-WiFi", password="test123456"):
        """測試新增 WiFi 憑證"""
        command = {
            "action": "wifi_add_profile",
            "device_id": device_id,
            "uuid": str(uuid.uuid4()),
            "data": {
                "ssid": ssid,
                "password": password,
                "priority": 3
            }
        }
        await self.send_command(command)

    async def test_wifi_delete_profile(self, device_id="a0001", ssid="Test-WiFi"):
        """測試刪除 WiFi 憑證"""
        command = {
            "action": "wifi_delete_profile",
            "device_id": device_id,
            "uuid": str(uuid.uuid4()),
            "data": {
                "ssid": ssid
            }
        }
        await self.send_command(command)

    async def run_all_tests(self, device_id="a0001"):
        """執行所有測試"""
        print("\n=== 開始 WiFi 功能測試 ===")
        
        print("\n1. 測試取得 WiFi 狀態")
        await self.test_wifi_get_status(device_id)
        await asyncio.sleep(2)
        
        print("\n2. 測試 WiFi 掃描")
        await self.test_wifi_scan_list(device_id)
        await asyncio.sleep(3)  # WiFi 掃描需要較長時間
        
        print("\n3. 測試取得已儲存的 WiFi 憑證")
        await self.test_wifi_get_profiles(device_id)
        await asyncio.sleep(2)
        
        print("\n4. 測試新增 WiFi 憑證")
        await self.test_wifi_add_profile(device_id, "Test-Network", "password123")
        await asyncio.sleep(2)
        
        print("\n5. 再次取得 WiFi 憑證列表（驗證新增結果）")
        await self.test_wifi_get_profiles(device_id)
        await asyncio.sleep(2)
        
        print("\n6. 測試刪除 WiFi 憑證")
        await self.test_wifi_delete_profile(device_id, "Test-Network")
        await asyncio.sleep(2)
        
        print("\n7. 最後一次取得 WiFi 憑證列表（驗證刪除結果）")
        await self.test_wifi_get_profiles(device_id)
        await asyncio.sleep(2)
        
        print("\n8. 測試錯誤情況 - 無效的 SSID")
        await self.test_wifi_add_profile(device_id, "", "password123")
        await asyncio.sleep(2)
        
        print("\n9. 測試錯誤情況 - 密碼太短")
        await self.test_wifi_add_profile(device_id, "Short-Pass-WiFi", "123")
        await asyncio.sleep(2)
        
        print("\n10. 測試錯誤情況 - 刪除不存在的憑證")
        await self.test_wifi_delete_profile(device_id, "Non-Existent-WiFi")
        await asyncio.sleep(2)
        
        print("\n=== WiFi 功能測試完成 ===")

    async def interactive_mode(self):
        """互動模式"""
        device_id = "a0001"
        
        while self.is_connected:
            print("\n=== WiFi 測試指令選單 ===")
            print("1. 取得 WiFi 狀態")
            print("2. WiFi 掃描")
            print("3. 取得 WiFi 憑證列表")
            print("4. 新增 WiFi 憑證")
            print("5. 刪除 WiFi 憑證")
            print("6. 執行完整測試")
            print("7. 變更目標裝置 ID")
            print("0. 退出")
            
            try:
                choice = input(f"\n請選擇功能 (目前裝置: {device_id}): ").strip()
                
                if choice == "1":
                    await self.test_wifi_get_status(device_id)
                elif choice == "2":
                    await self.test_wifi_scan_list(device_id)
                elif choice == "3":
                    await self.test_wifi_get_profiles(device_id)
                elif choice == "4":
                    ssid = input("請輸入 SSID: ").strip()
                    password = input("請輸入密碼: ").strip()
                    await self.test_wifi_add_profile(device_id, ssid, password)
                elif choice == "5":
                    ssid = input("請輸入要刪除的 SSID: ").strip()
                    await self.test_wifi_delete_profile(device_id, ssid)
                elif choice == "6":
                    await self.run_all_tests(device_id)
                elif choice == "7":
                    new_device_id = input("請輸入新的裝置 ID: ").strip()
                    if new_device_id:
                        device_id = new_device_id
                        print(f"已變更目標裝置為: {device_id}")
                elif choice == "0":
                    print("退出互動模式")
                    break
                else:
                    print("無效的選擇，請重新輸入")
                    
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("\n程式被中斷")
                break
            except Exception as e:
                print(f"執行指令時發生錯誤: {e}")

    async def disconnect(self):
        """斷開連接"""
        if self.ws and self.is_connected:
            await self.ws.close()
            self.is_connected = False
            print("[前端] 已斷開連接")


async def main():
    ws_url = "ws://localhost:38000"  # WebSocket Server 位址
    
    # 建立前端測試客戶端
    frontend = FrontendTestClient(ws_url)
    
    print("前端測試程式啟動中...")
    print("連接到 WebSocket 伺服器...")
    
    try:
        # 連接到伺服器
        await frontend.connect()
        
        if frontend.is_connected:
            print("連接成功！")
            
            # 等待一下讓連接穩定
            await asyncio.sleep(2)
            
            # 選擇執行模式
            print("\n請選擇執行模式:")
            print("1. 自動執行完整測試")
            print("2. 互動模式")
            
            mode = input("請輸入選擇 (1 或 2): ").strip()
            
            if mode == "1":
                # 自動執行所有測試
                await frontend.run_all_tests()
                
                # 保持連接一段時間以查看結果
                print("\n測試完成，保持連接 30 秒以查看結果...")
                await asyncio.sleep(30)
                
            elif mode == "2":
                # 互動模式
                await frontend.interactive_mode()
            else:
                print("無效選擇，執行預設測試")
                await frontend.run_all_tests()
        else:
            print("連接失敗！請確認 WebSocket 伺服器已啟動")
            
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"執行測試時發生錯誤: {e}")
    finally:
        await frontend.disconnect()
        print("前端測試程式結束")


if __name__ == "__main__":
    asyncio.run(main())