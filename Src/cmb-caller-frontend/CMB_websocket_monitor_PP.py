'''

2025/10/28
OK

'''

import asyncio
import websockets
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import aiohttp
from enum import Enum
from dataclasses import dataclass
import functools
import sys
import os

print = functools.partial(print, flush=True)

try:
    __IPYTHON__  # 如果在 Jupyter 中，這個變數會存在
    import nest_asyncio
    nest_asyncio.apply()
    print("nest_asyncio 已啟用 (Jupyter 環境)", flush=True)
except NameError:
    pass  # 在標準 Python 環境中，什麼都不做
    print("nest_asyncio 未啟用 (非 Jupyter 環境)", flush=True)

# 連線狀態枚舉
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

class WebSocketMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ws_url = config['websocket']['url']
        self.login_data = config['websocket']['login_data']
        self.telegram_config = config['telegram']

        self.client_id = self.login_data.get('caller_id', 'monitor')

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.listen_task: Optional[asyncio.Task] = None
        self.process_task: Optional[asyncio.Task] = None

        self.last_connection_check = 0
        self.last_quality_check = 0
        self.connection_failed_since: Optional[float] = None
        self.notification_intervals = config['monitoring']['notification_intervals']
        self.next_notification_index = 0
        self.last_notification_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_delay = config['monitoring']['reconnect_max_delay']
        self.max_reconnect_attempts = 10000

        self.ping_sent_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None
        self.ping_response_times: List[float] = []
        self.quality_check_timeout = 10

        self.messages_received = 0
        self.messages_processed = 0
        self.last_message_time: Optional[float] = None

        self._last_status_report = 0

        self.performance_stats = {
            'total_reconnects': 0,
            'total_messages': 0,
            'total_errors': 0,
            'start_time': time.time(),
            'last_reset_time': time.time()
        }

        self._last_memory_check = 0

        self.state_change_time = time.time()
        print(f"WebSocketMonitor init: self.ws_url -> '{self.ws_url}'")

        self.last_reconnect_attempt = 0
        self.reconnect_interval = 5
        self.continuous_reconnect_enabled = True

    async def run_monitoring(self):
        # await asyncio.sleep(10)
        logging.info("啟動 WebSocket 監控程式")
        print("🟡 啟動 WebSocket 監控程式...")

        consecutive_errors = 0
        max_consecutive_errors = 5

        initial_success = await self.connect_and_login()
        if not initial_success:
            print("🔴 初始連線失敗，開始重連流程")
            logging.error("初始連線失敗，開始重連流程")
            self.connection_failed_since = time.time()

        while True:
            try:
                current_time = time.time()

                if consecutive_errors >= max_consecutive_errors:
                    logging.error("連續錯誤過多，重啟監控循環")
                    await self.safe_close()
                    await asyncio.sleep(10)
                    consecutive_errors = 0
                    await self.connect_and_login()
                    continue

                if (self.continuous_reconnect_enabled and
                    self.connection_state == ConnectionState.DISCONNECTED and
                    current_time - self.last_reconnect_attempt >= self.reconnect_interval):

                    await self._handle_continuous_reconnect(current_time)

                if current_time - self.last_connection_check >= 600:
                    if self.connection_state != ConnectionState.CONNECTED:
                        print(f"🟡 [{datetime.now().strftime('%H:%M:%S')}] 定期連線狀態檢查 - 斷線中")
                        logging.info("定期連線狀態檢查 - 斷線中")
                        reconnect_success = await self.attempt_reconnect()
                        if not reconnect_success:
                            await self.handle_connection_failure()
                    else:
                        self.log_check_result("連線狀態", True, {
                            "state": self.connection_state.value,
                            "active": True
                        })
                    self.last_connection_check = current_time

                if (self.connection_state == ConnectionState.CONNECTED and
                    current_time - self.last_quality_check >= self.config['monitoring']['quality_check_interval']):

                    try:
                        quality_result = await self.check_connection_quality()
                        self.log_check_result("連線品質", quality_result["quality_ok"], quality_result)
                        self.last_quality_check = current_time
                    except Exception as e:
                        logging.error(f"品質檢查過程錯誤: {e}")
                        self.log_check_result("連線品質", False, {"reason": f"check_exception: {str(e)}", "method": "exception"})

                if (self.connection_failed_since is not None and
                    self.connection_state != ConnectionState.CONNECTED):
                    await self.handle_connection_failure()

                await self._check_memory_usage()

                if current_time - self._last_status_report >= self.config['monitoring']['status_report_interval']:
                    self._report_current_status()
                    self._last_status_report = current_time

                consecutive_errors = 0
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logging.info("監控循環被取消")
                break
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"監控循環錯誤 ({consecutive_errors}/{max_consecutive_errors}): {e}")
                self.performance_stats['total_errors'] += 1
                await asyncio.sleep(5)

    async def _handle_continuous_reconnect(self, current_time: float):
        print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 持續重連嘗試 (#{self.reconnect_attempts + 1})")
        logging.info(f"持續重連嘗試 (#{self.reconnect_attempts + 1})")

        if self.connection_failed_since is None:
            self.connection_failed_since = current_time

        self.last_reconnect_attempt = current_time
        reconnect_success = await self.attempt_reconnect()

        if not reconnect_success:
            await self.handle_connection_failure()

    async def connect_and_login(self) -> bool:
        try:
            logging.info(f"嘗試連接到 WebSocket: {self.ws_url}")
            self._update_connection_state(ConnectionState.CONNECTING)

            try:
                self.ws = await asyncio.wait_for(
                    websockets.connect(
                        self.ws_url,
                        ping_interval=None,
                        close_timeout=10
                    ),
                    timeout=15
                )
            except asyncio.TimeoutError:
                logging.error("WebSocket 連線超時")
                return False

            self._update_connection_state(ConnectionState.CONNECTED)

            login_msg = json.dumps(self.login_data)
            await self.ws.send(login_msg)
            logging.info("WebSocket 登入訊息發送成功")

            if self.listen_task is None or self.listen_task.done():
                self.listen_task = asyncio.create_task(self._websocket_listener())
            if self.process_task is None or self.process_task.done():
                self.process_task = asyncio.create_task(self._message_processor())

            self.reconnect_attempts = 0
            self._reset_notification_state()
            return True

        except Exception as e:
            logging.error(f"連線或登入失敗: {e}")
            await self.safe_close()
            return False

    async def _websocket_listener(self):
        logging.info("WebSocket 監聽器啟動")
        try:
            async for message in self.ws:
                if message is None:
                    continue

                if len(message) > 10 * 1024 * 1024:
                    logging.warning(f"訊息過大: {len(message)} bytes，略過")
                    continue

                # 記錄最後收到訊息的時間
                self.last_message_time = time.time()
                
                # 檢查是否是 pong 回應
                if isinstance(message, str) and "pong" in message.lower():
                    self.last_pong_time = time.time()
                    logging.debug(f"收到 pong 回應: {message}")

                ws_message = WebSocketMessage(
                    content=message, 
                    timestamp=time.time(), 
                    message_type="websocket"
                )

                if self.message_queue.full():
                    try:
                        self.message_queue.get_nowait()
                        logging.warning("訊息佇列已滿，丟棄最舊訊息")
                    except:
                        pass

                await self.message_queue.put(ws_message)
                self.messages_received += 1
                self.performance_stats['total_messages'] += 1

            logging.info("WebSocket 連線關閉，監聽結束")

        except websockets.exceptions.ConnectionClosedOK:
            logging.info("WebSocket 正常關閉")
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"WebSocket 連線非正常關閉: {e}")
        except Exception as e:
            logging.error(f"監聽發生錯誤: {e}")
            self.performance_stats['total_errors'] += 1
        finally:
            await self._cleanup_listener()
    
    async def _cleanup_listener(self):
        poison_pill = WebSocketMessage(content=None, timestamp=time.time(), message_type="poison_pill")
        try:
            await self.message_queue.put(poison_pill)
        except Exception as e:
            logging.warning(f"佇列加入終止訊號失敗: {e}")
    
        self._update_connection_state(ConnectionState.DISCONNECTED)
    
        try:
            if self.ws and self.ws.open:
                await self.ws.close(code=1000, reason="Client cleanup")
        except Exception as e:
            logging.warning(f"關閉連線例外: {e}")
    
        if not isinstance(sys.exc_info()[1], asyncio.CancelledError):
            await asyncio.sleep(1.0)
            logging.info("監聽器觸發重新連線")
            await self.attempt_reconnect()

    async def _message_processor(self):
        logging.info("訊息處理器啟動")
        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if message.message_type == "poison_pill" and message.content is None:
                    logging.info("收到終止訊號，訊息處理結束")
                    break

                await self._process_websocket_message(message)
                self.messages_processed += 1
                self.message_queue.task_done()

        except asyncio.CancelledError:
            logging.warning("訊息處理任務取消")
        except Exception as e:
            logging.error(f"訊息處理錯誤: {e}")
            self.performance_stats['total_errors'] += 1

    async def _process_websocket_message(self, message: WebSocketMessage):
        try:
            content = message.content
            if isinstance(content, str) and "pong" in content.lower():
                await self._handle_pong_message(content, message.timestamp)
                return

            if isinstance(content, str) and content.strip().startswith('{'):
                try:
                    data = json.loads(content)
                    await self._handle_json_message(data, message.timestamp)
                    return
                except json.JSONDecodeError:
                    pass

            await self._handle_text_message(content, message.timestamp)

        except Exception as e:
            logging.error(f"處理訊息錯誤: {e}")
            self.performance_stats['total_errors'] += 1

    async def _handle_pong_message(self, content: str, timestamp: float):
        if self.ping_sent_time is not None:
            response_time = (timestamp - self.ping_sent_time) * 1000
            self.ping_response_times.append(response_time)
            if len(self.ping_response_times) > 10:
                self.ping_response_times.pop(0)
            self.last_pong_time = timestamp
            avg_response = sum(self.ping_response_times) / len(self.ping_response_times)
            logging.info(f"Pong 回應時間: {response_time:.2f}ms (平均: {avg_response:.2f}ms)")
        else:
            logging.debug("非等待期收到 PONG")

    async def _handle_json_message(self, data: Dict, timestamp: float):
        action = data.get("action", "")
        if action == "pong":
            if self.ping_sent_time:
                response_time = (timestamp - self.ping_sent_time) * 1000
                self.ping_response_times.append(response_time)
                if len(self.ping_response_times) > 10:
                    self.ping_response_times.pop(0)
                self.last_pong_time = timestamp
                self.ping_sent_time = None
                avg_response = sum(self.ping_response_times) / len(self.ping_response_times)
                logging.info(f"Pong 回應時間: {response_time:.2f}ms (平均: {avg_response:.2f}ms)")
        elif action == "login_response":
            status = data.get("status", "unknown")
            logging.info(f"登入回應: {status}")
            if status == "OK" and self.connection_failed_since is not None:
                self._reset_notification_state()

        logging.info(f"處理 JSON 訊息: {data}")

    async def _handle_text_message(self, content: str, timestamp: float):
        if "ping" in content.lower() and "pong" not in content.lower():
            await self._send_pong_response(content)
        else:
            logging.debug(f"處理文字訊息: {content[:100]}{'...' if len(content) > 100 else ''}")

    async def _send_pong_response(self, ping_message: str):
        try:
            if "ping" in ping_message.lower():
                if ping_message.startswith('{'):
                    pong_response = {
                        "action": "pong",
                        "timestamp": time.time(),
                        "response_to": "ping"
                    }
                    await self.ws.send(json.dumps(pong_response))
                else:
                    parts = ping_message.split(',')
                    if len(parts) >= 2:
                        response = f"pong,{parts[1]}" if parts[1] else "pong"
                        await self.ws.send(response)
        except Exception as e:
            logging.error(f"發送 pong 回應失敗: {e}")
            self.performance_stats['total_errors'] += 1

    async def check_connection_quality(self) -> Dict[str, Any]:
        """檢查連線品質"""
        # 首先檢查連線狀態
        if (self.connection_state != ConnectionState.CONNECTED or 
            self.ws is None or 
            not self.ws.open):
            return {
                "response_time_ms": None,
                "quality_ok": False,
                "reason": "not_connected_or_closed"
            }

        try:
            # 方法1: 使用內建 ping/pong
            try:
                ping_start = time.time()
                await asyncio.wait_for(self.ws.ping(), timeout=5.0)
                
                # 等待 pong 回應
                wait_start = time.time()
                while time.time() - wait_start < 5:
                    if (self.last_pong_time is not None and 
                        self.last_pong_time > ping_start):
                        response_time = (self.last_pong_time - ping_start) * 1000
                        quality_ok = response_time < 1000
                        return {
                            "response_time_ms": round(response_time, 2),
                            "quality_ok": quality_ok,
                            "method": "builtin_ping"
                        }
                    await asyncio.sleep(0.1)
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                logging.debug("內建 ping 方法失敗，嘗試自訂 ping")

            # 方法2: 使用自訂 ping/pong 訊息
            self.ping_sent_time = time.time()
            ping_msg = f"{self.client_id},ping"
            logging.info(f"send:{ping_msg}")
            
            try:
                await asyncio.wait_for(self.ws.send(ping_msg), timeout=5.0)
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                return {
                    "response_time_ms": None,
                    "quality_ok": False,
                    "reason": "send_timeout"
                }

            # 等待自訂 pong 回應
            wait_start = time.time()
            while time.time() - wait_start < self.quality_check_timeout:
                if (self.last_pong_time is not None and
                    self.ping_sent_time is not None and
                    self.last_pong_time > self.ping_sent_time):

                    response_time = (self.last_pong_time - self.ping_sent_time) * 1000
                    quality_ok = response_time < 1000

                    # 重置狀態
                    self.last_pong_time = None
                    self.ping_sent_time = None

                    return {
                        "response_time_ms": round(response_time, 2),
                        "quality_ok": quality_ok,
                        "method": "custom_ping"
                    }
                await asyncio.sleep(0.1)

            # 方法3: 啟發式檢查 - 如果有最近收到的訊息，認為連線正常
            if self.last_message_time and (time.time() - self.last_message_time) < 120:
                return {
                    "response_time_ms": None,
                    "quality_ok": True,
                    "method": "heuristic",
                    "reason": "recent_messages_received"
                }

            # 所有方法都失敗
            logging.warning("所有品質檢查方法失敗")
            return {
                "response_time_ms": None, 
                "quality_ok": False, 
                "reason": "all_methods_failed"
            }

        except Exception as e:
            logging.error(f"品質檢查異常: {e}")
            self.performance_stats['total_errors'] += 1
            return {
                "response_time_ms": None, 
                "quality_ok": False, 
                "reason": f"exception: {str(e)}"
            }

    def log_check_result(self, check_type: str, success: bool, details: Dict[str, Any]):
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

        json_log_file = self.config['logging']['file'].replace('.log', '_json.log')
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"寫入 JSON 日誌失敗: {e}")

        if check_type == "連線品質":
            if details.get("quality_ok"):
                if details.get("response_time_ms") is not None:
                    logging.info(f"連線品質良好: 延遲 {details['response_time_ms']:.2f}ms (方法: {details['method']})")
                else:
                    logging.info(f"連線品質良好: 方法 {details['method']} (原因: {details.get('reason', 'N/A')})")
            else:
                logging.warning(f"連線品質檢查失敗: {details}")
        else:
            status = "成功" if success else "失敗"
            logging.info(f"{check_type}檢查{status}: {details}")

    async def safe_close(self):
        self._update_connection_state(ConnectionState.DISCONNECTED)
        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        if self.process_task and not self.process_task.done():
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            try:
                await self.ws.close(code=1000, reason="Client safe close")
            except:
                pass
            self.ws = None

        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except:
                break

        logging.info("安全關閉完成")

    async def send_telegram_notification(self, message: str):
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
                        logging.error(f"Telegram 通知失敗: {error_text}")
        except asyncio.TimeoutError:
            logging.error("Telegram 通知逾時")
        except Exception as e:
            logging.error(f"Telegram 發送錯誤: {e}")

    def should_send_notification(self) -> bool:
        if (self.connection_failed_since is None or
            self.connection_state == ConnectionState.CONNECTED):
            return False

        failure_duration = time.time() - self.connection_failed_since

        if self.next_notification_index >= len(self.notification_intervals):
            interval = self.notification_intervals[-1]
            return (time.time() - self.last_notification_time) >= interval

        current_interval = self.notification_intervals[self.next_notification_index]
        return failure_duration >= current_interval

    async def handle_connection_failure(self):
        current_time = time.time()

        if self.connection_failed_since is None:
            self.connection_failed_since = current_time
            self.next_notification_index = 0
            logging.warning("開始記錄連線失敗時間")
            print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 連線失敗計時開始...")

        if self.should_send_notification():
            downtime = int(current_time - self.connection_failed_since)
            message = (
                f"***** 監控程式 Version *****\n"
                f"🔴 WebSocket 連線異常\n"
                f"• 伺服器: {self.ws_url}\n"
                f"• 持續時間: {downtime} 秒\n"
                f"• 最後檢查: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.send_telegram_notification(message)
            self.last_notification_time = current_time
            self.next_notification_index += 1

            print(f"📢 [{datetime.now().strftime('%H:%M:%S')}] 已發送 Telegram 通知 (斷線 {downtime} 秒)")
            logging.warning(f"發送斷線通知，下次通知索引: {self.next_notification_index}")

    def _update_connection_state(self, new_state: ConnectionState):
        old_state = self.connection_state
        self.connection_state = new_state

        if old_state != new_state:
            status_colors = {
                ConnectionState.CONNECTED: "🟢",
                ConnectionState.DISCONNECTED: "🔴",
                ConnectionState.CONNECTING: "🟡",
                ConnectionState.RECONNECTING: "🟠"
            }
            color = status_colors.get(new_state, "⚪")
            print(f"\n{color} [{datetime.now().strftime('%H:%M:%S')}] 連線狀態: {old_state.value} → {new_state.value}")
            self.state_change_time = time.time()

            if new_state == ConnectionState.DISCONNECTED:
                print("🔴 檢測到斷線！立即嘗試重新連線...")
            elif new_state == ConnectionState.CONNECTED:
                print("🟢 連線成功建立！")
                if self.connection_failed_since is not None:
                    self._reset_notification_state()

    def _reset_notification_state(self):
        if self.connection_failed_since is not None:
            downtime = int(time.time() - self.connection_failed_since)
            if downtime > 5:
                recovery_message = (
                    f"***** 監控程式 Version *****\n"
                    f"🟢 WebSocket 連線恢復\n"
                    f"• 伺服器: {self.ws_url}\n"
                    f"• 中斷時間: {downtime} 秒\n"
                    f"• 恢復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                asyncio.create_task(self._send_telegram_notification_async(recovery_message))
                print(f"🟢 [{datetime.now().strftime('%H:%M:%S')}] 連線恢復！中斷時間: {downtime} 秒")

            self.connection_failed_since = None
            self.next_notification_index = 0
            self.last_notification_time = 0
            logging.info("連線恢復，重置通知狀態")

    async def _send_telegram_notification_async(self, message: str):
        try:
            await self.send_telegram_notification(message)
        except Exception as e:
            logging.error(f"發送恢復通知失敗: {e}")

    async def attempt_reconnect(self) -> bool:
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logging.error(f"達成最大重連次數 {self.max_reconnect_attempts}，停止重連")
            return False

        if self.reconnect_attempts > 0:
            delay = 1.0
            print(f"🟡 [{datetime.now().strftime('%H:%M:%S')}] 重連嘗試 #{self.reconnect_attempts}, 等待 {delay} 秒")
            logging.info(f"重連嘗試 #{self.reconnect_attempts}, 等待 {delay} 秒")
            await asyncio.sleep(delay)

        try:
            try:
                async with asyncio.timeout(30):
                    await self.safe_close()
                    success = await self.connect_and_login()
            except asyncio.TimeoutError:
                logging.error("重連操作超時")
                self.reconnect_attempts += 1
                return False

            if success:
                print(f"🟢 [{datetime.now().strftime('%H:%M:%S')}] 重連成功！嘗試次數: {self.reconnect_attempts + 1}")
                logging.info(f"重連成功！嘗試次數: {self.reconnect_attempts + 1}")
                self.reconnect_attempts = 0
                self.performance_stats['total_reconnects'] += 1
                self._reset_notification_state()
                return True
            else:
                self.reconnect_attempts += 1
                print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 重連失敗，次數: {self.reconnect_attempts}")
                logging.warning(f"重連失敗，次數: {self.reconnect_attempts}")
                return False
        except Exception as e:
            logging.error(f"重連錯誤: {e}")
            self.reconnect_attempts += 1
            self.performance_stats['total_errors'] += 1
            return False

    def _report_current_status(self):
        uptime = int(time.time() - self.performance_stats['start_time'])
        messages_per_minute = (self.messages_received / uptime * 60) if uptime > 0 else 0
        current_queue_size = self.message_queue.qsize()
        avg_latency = sum(self.ping_response_times) / len(self.ping_response_times) if self.ping_response_times else 0
        success_rate = (self.messages_processed / self.messages_received * 100) if self.messages_received > 0 else 100
        total_errors = self.performance_stats['total_errors']

        print(f"🟢 [{datetime.now().strftime('%H:%M:%S')}] 狀態報告：\n"
              f"• 運行時間: {uptime}秒\n"
              f"• 重新連線次數: {self.performance_stats['total_reconnects']}\n"
              f"• 訊息總計: {self.messages_received}\n"
              f"• 訊息處理: {self.messages_processed}\n"
              f"• 佇列大小: {current_queue_size}\n"
              f"• 平均延遲: {avg_latency:.2f}ms\n"
              f"• 成功率: {success_rate:.2f}%\n"
              f"• 錯誤次數: {total_errors}")

    async def _check_memory_usage(self):
        current_time = time.time()
        if current_time - self._last_memory_check > 3600:  # 每小時檢查一次
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                logging.info(f"記憶體使用量: {memory_mb:.2f} MB")
                
                # 如果記憶體使用超過 500MB，發出警告
                if memory_mb > 500:
                    logging.warning(f"記憶體使用量偏高: {memory_mb:.2f} MB")
            except ImportError:
                pass  # 如果沒有 psutil，跳過記憶體檢查
            self._last_memory_check = current_time

# 配置部分 - 使用環境變數增強安全性
client_id = 'z0001'
ws_url = ''

CONFIG = {
    "websocket": {
        "url": os.getenv('WEBSOCKET_URL', ws_url),
        "login_data": {
            "action": "login",
            "vendor_id": "tawe",
            "caller_id": os.getenv('CLIENT_ID', client_id),
            "password": os.getenv('CMB_PASSWORD', 'YV7X+xUEsMckopbXpp5sey+eosV8HYIGxa/fOS69/SU='),
            "uuid": "monitor_001"
        }
    },
    "telegram": {
        "bot_token": os.getenv('TELEGRAM_TOKEN', '7953139290:AAEFzEJpPK2DaUnUZEg6gOOMIYFdef9DZ84'),
        "chat_id": os.getenv('TELEGRAM_CHAT_ID', '6597541679')
    },
    "logging": {
        "file": os.getenv('LOG_FILE', 'websocket_monitor.log'),
        "level": os.getenv('LOG_LEVEL', 'INFO')
    },
    "monitoring": {
        "quality_check_interval": 120,  # 增加到 120 秒
        "status_report_interval": 1800,
        "reconnect_max_delay": 300,
        "notification_intervals": [30, 60, 300, 600, 1800, 3600]
    }
}

def setup_global_logging():
    """全域日誌設定"""
    log_format = '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    log_file = CONFIG['logging']['file']
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 設定日誌輪轉
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
    except ImportError:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    logging.basicConfig(
        level=getattr(logging, CONFIG['logging']['level']),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),
            file_handler
        ]
    )

