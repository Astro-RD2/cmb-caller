'''
🟢 [11:13:06] 狀態: disconnected → connected
2025-10-28 11:13:06.545 [INFO] [root] 登入訊息已發送
🟢 重連成功！次數: 0

🟡 [11:13:06] 狀態: connected → connecting

🟢 [11:13:06] 狀態: connecting → connected
2025-10-28 11:13:06.869 [INFO] [root] 登入訊息已發送
🟢 重連成功！次數: 0

🟡 [11:13:07] 狀態: connected → connecting

🟢 [11:13:07] 狀態: connecting → connected
2025-10-28 11:13:07.106 [INFO] [root] 登入訊息已發送
🟢 重連成功！次數: 0

🟡 [11:13:07] 狀態: connected → connecting

🟢 [11:13:07] 狀態: connecting → connected
2025-10-28 11:13:07.600 [INFO] [root] 登入訊息已發送
🟢 重連成功！次數: 0
2025-10-28 11:13:25.812 [INFO] [root] Pong 回應時間: 9.00ms (平均: 8.36ms)
2025-10-28 11:13:25.887 [INFO] [root] 連線品質良好: 延遲 9.00ms (方法: custom_ping)
'''


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
import sys
import os
import functools
from math import floor, log10

print = functools.partial(print, flush=True)

print("CMB_websocket_monitor.py 程式啟動!", flush=True)

try:
    __IPYTHON__
    import nest_asyncio
    nest_asyncio.apply()
    print("nest_asyncio 已啟用 (Jupyter 環境)", flush=True)
except NameError:
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


class WebSocketMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ws_url = config['websocket']['url']
        self.login_data = config['websocket']['login_data']
        self.telegram_config = config['telegram']
        self.client_id = config['websocket']['login_data'].get('caller_id', 'monitor')

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.listen_task: Optional[asyncio.Task] = None
        self.process_task: Optional[asyncio.Task] = None

        # 監控變數
        self.last_connection_check = 0
        self.last_quality_check = 0
        self.connection_failed_since: Optional[float] = None
        self.notification_intervals = config['monitoring']['notification_intervals']
        self.next_notification_index = 0
        self.last_notification_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_delay = config['monitoring']['reconnect_max_delay']
        self.max_reconnect_attempts = 10000

        # 品質檢查
        self.ping_sent_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None
        self.ping_response_times: List[float] = []
        self.quality_check_timeout = 30

        # 統計
        self.messages_received = 0
        self.messages_processed = 0
        self.last_message_time: Optional[float] = None
        self._last_status_report = 0
        self.performance_stats = {
            'total_reconnects': 0, 'total_messages': 0, 'total_errors': 0,
            'start_time': time.time(), 'last_reset_time': time.time()
        }
        self._last_memory_check = 0

        # 連續品質失敗計數（主迴圈使用）
        self.consecutive_quality_failures = 0
        self.max_consecutive_quality_failures = 3

        self.state_change_time = time.time()
        self.last_reconnect_attempt = 0
        self.reconnect_interval = 5
        self.continuous_reconnect_enabled = True

    # === 延遲格式化：至少 3 位有效數字 ===
    def format_delay(self, ms: float) -> str:
        if ms == 0:
            return "0.00"
        magnitude = floor(log10(abs(ms)))
        precision = max(0, 2 - magnitude)  # 至少 3 位有效數字
        return f"{ms:.{precision}f}"

    async def run_monitoring(self):
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

                # 健康檢查
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("連續錯誤過多，重啟監控循環")
                    await self.safe_close()
                    await asyncio.sleep(10)
                    consecutive_errors = 0
                    await self.connect_and_login()
                    continue

                # 持續重連
                if (self.continuous_reconnect_enabled and
                    self.connection_state == ConnectionState.DISCONNECTED and
                    current_time - self.last_reconnect_attempt >= self.reconnect_interval):
                    await self._handle_continuous_reconnect(current_time)

                # 定期連線狀態檢查 (10分鐘)
                if current_time - self.last_connection_check >= 600:
                    if self.connection_state != ConnectionState.CONNECTED:
                        print(f"🟡 [{datetime.now().strftime('%H:%M:%S')}] 定期檢查 - 斷線中")
                        reconnect_success = await self.attempt_reconnect()
                        if not reconnect_success:
                            await self.handle_connection_failure()
                    else:
                        self.log_check_result("連線狀態", True, {"state": "connected", "active": True})
                    self.last_connection_check = current_time

                # 品質檢查 (60秒) + 連續失敗強制重連
                if (self.connection_state == ConnectionState.CONNECTED and
                    current_time - self.last_quality_check >= self.config['monitoring']['quality_check_interval']):
                    quality_result = await self.check_connection_quality()
                    self.log_check_result("連線品質", quality_result["quality_ok"], quality_result)
                    self.last_quality_check = current_time

                    if not quality_result["quality_ok"]:
                        self.consecutive_quality_failures += 1
                        logging.warning(f"品質檢查失敗次數: {self.consecutive_quality_failures}")
                        if self.consecutive_quality_failures >= self.max_consecutive_quality_failures:
                            logging.error("連續品質失敗過多，強制重連")
                            self._update_connection_state(ConnectionState.DISCONNECTED)
                            self.consecutive_quality_failures = 0
                            asyncio.create_task(self.attempt_reconnect())
                    else:
                        self.consecutive_quality_failures = 0

                # 斷線通知
                if self.connection_failed_since and self.connection_state != ConnectionState.CONNECTED:
                    await self.handle_connection_failure()

                # 記憶體檢查
                await self._check_memory_usage()

                # 狀態報告 (30分鐘)
                if current_time - self._last_status_report >= self.config['monitoring']['status_report_interval']:
                    self._report_current_status()
                    self._last_status_report = current_time

                consecutive_errors = 0
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"監控錯誤 ({consecutive_errors}/{max_consecutive_errors}): {e}")
                await asyncio.sleep(5)

    async def _handle_continuous_reconnect(self, current_time: float):
        print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 持續重連嘗試 #{self.reconnect_attempts + 1}")
        self.last_reconnect_attempt = current_time
        if self.connection_failed_since is None:
            self.connection_failed_since = current_time
        await self.attempt_reconnect()

    def _update_connection_state(self, new_state: ConnectionState):
        old_state = self.connection_state
        self.connection_state = new_state
        if old_state != new_state:
            color = {"connected": "🟢", "disconnected": "🔴", "connecting": "🟡"}.get(new_state.value, "⚪")
            print(f"\n{color} [{datetime.now().strftime('%H:%M:%S')}] 狀態: {old_state.value} → {new_state.value}")
            self.state_change_time = time.time()
            if new_state == ConnectionState.DISCONNECTED:
                print("🔴 斷線！立即重連...")
            elif new_state == ConnectionState.CONNECTED and self.connection_failed_since:
                self._reset_notification_state()

    def _reset_notification_state(self):
        if self.connection_failed_since:
            downtime = int(time.time() - self.connection_failed_since)
            if downtime > 5:
                msg = f"***** {target_env} *****\n🟢 連線恢復\n伺服器: {self.ws_url}\n中斷: {downtime}秒"
                asyncio.create_task(self._send_telegram_notification_async(msg))
            self.connection_failed_since = None
            self.next_notification_index = 0
            self.last_notification_time = 0

    async def connect_and_login(self) -> bool:
        try:
            self._update_connection_state(ConnectionState.CONNECTING)
            self.ws = await asyncio.wait_for(
                websockets.connect(self.ws_url, ping_interval=None, close_timeout=10),
                timeout=15
            )
            self._update_connection_state(ConnectionState.CONNECTED)
            await self.ws.send(json.dumps(self.login_data))
            logging.info("登入訊息已發送")

            self.listen_task = asyncio.create_task(self._websocket_listener())
            self.process_task = asyncio.create_task(self._message_processor())
            self.reconnect_attempts = 0
            self._reset_notification_state()

            # 重連後立即發 ping 測試
            asyncio.create_task(self._send_test_ping_after_reconnect())
            return True
        except Exception as e:
            logging.error(f"連線失敗: {e}")
            await self.safe_close()
            return False

    async def _send_test_ping_after_reconnect(self):
        await asyncio.sleep(2)  # 等待登入完成
        if self.connection_state == ConnectionState.CONNECTED:
            await self.ws.send(f"{self.client_id},ping")

    async def _websocket_listener(self):
        try:
            async for message in self.ws:
                if len(message) > 10*1024*1024:
                    continue
                await self.message_queue.put(WebSocketMessage(message, time.time(), "websocket"))
                self.messages_received += 1
                self.last_message_time = time.time()
        except websockets.exceptions.ConnectionClosed as e:
            logging.error(f"連線關閉: {e.code} {e.reason}")
        except Exception as e:
            logging.error(f"監聽錯誤: {e}")
        finally:
            await self._cleanup_listener()

    async def _cleanup_listener(self):
        await self.message_queue.put(WebSocketMessage(None, time.time(), "poison_pill"))
        self._update_connection_state(ConnectionState.DISCONNECTED)
        if not asyncio.current_task().cancelled():
            await asyncio.sleep(1)
            await self.attempt_reconnect()

    async def _message_processor(self):
        while True:
            try:
                msg = await asyncio.wait_for(self.message_queue.get(), 1.0)
                if msg.message_type == "poison_pill":
                    break
                await self._process_websocket_message(msg)
                self.messages_processed += 1
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"處理錯誤: {e}")

    async def _process_websocket_message(self, message: WebSocketMessage):
        content = message.content
        if isinstance(content, str) and "pong" in content.lower():
            await self._handle_pong_message(content, message.timestamp)
            return
        if content.startswith('{'):
            try:
                data = json.loads(content)
                await self._handle_json_message(data, message.timestamp)
            except:
                pass

    async def _handle_pong_message(self, content: str, ts: float):
        if self.ping_sent_time:
            rt = (ts - self.ping_sent_time) * 1000
            self.ping_response_times.append(rt)
            if len(self.ping_response_times) > 10:
                self.ping_response_times.pop(0)
            self.last_pong_time = ts
            avg = sum(self.ping_response_times) / len(self.ping_response_times)
            logging.info(f"Pong 回應時間: {self.format_delay(rt)}ms (平均: {self.format_delay(avg)}ms)")

    async def check_connection_quality(self) -> Dict[str, Any]:
        if not self.ws or self.connection_state != ConnectionState.CONNECTED:
            return {"quality_ok": False, "reason": "not_connected"}

        try:
            # 方法2: 自訂 ping（優先）
            self.ping_sent_time = time.time()
            await self.ws.send(f"{self.client_id},ping")
            start = time.time()
            while time.time() - start < self.quality_check_timeout:
                if self.last_pong_time and self.last_pong_time > self.ping_sent_time:
                    rt = (self.last_pong_time - self.ping_sent_time) * 1000
                    self.ping_sent_time = None
                    self.last_pong_time = None
                    return {
                        "response_time_ms": rt,
                        "quality_ok": rt < 1000,
                        "method": "custom_ping"
                    }
                await asyncio.sleep(0.1)

            # 方法3: 啟發式
            if self.last_message_time and (time.time() - self.last_message_time) < 120:
                return {
                    "response_time_ms": None,
                    "quality_ok": True,
                    "method": "heuristic",
                    "reason": "recent_messages_received"
                }

            return {"quality_ok": False, "reason": "all_methods_failed"}
        except Exception as e:
            return {"quality_ok": False, "reason": f"exception: {e}"}

    def log_check_result(self, check_type: str, success: bool, details: Dict[str, Any]):
        if check_type == "連線品質":
            if details.get("quality_ok"):
                if "response_time_ms" in details and details["response_time_ms"] is not None:
                    delay = self.format_delay(details["response_time_ms"])
                    logging.info(f"連線品質良好: 延遲 {delay}ms (方法: {details['method']})")
                else:
                    logging.info(f"連線品質良好: 方法 {details['method']} (原因: {details.get('reason', 'N/A')})")
            else:
                logging.warning(f"連線品質檢查失敗: {details}")
        else:
            status = "成功" if success else "失敗"
            logging.info(f"{check_type}檢查{status}: {details}")

    async def safe_close(self):
        self._update_connection_state(ConnectionState.DISCONNECTED)
        for task in [self.listen_task, self.process_task]:
            if task and not task.done():
                task.cancel()
        if self.ws:
            try:
                await asyncio.wait_for(self.ws.close(), timeout=10)
            except:
                pass
            self.ws = None
        while not self.message_queue.empty():
            try: self.message_queue.get_nowait(); self.message_queue.task_done()
            except: break

    async def attempt_reconnect(self) -> bool:
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            return False
        if self.reconnect_attempts > 0:
            await asyncio.sleep(1.0)
        self.reconnect_attempts += 1
        success = await self.connect_and_login()
        if success:
            print(f"🟢 重連成功！次數: {self.reconnect_attempts}")
            self.reconnect_attempts = 0
            self.performance_stats['total_reconnects'] += 1
            self._reset_notification_state()
        return success

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        uptime = time.time() - self.performance_stats['start_time']
        messages_per_minute = (self.messages_received / uptime * 60) if uptime > 0 else 0
        
        return {
            'uptime_seconds': int(uptime),
            'total_reconnects': self.performance_stats['total_reconnects'],
            'total_messages': self.messages_received,
            'messages_per_minute': round(messages_per_minute, 2),
            'current_queue_size': self.message_queue.qsize(),
            'connection_quality_avg': sum(self.ping_response_times) / len(self.ping_response_times) if self.ping_response_times else 0,
            'success_rate': (self.messages_processed / self.messages_received * 100) if self.messages_received > 0 else 100,
            'total_errors': self.performance_stats['total_errors']
        }
    
    async def _check_memory_usage(self):
        """檢查記憶體使用情況"""
        if time.time() - self._last_memory_check < 300:  # 每5分鐘檢查一次
            return
            
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            if memory_info.rss > 100 * 1024 * 1024:  # 100MB 警告
                logging.warning(f"記憶體使用較高: {memory_info.rss / 1024 / 1024:.2f} MB")
                
        except ImportError:
            pass  # psutil 不可用時跳過
        except Exception as e:
            logging.debug(f"記憶體檢查失敗: {e}")
        
        self._last_memory_check = time.time()
    
    def _report_current_status(self):
        """報告當前狀態"""
        status_info = {
            "connection_state": self.connection_state.value,
            "messages_received": self.messages_received,
            "messages_processed": self.messages_processed,
            "reconnect_attempts": self.reconnect_attempts,
            "last_message_time": self.last_message_time,
            "current_time": time.time()
        }
        
        # 在控制台顯示狀態
        state_emoji = {
            ConnectionState.CONNECTED: "🟢",
            ConnectionState.DISCONNECTED: "🔴",
            ConnectionState.CONNECTING: "🟡",
            ConnectionState.RECONNECTING: "🟠"
        }
        
        emoji = state_emoji.get(self.connection_state, "⚪")
        print(f"\n{emoji} [{datetime.now().strftime('%H:%M:%S')}] 定期狀態報告:")
        print(f"   連線狀態: {self.connection_state.value}")
        print(f"   訊息接收: {self.messages_received}")
        print(f"   訊息處理: {self.messages_processed}")
        print(f"   重連嘗試: {self.reconnect_attempts}")
        if self.connection_failed_since is not None:
            downtime = int(time.time() - self.connection_failed_since)
            print(f"   斷線時間: {downtime} 秒")
        
        # 顯示效能統計
        stats = self.get_performance_stats()
        print(f"   運行時間: {stats['uptime_seconds']} 秒")
        print(f"   總重連次數: {stats['total_reconnects']}")
        print(f"   訊息/分鐘: {stats['messages_per_minute']}")
        print(f"   成功率: {stats['success_rate']:.1f}%")
        
        logging.info(f"定期狀態報告: {status_info}")
    
    async def _monitoring_cycle(self, current_time: float):
        """監控循環的核心邏輯"""
        # 連線狀態檢查（每10分鐘）
        if current_time - self.last_connection_check >= 600:
            if self.connection_state != ConnectionState.CONNECTED:
                print(f"🟡 [{datetime.now().strftime('%H:%M:%S')}] 執行定期連線狀態檢查 - 目前斷線")
                logging.info("執行定期連線狀態檢查 - 目前斷線")
                reconnect_success = await self.attempt_reconnect()
                if not reconnect_success:
                    await self.handle_connection_failure()
            else:
                # 連線正常，記錄狀態
                self.log_check_result("連線狀態", True, {
                    "state": self.connection_state.value,
                    "active": True
                })
            
            self.last_connection_check = current_time
        
        # 連線品質檢查（每1分鐘，僅在連線狀態下）
        if (self.connection_state == ConnectionState.CONNECTED and 
            current_time - self.last_quality_check >= self.config['monitoring']['quality_check_interval']):
            
            try:
                quality_result = await self.check_connection_quality()
                
                self.log_check_result("連線品質", quality_result["quality_ok"], quality_result)
                self.last_quality_check = current_time
                
                if not quality_result["quality_ok"]:
                    self.consecutive_quality_failures += 1
                    logging.warning(f"連續品質檢查失敗次數: {self.consecutive_quality_failures}")
                    if self.consecutive_quality_failures >= self.max_consecutive_quality_failures:
                        logging.error("連續品質檢查失敗過多次，強制重新連線")
                        self._update_connection_state(ConnectionState.DISCONNECTED)
                        self.consecutive_quality_failures = 0
                        await self.attempt_reconnect()
                else:
                    self.consecutive_quality_failures = 0
                
            except Exception as e:
                logging.error(f"品質檢查過程中發生錯誤: {e}")
                print("B.")
                self.log_check_result("連線品質", False, {
                    "reason": f"check_exception: {str(e)}",
                    "method": "exception"
                })
        
        # 即時重連機制 - 檢測到斷線立即重連
        if (self.connection_state == ConnectionState.DISCONNECTED and 
            self.connection_failed_since is None):
            print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 檢測到連線中斷，立即嘗試重新連線")
            logging.info("檢測到連線中斷，立即嘗試重新連線")
            self.connection_failed_since = current_time
            reconnect_success = await self.attempt_reconnect()
            if not reconnect_success:
                await self.handle_connection_failure()
        
        # 處理連線失敗的通知（每秒檢查）
        if (self.connection_failed_since is not None and 
            self.connection_state != ConnectionState.CONNECTED):
            await self.handle_connection_failure()
        
        # 記憶體使用檢查
        await self._check_memory_usage()

    

# 配置部分 - 使用環境變數增強安全性
# client_id = 'z0002'
client_id = 'z0001'
ws_url = ''

CONFIG = {
    "websocket": {
        # "url": os.getenv('WEBSOCKET_URL', "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"),
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
        "quality_check_interval": 60,
        "status_report_interval": 1800,
        "reconnect_max_delay": 300,
        "notification_intervals": [30, 60, 300, 600, 1800, 3600]
    }
}


def setup_global_logging():
    """全域日誌設定"""
    log_format = '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    log_file = 'websocket_monitor.log'
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
    except ImportError:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    logging.basicConfig(
        level=logging.INFO,
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
# target_env = "local"
# target_env = "trial"
target_env = "live"
    



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