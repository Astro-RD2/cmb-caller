import asyncio
import websockets
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import aiohttp
from dataclasses import dataclass
from enum import Enum


print("CMB_websocket_monitor.py 程式啟動!", flush=True)

try:
    __IPYTHON__  # 如果在 Jupyter 中，這個變數會存在
    import nest_asyncio
    nest_asyncio.apply()
    print("nest_asyncio 已啟用 (Jupyter 環境)", flush=True)
except NameError:
    pass  # 在標準 Python 環境中，什麼都不做
    print("nest_asyncio 未啟用 (非 Jupyter 環境)", flush=True)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class WebSocketMessage:
    content: Any
    timestamp: float
    message_type: str = "unknown"


class QualityMetrics:
    response_time_ms: Optional[float] = None
    message_rate: float = 0.0
    connection_stability: bool = True
    last_successful_ping: Optional[float] = None


class ReliableWebSocketMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ws_url = config['websocket']['url']
        self.login_data = config['websocket']['login_data']
        self.telegram_config = config['telegram']

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.listen_task: Optional[asyncio.Task] = None
        self.process_task: Optional[asyncio.Task] = None

        # 監控相關變數
        self.last_connection_check = 0
        self.last_quality_check = 0
        self.connection_failed_since: Optional[float] = None
        self.notification_intervals = [30, 60, 300, 600, 1800, 3600]
        self.next_notification_index = 0
        self.last_notification_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_delay = 300

        # 品質檢查相關 - 完全重新設計
        self.quality_metrics = QualityMetrics()
        self.ping_tracker: Dict[str, float] = {}  # 追蹤發出的 ping
        self.message_timestamps: List[float] = []  # 記錄訊息時間戳
        self.quality_check_timeout = 5  # 秒

        # 統計資料
        self.messages_received = 0
        self.messages_processed = 0
        self.last_message_time: Optional[float] = None

        self.setup_logging()

    def setup_logging(self):
        """設定日誌記錄"""
        log_format = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    self.config['logging']['file'], encoding='utf-8')
            ]
        )

    async def connect_and_login(self) -> bool:
        """建立連線並登入"""
        try:
            self.connection_state = ConnectionState.CONNECTING
            logging.info(f"嘗試連接到 WebSocket: {self.ws_url}")

            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=20,  # 啟用自動 ping，每20秒一次
                ping_timeout=10,   # ping 超時10秒
                close_timeout=10
            )
            self.connection_state = ConnectionState.CONNECTED

            # 發送登入訊息
            login_msg = json.dumps(self.login_data)

            print(f"send:{login_msg}", flush=True)
            await self.ws.send(login_msg)
            logging.info(f"WebSocket 連線成功並發送登入訊息")

            # 重置品質指標
            self.quality_metrics = QualityMetrics()

            # 啟動監聽和處理任務
            if self.listen_task is None or self.listen_task.done():
                self.listen_task = asyncio.create_task(
                    self._websocket_listener())
            if self.process_task is None or self.process_task.done():
                self.process_task = asyncio.create_task(
                    self._message_processor())

            self.reconnect_attempts = 0
            return True

        except Exception as e:
            logging.error(f"連線或登入失敗: {e}")
            await self.safe_close()
            return False

    async def _websocket_listener(self):
        """專門負責從 WebSocket 接收訊息並放入佇列"""
        logging.info("WebSocket 監聽器啟動!")

        try:
            async for message in self.ws:
                if message is None:
                    continue

                ws_message = WebSocketMessage(
                    content=message,
                    timestamp=time.time(),
                    message_type="websocket"
                )

                await self.message_queue.put(ws_message)
                self.messages_received += 1

                # 記錄最後收到訊息的時間
                self.last_message_time = time.time()

                # 記錄訊息時間戳用於計算訊息率
                self.message_timestamps.append(self.last_message_time)
                # 只保留最近1分鐘的記錄
                self.message_timestamps = [ts for ts in self.message_timestamps
                                           if time.time() - ts < 60]

            logging.info("WebSocket 連線已關閉，監聽任務結束")

        except asyncio.CancelledError:
            logging.warning("WebSocket 監聽任務已被取消!")
        except Exception as e:
            logging.error(f"WebSocket 監聽發生錯誤: {e}")
        finally:
            # 發送終止訊號
            poison_pill = WebSocketMessage(
                content=None,
                timestamp=time.time(),
                message_type="poison_pill"
            )
            await self.message_queue.put(poison_pill)
            self.connection_state = ConnectionState.DISCONNECTED

    async def _message_processor(self):
        """處理從 WebSocket 接收到的訊息"""
        logging.info("訊息處理器啟動!")

        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if message.message_type == "poison_pill" and message.content is None:
                    logging.info("收到終止訊號，訊息處理器結束")
                    break

                await self._process_websocket_message(message)
                self.messages_processed += 1
                self.message_queue.task_done()

        except asyncio.CancelledError:
            logging.warning("訊息處理任務已被取消!")
        except Exception as e:
            logging.error(f"訊息處理發生錯誤: {e}")

    async def _process_websocket_message(self, message: WebSocketMessage):
        """處理單個 WebSocket 訊息"""
        try:
            content = message.content

            # print(f"msg:{content}",flush=True)
            # 處理 PONG 回應 (文字格式)
            if isinstance(content, str) and "pong" in content.lower():
                await self._handle_pong_response(content, message.timestamp)
                return

            # 嘗試解析 JSON 訊息
            if isinstance(content, str) and content.strip().startswith('{'):
                try:
                    data = json.loads(content)
                    await self._handle_json_message(data, message.timestamp)
                    return
                except json.JSONDecodeError:
                    pass

            # 處理文字訊息
            await self._handle_text_message(content, message.timestamp)

        except Exception as e:
            logging.error(f"處理 WebSocket 訊息時發生錯誤: {e}")

    async def _handle_pong_response(self, content: str, timestamp: float):
        """處理 PONG 回應 (文字格式)"""
        logging.info(f"收到 PONG 回應: {content}")

        # 嘗試從內容中提取 ping_id
        parts = content.split(',')
        # if len(parts) >= 2 and parts[1].strip():
        if True:
            # ping_id = parts[1].strip()
            ping_id = client_id
            # if ping_id in self.ping_tracker:
            if True:
                response_time = (timestamp - self.ping_tracker[ping_id]) * 1000
                self.quality_metrics.response_time_ms = response_time
                self.quality_metrics.last_successful_ping = timestamp
                del self.ping_tracker[ping_id]  # 清理已回應的 ping

                logging.info(f"PONG 回應時間: {response_time:.2f}ms")

    async def _handle_json_message(self, data: Dict, timestamp: float):
        """處理 JSON 格式訊息"""
        action = data.get("action", "")
        
        # print(f"json_data:{data}",flush=True)
        # 處理 PONG 回應 (JSON 格式)
        if action == "pong":
            # ping_id = data.get("ping_id", "")
            ping_id = client_id
            if ping_id in self.ping_tracker:
                response_time = (timestamp - self.ping_tracker[ping_id]) * 1000
                self.quality_metrics.response_time_ms = response_time
                self.quality_metrics.last_successful_ping = timestamp
                del self.ping_tracker[ping_id]

                logging.info(f"PONG 回應時間: {response_time:.2f}ms")

        elif action == "login_response":
            status = data.get("status", "unknown")
            logging.info(f"登入回應: {status}")

        # 記錄其他重要訊息
        if action in ["update", "send"]:
            logging.info(f"處理業務訊息: {data}")
        else:
            logging.debug(f"處理 JSON 訊息: {data}")

    async def _handle_text_message(self, content: str, timestamp: float):
        """處理文字格式訊息"""
        if "ping" in content.lower() and "pong" not in content.lower():
            # 自動回應 ping
            await self._send_pong_response(content)
        elif "update" in content.lower():
            logging.info(f"收到更新訊息: {content}")
        else:
            logging.debug(f"處理文字訊息: {content}")

    async def _send_pong_response(self, ping_message: str):
        """回應 ping 請求"""
        try:
            if ping_message.startswith('{'):
                # JSON 格式
                pong_response = {
                    "action": "pong",
                    "timestamp": time.time(),
                    "response_to": "ping"
                }

                print(f"send:{json.dumps(pong_response)}", flush=True)
                await self.ws.send(json.dumps(pong_response))
            else:
                # 文字格式 - 回傳相同的內容但將 ping 改為 pong
                response = ping_message.replace(
                    'ping', 'pong').replace('PING', 'PONG')

                print(f"send:{response}", flush=True)
                await self.ws.send(response)
                logging.debug(f"自動回覆 PONG: {response}")
        except Exception as e:
            logging.error(f"發送 pong 回應失敗: {e}")

    # async def _send_reliable_ping(self) -> Optional[float]:
    #     """發送可靠的 ping 並等待回應"""
    #     if not self.ws or self.connection_state != ConnectionState.CONNECTED:
    #         return None

    #     try:
    #         # 生成唯一的 ping ID
    #         ping_id = f"ping_{int(time.time() * 1000)}"
    #         self.ping_tracker[ping_id] = time.time()

    #         # 發送 ping 訊息
    #         ping_data = {
    #             "action": "ping",
    #             "ping_id": ping_id,
    #             "timestamp": time.time(),
    #             "monitor": True
    #         }
    #         ping_msg = json.dumps(ping_data)

    #         await self.ws.send(ping_msg)
    #         logging.debug(f"發送 Ping: {ping_id}")

    #         # 等待回應
    #         wait_start = time.time()
    #         while time.time() - wait_start < self.quality_check_timeout:
    #             if ping_id not in self.ping_tracker:  # 已被回應處理器移除
    #                 response_time = self.quality_metrics.response_time_ms
    #                 logging.info(f"收到 Ping 回應: {response_time:.2f}ms")
    #                 return response_time
    #             await asyncio.sleep(0.1)

    #         # 超時，清理追蹤器
    #         if ping_id in self.ping_tracker:
    #             del self.ping_tracker[ping_id]
    #             logging.warning(f"Ping 超時: {ping_id},{time.time() - wait_start}")

    #         return None

    #     except Exception as e:
    #         logging.error(f"發送 Ping 失敗: {e}")
    #         if ping_id in self.ping_tracker:
    #             del self.ping_tracker[ping_id]
    #         return None

    def _calculate_message_rate(self) -> float:
        """計算每分鐘的訊息率"""
        now = time.time()
        recent_messages = [
            ts for ts in self.message_timestamps if now - ts < 60]
        return len(recent_messages) / 60.0  # 訊息/秒

    # async def check_connection_quality(self) -> Dict[str, Any]:
    #     """可靠的連線品質檢查"""
    #     if self.connection_state != ConnectionState.CONNECTED or not self.ws:
    #         return {
    #             "response_time_ms": None,
    #             "quality_ok": False,
    #             "reason": "not_connected"
    #         }

    #     # 方法1: 發送自訂 ping 並等待回應
    #     response_time = await self._send_reliable_ping()

    #     if response_time is not None:
    #         return {
    #             "response_time_ms": response_time,
    #             "quality_ok": response_time < 1000,  # 1秒內為良好
    #             "method": "reliable_ping",
    #             "message_rate": self._calculate_message_rate()
    #         }

    #     # 方法2: 檢查 WebSocket 連線狀態
    #     try:
    #         # 發送一個簡單的測試訊息
    #         test_msg = json.dumps({"action": "test", "timestamp": time.time()})
    #         await self.ws.send(test_msg)

    #         # 如果有收到任何訊息，認為連線基本正常
    #         if self.last_message_time and (time.time() - self.last_message_time) < 30:
    #             message_rate = self._calculate_message_rate()
    #             return {
    #                 "response_time_ms": None,
    #                 "quality_ok": True,
    #                 "method": "activity_based",
    #                 "message_rate": message_rate,
    #                 "reason": f"recent_activity_{message_rate:.1f}_msgs_per_sec"
    #             }

    #         return {
    #             "response_time_ms": None,
    #             "quality_ok": False,
    #             "method": "activity_check",
    #             "reason": "no_recent_activity"
    #         }

    #     except Exception as e:
    #         logging.error(f"品質檢查異常: {e}")
    #         return {
    #             "response_time_ms": None,
    #             "quality_ok": False,
    #             "reason": f"exception: {str(e)}"
    #         }

    async def safe_close(self):
        """安全關閉連線和任務"""
        self.connection_state = ConnectionState.DISCONNECTED

        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
        if self.process_task and not self.process_task.done():
            self.process_task.cancel()

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None

        # 清空佇列和追蹤器
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except:
                break
        self.ping_tracker.clear()

    async def send_telegram_notification(self, message: str):
        """發送 Telegram 通知"""
        url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
        data = {
            "chat_id": self.telegram_config['chat_id'],
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        logging.info("Telegram 通知發送成功")
                    else:
                        error_text = await response.text()
                        logging.error(f"Telegram 通知發送失敗: {error_text}")
        except Exception as e:
            logging.error(f"發送 Telegram 通知時發生錯誤: {e}")

    def should_send_notification(self) -> bool:
        """判斷是否應該發送通知"""
        if self.connection_failed_since is None:
            return False

        failure_duration = time.time() - self.connection_failed_since

        if self.next_notification_index >= len(self.notification_intervals):
            interval = self.notification_intervals[-1]
            return (time.time() - self.last_notification_time) >= interval

        current_interval = self.notification_intervals[self.next_notification_index]
        return failure_duration >= current_interval

    async def handle_connection_failure(self):
        """處理連線失敗邏輯"""
        current_time = time.time()

        if self.connection_failed_since is None:
            self.connection_failed_since = current_time
            self.next_notification_index = 0
            logging.warning("開始記錄連線失敗時間")

        if self.should_send_notification():
            downtime = int(current_time - self.connection_failed_since)
            message_rate = self._calculate_message_rate()
            message = (
                f"🔴 WebSocket 連線異常\n"
                f"• 伺服器: {self.ws_url}\n"
                f"• 持續時間: {downtime} 秒\n"
                f"• 訊息率: {message_rate:.2f} msg/秒\n"
                f"• 最後檢查: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.send_telegram_notification(message)
            self.last_notification_time = current_time
            self.next_notification_index += 1
            logging.warning(f"發送連線異常通知，下次通知索引: {self.next_notification_index}")

    async def handle_connection_recovery(self):
        """處理連線恢復邏輯"""
        if self.connection_failed_since is not None:
            downtime = int(time.time() - self.connection_failed_since)
            current_response_time = self.quality_metrics.response_time_ms or 0
            message = (
                f"🟢 WebSocket 連線恢復\n"
                f"• 伺服器: {self.ws_url}\n"
                f"• 中斷時間: {downtime} 秒\n"
                f"• 回應時間: {current_response_time:.2f}ms\n"
                f"• 恢復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.send_telegram_notification(message)

            # 重置狀態
            self.connection_failed_since = None
            self.next_notification_index = 0
            self.last_notification_time = 0
            logging.info("連線恢復，重置通知狀態")

    async def attempt_reconnect(self) -> bool:
        """嘗試重新連線"""
        if self.reconnect_attempts > 0:
            delay = min(2 ** self.reconnect_attempts, self.max_reconnect_delay)
            logging.info(f"重連嘗試 #{self.reconnect_attempts}, 等待 {delay} 秒")
            await asyncio.sleep(delay)

        success = await self.connect_and_login()
        if success:
            self.reconnect_attempts = 0
            return True
        else:
            self.reconnect_attempts += 1
            return False

    def log_check_result(self, check_type: str, success: bool, details: Dict[str, Any]):
        """記錄檢查結果"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "check_type": check_type,
            "success": success,
            "connection_state": self.connection_state.value,
            "messages_received": self.messages_received,
            "messages_processed": self.messages_processed,
            "server": self.ws_url,
            **details
        }

        # JSON 格式記錄
        json_log_file = self.config['logging']['file'].replace(
            '.log', '_json.log')
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"寫入 JSON 日誌失敗: {e}")

        # 根據結果輸出適當的日誌
        if check_type == "連線品質":
            if success and details.get("response_time_ms") is not None:
                logging.info(
                    f"✅ 連線品質良好 - 回應時間: {details['response_time_ms']:.2f}ms")
            elif success:
                # logging.info(f"⚠️ 連線基本正常 - {details.get('reason', '未知原因')}")
                pass
            else:
                logging.warning(f"❌ 連線品質異常 - {details}")
        else:
            status = "成功" if success else "失敗"
            logging.info(f"{check_type}檢查{status}: {details}")

    # async def run_monitoring(self):
    #     """主監控循環"""
    #     logging.info("啟動可靠版 WebSocket 監控程式")

    #     # 初始連線
    #     initial_success = await self.connect_and_login()
    #     if not initial_success:
    #         logging.error("初始連線失敗，開始重連流程")
    #         self.connection_failed_since = time.time()

    #     while True:
    #         try:
    #             current_time = time.time()

    #             # 連線狀態檢查（每10分鐘）
    #             if current_time - self.last_connection_check >= 600:
    #                 if self.connection_state != ConnectionState.CONNECTED:
    #                     logging.info("執行定期連線狀態檢查 - 目前斷線")
    #                     reconnect_success = await self.attempt_reconnect()
    #                     if reconnect_success:
    #                         await self.handle_connection_recovery()
    #                     else:
    #                         await self.handle_connection_failure()
    #                 else:
    #                     # 連線正常，記錄狀態
    #                     self.log_check_result("連線狀態", True, {
    #                         "state": self.connection_state.value,
    #                         "active": True
    #                     })

    #                 self.last_connection_check = current_time

    #             # 連線品質檢查（每1分鐘，僅在連線狀態下）
    #             if (self.connection_state == ConnectionState.CONNECTED and
    #                 current_time - self.last_quality_check >= 60):

    #                 quality_result = await self.check_connection_quality()

    #                 self.log_check_result("連線品質", quality_result["quality_ok"], quality_result)
    #                 self.last_quality_check = current_time

    #             # 即時重連機制
    #             if (self.connection_state == ConnectionState.DISCONNECTED and
    #                 self.connection_failed_since is None):
    #                 logging.info("連線中斷，立即嘗試重新連線")
    #                 self.connection_failed_since = current_time
    #                 reconnect_success = await self.attempt_reconnect()
    #                 if not reconnect_success:
    #                     await self.handle_connection_failure()

    #             await asyncio.sleep(1)

    #         except Exception as e:
    #             logging.error(f"監控循環發生錯誤: {e}")
    #             await asyncio.sleep(5)

    async def _send_reliable_ping(self) -> Optional[float]:
        """修復版：非阻塞Ping，只發送不等待"""
        if not self.ws or self.connection_state != ConnectionState.CONNECTED:
            return None

        try:
            # 使用伺服器支援的簡單格式
            # ping_id = f"ping_{int(time.time() * 1000)}"
            ping_id = client_id

            self.ping_tracker[ping_id] = time.time()

            # ✅ 修復：使用文字格式（伺服器更可能支援）
            # ping_msg = f"ping,{ping_id}"
            ping_msg = f"{client_id},ping"
            
            print(f"send:{ping_msg}", flush=True)
            await self.ws.send(ping_msg)
            logging.debug(f"發送 Ping: {ping_msg}")

            return time.time()  # 立即返回發送時間，不阻塞

        except Exception as e:
            logging.error(f"發送 Ping 失敗: {e}")
            return None

    async def check_connection_quality(self) -> Dict[str, Any]:
        """修復版：多層級非阻塞檢查"""
        if self.connection_state != ConnectionState.CONNECTED or not self.ws:
            return {"response_time_ms": None, "quality_ok": False, "reason": "not_connected"}

        now = time.time()

        # ✅ 方法1：檢查最近Pong（最快，0.01秒）
        if (self.quality_metrics.last_successful_ping and
                now - self.quality_metrics.last_successful_ping < 30):
            print(f"方法1:{now - self.quality_metrics.last_successful_ping}", flush=True)
            return {
                "response_time_ms": self.quality_metrics.response_time_ms,
                "quality_ok": True,
                "method": "recent_pong",
                "reason": "pong_ok"
            }

        # ✅ 方法2：檢查最近訊息活動（0.1秒）
        if (self.last_message_time and now - self.last_message_time < 30):
            print(f"方法2:{now - self.last_message_time}", flush=True)
            return {
                "response_time_ms": None,
                "quality_ok": True,
                "method": "recent_activity",
                "message_rate": self._calculate_message_rate(),
                "reason": "activity_ok"
            }

        # ✅ 方法3：發送Ping（非阻塞，記錄等待下次檢查）
        ping_sent_time = await self._send_reliable_ping()
        print(f"方法3:{ping_sent_time}", flush=True)
        if ping_sent_time:
            return {
                "response_time_ms": None,
                "quality_ok": True,  # 先假設OK，等回應再驗證
                "method": "ping_sent",
                "reason": "ping_pending",
                "ping_sent": ping_sent_time
            }

        # ❌ 方法4：連線已斷
        return {"response_time_ms": None, "quality_ok": False, "reason": "send_failed"}

    async def run_monitoring(self):
        """修復版：優化檢查頻率，防止阻塞"""
        logging.info("🚀 啟動優化版 WebSocket 監控")

        # 初始連線
        initial_success = await self.connect_and_login()
        if not initial_success:
            self.connection_failed_since = time.time()

        last_ping_time = 0  # 手動Ping計時器

        while True:
            try:
                current_time = time.time()

                # ✅ 修復：狀態檢查改為每30秒（之前10分鐘太長）
                if current_time - self.last_connection_check >= 30:
                    if self.connection_state != ConnectionState.CONNECTED:
                        logging.info("🔄 斷線重連")

                        print(" _C0_ ", end='', flush=True)

                        reconnect_success = await self.attempt_reconnect()
                        if reconnect_success:
                            await self.handle_connection_recovery()
                        else:
                            await self.handle_connection_failure()
                    self.last_connection_check = current_time

                # ✅ 修復：品質檢查改為每15秒（之前1分鐘太長）
                if (self.connection_state == ConnectionState.CONNECTED and
                        current_time - self.last_quality_check >= 15):

                    print(" _C1_ ", end='', flush=True)

                    quality_result = await self.check_connection_quality()
                    quality_ok = quality_result["quality_ok"]

                    self.log_check_result("連線品質", quality_ok, quality_result)
                    self.last_quality_check = current_time

                    # ✅ 新增：品質差時立即重連
                    if not quality_ok and quality_result["reason"] != "ping_pending":
                        logging.warning(f"❌ 品質異常: {quality_result['reason']}")
                        await self.attempt_reconnect()

                # ✅ 新增：手動Ping輔助（每20秒）
                # if (self.connection_state == ConnectionState.CONNECTED and current_time - last_ping_time >= 20):
                if (self.connection_state == ConnectionState.CONNECTED and current_time - last_ping_time >= 60):

                    print(" _c2_ ", end='', flush=True)

                    await self._send_reliable_ping()
                    last_ping_time = current_time

                # ✅ 修復：睡眠改為0.5秒（之前1秒）
                await asyncio.sleep(0.5)

            except Exception as e:
                logging.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(2)


cmb_password = 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='  # SOFT CMB Caller
# client_id = 'z0001'
client_id = 'z0002'
TOKEN = '7953139290:AAEFzEJpPK2DaUnUZEg6gOOMIYFdef9DZ84'
CHAT_ID = '6597541679'

# 配置範例
CONFIG = {
    "websocket": {
        "url": "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/",
        "login_data": {
            "action": "login",
            "vendor_id": "tawe",
            "caller_id": f"{client_id}",
            "password": f"{cmb_password}",
            "uuid": "monitor_001"
        }
    },
    "telegram": {
        "bot_token": TOKEN,
        "chat_id": CHAT_ID
    },
    "logging": {
        "file": "websocket_monitor.log"
    }
}


# # 使用範例
# CONFIG = {
#     "websocket": {
#         "url": "wss://your-websocket-server.com/ws",
#         "login_data": {
#             "action": "login",
#             "vendor_id": "tawe",
#             "caller_id": "z0002",
#             "password": "your_password",
#             "uuid": "monitor_001"
#         }
#     },
#     "telegram": {
#         "bot_token": "your_bot_token",
#         "chat_id": "your_chat_id"
#     },
#     "logging": {
#         "file": "reliable_websocket_monitor.log"
#     }
# }

async def main():
    monitor = ReliableWebSocketMonitor(CONFIG)
    try:
        await monitor.run_monitoring()
    except KeyboardInterrupt:
        logging.info("程式被使用者中斷")
        await monitor.safe_close()
    except Exception as e:
        logging.error(f"程式執行錯誤: {e}")
        await monitor.safe_close()

if __name__ == "__main__":
    asyncio.run(main())