# WebSocket 伺服器地址
ws_urls = {
    "local": "ws://localhost:38000",
    "trial": "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/",
    "live": "wss://cmb-caller-frontend-410240967190.asia-east1.run.app/"
}

# 選擇伺服器
target_env = "trial"

async def main():
    global target_env, ws_url

    # 先設定日誌
    setup_global_logging()
    
    # 檢查是否有命令列參數
    if len(sys.argv) > 1:
        param = sys.argv[1].lower()
        if param in ws_urls:
            target_env = param
            logging.info(f"從參數取得 '{param}'，使用對應的 WebSocket URL。")
            logging.info(f"使用 '{target_env}'。")
        else:
            logging.warning(f"無效的參數 '{param}'。將使用預設值 '{target_env}'。")
    else:
        logging.info(f"未提供參數，使用預設值 '{target_env}'。")
    
    ws_url = ws_urls[target_env]
    logging.info(f"程式啟動，將會連接到: {ws_url}")

    # 動態更新 CONFIG 中的 URL
    CONFIG["websocket"]["url"] = ws_url
    CONFIG["websocket"]["login_data"]["caller_id"] = client_id
    
    monitor = WebSocketMonitor(CONFIG)
    
    # 添加信號處理
    def signal_handler(signum, frame):
        logging.info(f"收到信號 {signum}，準備關閉...")
        asyncio.create_task(monitor.safe_close())
    
    try:
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except ImportError:
        pass  # Windows 可能不支援
    
    try:
        await monitor.run_monitoring()
    except KeyboardInterrupt:
        logging.info("程式被使用者中斷")
    except Exception as e:
        logging.error(f"程式執行錯誤: {e}")
    finally:
        # 確保資源清理
        await monitor.safe_close()
        logging.info("程式正常退出")

if __name__ == "__main__":
    asyncio.run(main())