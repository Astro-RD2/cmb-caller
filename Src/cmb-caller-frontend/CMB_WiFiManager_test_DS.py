'''
2025/05/26 OK, GOOD
'''


import asyncio
import websockets
import json
import random
from datetime import datetime
from typing import Dict, Optional

import nest_asyncio
nest_asyncio.apply()


class FrontendSimulator:
    def __init__(self, ws_url: str, device_id: str = "frontend_001"):
        self.ws_url = ws_url
        self.device_id = device_id
        self.ws = None
        self.is_connected = False
        self.receive_task = None
        self.send_task = None
        self.message_queue = asyncio.Queue()
        self.msg_count = 0

    async def connect(self):
        """連接 WebSocket 伺服器"""
        while True:
            try:
                self.ws = await websockets.connect(self.ws_url)
                self.is_connected = True
                print(f"{self._timestamp()} [Frontend] 已連接至伺服器 {self.ws_url}")

                # 發送識別訊息
                cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='   # SOFT CMB Caller
                print(f"{self._timestamp()} [Frontend] 發送登入請求")
                message = f'{self.device_id},AUTH,{cmb_password}'
                print(f"{self._timestamp()} [Frontend] 已發送訊息: {message}")
                await self.ws.send(message)

                # 創建收發任務
                self.receive_task = asyncio.create_task(self.listen())
                self.send_task = asyncio.create_task(self.send_messages())

                # 開始測試流程
                await self.run_tests()
                # await self.run_tests_new()

                # 等待任務完成
                await asyncio.gather(self.receive_task, self.send_task)

            except Exception as e:
                print(f"{self._timestamp()} [Frontend] 連接失敗: {str(e)}")
                self.is_connected = False
                if self.receive_task:
                    self.receive_task.cancel()
                if self.send_task:
                    self.send_task.cancel()
                await asyncio.sleep(5)  # 等待後重試

    async def listen(self):
        """監聽來自伺服器的訊息"""
        try:
            while self.is_connected:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                    self.msg_count += 1
                    # print(f"count:{self.msg_count} ",end='',flush=True)
                    print(f"{self._timestamp()} [Frontend] 收到訊息: {message}")
                except asyncio.TimeoutError:
                    # 超時是正常的，繼續監聽
                    continue
                except Exception as e:
                    print(f"{self._timestamp()} [Frontend] 監聽失敗: {str(e)}")
                    self.is_connected = False
                    break
        except Exception as e:
            print(f"{self._timestamp()} [Frontend] 監聽任務錯誤: {str(e)}")
            self.is_connected = False

    async def send_messages(self):
        """從隊列發送訊息"""
        while self.is_connected:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.ws.send(message)
                print(f"{self._timestamp()} [Frontend] 已發送訊息: {message}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"{self._timestamp()} [Frontend] 發送訊息失敗: {str(e)}")
                self.is_connected = False
                break

    async def run_tests(self):
        ssid = "CMBz6666"
        password = "88888888"
        # ssid = "astrocorp_10F"
        # password = "Astro1688#"

        """執行測試流程"""
        await asyncio.sleep(1)  # 等待連接穩定

        # 測試獲取狀態
        await self.test_get_status()
        await asyncio.sleep(1)

        # 測試掃描 WiFi
        await self.test_scan_wifi()
        await asyncio.sleep(1)

        # 測試獲取 WiFi 配置
        await self.test_get_profiles()
        await asyncio.sleep(1)


        # # 測試獲取狀態
        # await self.test_get_status()
        # await asyncio.sleep(1)

        # # 測試掃描 WiFi
        # await self.test_scan_wifi()
        # await asyncio.sleep(1)

        # # 測試獲取 WiFi 配置
        # await self.test_get_profiles()
        # await asyncio.sleep(1)


        #'''
        print('\n-----------------------------------')
        # 測試添加 WiFi 配置
        self.msg_count = 0
        await self.test_add_profile(ssid, password)
        print('')
        i = 0
        while self.msg_count <= 1:
            print(f"w_{i},{self.msg_count} ",end='',flush=True)
            await asyncio.sleep(1)
            i += 1
        print(f'連線時間:{i}秒')

        # 測試獲取 WiFi 配置
        await self.test_get_profiles()
        await asyncio.sleep(1)

        # 測試刪除 WiFi 配置
        await self.test_delete_profile(ssid)
        await asyncio.sleep(1)

        # 測試獲取 WiFi 配置
        await self.test_get_profiles()
        await asyncio.sleep(1)

        print('\n-----------------------------------')
        # 測試添加 WiFi 配置
        self.msg_count = 0
        await self.test_add_profile()
        print('')
        i = 0
        while self.msg_count <= 1:
            print(f"w_{i},{self.msg_count} ",end='',flush=True)
            await asyncio.sleep(1)
            i += 1
        print(f'連線時間:{i}秒')

        # 測試獲取 WiFi 配置
        await self.test_get_profiles()
        await asyncio.sleep(1)

        # 測試刪除 WiFi 配置
        await self.test_delete_profile()
        await asyncio.sleep(1)

        # 測試獲取 WiFi 配置
        await self.test_get_profiles()
        await asyncio.sleep(1)

        print('\n--------------- END --------------------\n')

        #'''

    async def test_get_status(self):
        """測試獲取狀態"""
        request = {
            "action": "wifi_get_status",
            "device_id": self.device_id,  # 目標 ESP32 裝置 ID
            "uuid": self._generate_uuid()
        }
        print(f"{self._timestamp()} [Frontend] 發送獲取狀態請求", end=' ', flush=True)
        await self._send_message(request)

    async def test_scan_wifi(self):
        """測試掃描 WiFi"""
        request = {
            "action": "wifi_scan_list",
            "device_id": self.device_id,
            "uuid": self._generate_uuid()
        }
        print(
            f"{self._timestamp()} [Frontend] 發送掃描 WiFi 請求", end=' ', flush=True)
        await self._send_message(request)

    async def test_get_profiles(self):
        """測試獲取 WiFi 配置"""
        request = {
            "action": "wifi_get_profiles",
            "device_id": self.device_id,
            "uuid": self._generate_uuid()
        }
        print(
            f"{self._timestamp()} [Frontend] 發送獲取 WiFi 配置請求", end=' ', flush=True)
        await self._send_message(request)

    async def test_add_profile(self, ssid='Conplus_CSD', password=''):
        """測試添加 WiFi 配置"""
        request = {
            "action": "wifi_add_profile",
            "device_id": self.device_id,
            "uuid": self._generate_uuid(),
            "data": {
                "ssid": ssid,
                "password": password,
                "priority": 3
            }
        }
        print(
            f"{self._timestamp()} [Frontend] 發送添加 WiFi {ssid} 配置請求", end=' ', flush=True)
        await self._send_message(request)

    async def test_delete_profile(self, ssid='Conplus_CSD'):
        """測試刪除 WiFi 配置"""
        request = {
            "action": "wifi_delete_profile",
            "device_id": self.device_id,
            "uuid": self._generate_uuid(),
            "data": {
                "ssid": ssid
            }
        }
        print(
            f"{self._timestamp()} [Frontend] 發送刪除 WiFi {ssid} 配置請求", end=' ', flush=True)
        await self._send_message(request)

    async def _send_message(self, data: Dict):
        """發送 JSON 訊息"""
        # print(f'發送 JSON 訊息:{data}')
        try:
            message = json.dumps(data)
            await self.ws.send(message)
            print(f"{self._timestamp()} [Frontend] 已發送訊息: {message}")
        except Exception as e:
            print(f"{self._timestamp()} [Frontend] 發送訊息失敗: {str(e)}")
            self.is_connected = False

    def _generate_uuid(self):
        """生成簡單的 UUID"""
        return f"{random.getrandbits(32):08x}"

    def _timestamp(self):
        """取得當前時間戳記"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]


async def main():
    ws_url = "ws://localhost:38000"                                          # Local
    # ws_url = "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"   # Trial
    # ws_url = "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"   # Live
    simulator = FrontendSimulator(ws_url, 'z0002')
    await simulator.connect()

if __name__ == "__main__":
    asyncio.run(main())
