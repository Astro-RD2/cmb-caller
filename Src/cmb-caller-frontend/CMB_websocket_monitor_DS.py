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

print = functools.partial(print, flush=True)

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

class WebSocketMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ws_url = config['websocket']['url']
        self.login_data = config['websocket']['login_data']
        self.telegram_config = config['telegram']
        
        # 添加 client_id 屬性
        self.client_id = config['websocket']['login_data'].get('caller_id', 'monitor')
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.listen_task: Optional[asyncio.Task] = None
        self.process_task: Optional[asyncio.Task] = None
        
        # 監控相關變數
        self.last_connection_check = 0
        self.last_quality_check = 0
        self.connection_failed_since: Optional[float] = None
        self.notification_intervals = config['monitoring']['notification_intervals']
        self.next_notification_index = 0
        self.last_notification_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_delay = config['monitoring']['reconnect_max_delay']
        self.max_reconnect_attempts = 10
        
        # 品質檢查相關 - 初始化為 None
        self.ping_sent_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None
        self.ping_response_times: List[float] = []
        self.quality_check_timeout = 10  # 秒
        
        # 統計資料
        self.messages_received = 0
        self.messages_processed = 0
        self.last_message_time: Optional[float] = None
        
        # 狀態報告
        self._last_status_report = 0
        
        # 效能統計
        self.performance_stats = {
            'total_reconnects': 0,
            'total_messages': 0,
            'total_errors': 0,
            'start_time': time.time(),
            'last_reset_time': time.time()
        }
        
        # 記憶體監控
        self._last_memory_check = 0
        
        self.setup_logging()
        
        self.state_change_time = time.time()
        
    def setup_logging(self):
        """設定日誌記錄"""
        log_format = '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 創建日誌目錄
        log_file = self.config['logging']['file']
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
            level=getattr(logging, self.config['logging'].get('level', 'INFO')),
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(),
                file_handler
            ]
        )
    
    def _update_connection_state(self, new_state: ConnectionState):
        """更新連線狀態並立即顯示"""
        old_state = self.connection_state
        self.connection_state = new_state
        
        # 狀態變化時立即顯示
        if old_state != new_state:
            status_colors = {
                ConnectionState.CONNECTED: "🟢",
                ConnectionState.DISCONNECTED: "🔴", 
                ConnectionState.CONNECTING: "🟡",
                ConnectionState.RECONNECTING: "🟠"
            }
            
            color = status_colors.get(new_state, "⚪")
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n{color} [{timestamp}] 連線狀態變化: {old_state.value} → {new_state.value}, ({time.time() - self.state_change_time:.2f}秒)")
            self.state_change_time = time.time()
            
            # 特別顯示斷線情況
            if new_state == ConnectionState.DISCONNECTED:
                print("🔴 檢測到斷線！立即嘗試重新連線...")
            elif new_state == ConnectionState.CONNECTED:
                print("🟢 連線成功建立！")
                
                # 連線成功時，檢查是否需要重置通知狀態
                if self.connection_failed_since is not None:
                    self._reset_notification_state()
    
    def _reset_notification_state(self):
        """重置通知狀態"""
        if self.connection_failed_since is not None:
            downtime = int(time.time() - self.connection_failed_since)
            
            # 只有在實際有斷線記錄時才發送恢復通知
            if downtime > 5:  # 至少斷線5秒才發送恢復通知
                recovery_message = (
                    f"🟢 WebSocket 連線恢復\n"
                    f"• 伺服器: {self.ws_url}\n"
                    f"• 中斷時間: {downtime} 秒\n"
                    f"• 恢復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                # 非同步發送恢復通知（但不等待）
                asyncio.create_task(self._send_telegram_notification_async(recovery_message))
                
                print(f"🟢 [{datetime.now().strftime('%H:%M:%S')}] 連線恢復！中斷時間: {downtime} 秒")
            
            # 重置狀態
            self.connection_failed_since = None
            self.next_notification_index = 0
            self.last_notification_time = 0
            logging.info("連線恢復，重置通知狀態")
    
    async def _send_telegram_notification_async(self, message: str):
        """非同步發送 Telegram 通知（不阻塞主流程）"""
        try:
            await self.send_telegram_notification(message)
        except Exception as e:
            logging.error(f"發送恢復通知失敗: {e}")
    
    async def connect_and_login(self) -> bool:
        """建立連線並登入"""
        try:
            self._update_connection_state(ConnectionState.CONNECTING)
            logging.info(f"嘗試連接到 WebSocket: {self.ws_url}")
            
            # 添加連線超時
            try:
                self.ws = await asyncio.wait_for(
                    websockets.connect(
                        self.ws_url,
                        ping_interval=None,  # 禁用自動 ping
                        close_timeout=10
                    ),
                    timeout=15
                )
            except asyncio.TimeoutError:
                logging.error("WebSocket 連線超時")
                return False
            
            self._update_connection_state(ConnectionState.CONNECTED)
            
            # 發送登入訊息
            login_msg = json.dumps(self.login_data)
            await self.ws.send(login_msg)
            logging.info(f"WebSocket 連線成功並發送登入訊息")
            
            # 啟動監聽和處理任務
            if self.listen_task is None or self.listen_task.done():
                self.listen_task = asyncio.create_task(self._websocket_listener())
            if self.process_task is None or self.process_task.done():
                self.process_task = asyncio.create_task(self._message_processor())
            
            self.reconnect_attempts = 0
            
            # 連線成功時重置通知狀態
            self._reset_notification_state()
            
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
                    
                # 添加訊息大小檢查
                if len(message) > 10 * 1024 * 1024:  # 10MB 限制
                    logging.warning(f"收到過大訊息: {len(message)} bytes")
                    continue
                    
                print(f"message:{message}",flush=True)
                ws_message = WebSocketMessage(
                    content=message,
                    timestamp=time.time(),
                    message_type="websocket"
                )
                
                # 添加佇列滿時的處理策略
                if self.message_queue.full():
                    # 可選擇丟棄最舊的訊息或等待空間
                    try:
                        self.message_queue.get_nowait()  # 丟棄最舊訊息
                        logging.warning("訊息佇列已滿，丟棄最舊訊息")
                    except:
                        pass
                
                await self.message_queue.put(ws_message)
                self.messages_received += 1
                self.performance_stats['total_messages'] += 1
                
                # 記錄最後收到訊息的時間
                self.last_message_time = time.time()
                
            logging.info("WebSocket 連線已關閉，監聽任務結束")
            
        except asyncio.CancelledError:
            logging.warning("WebSocket 監聽任務已被取消!")
            return
        except Exception as e:
            logging.error(f"WebSocket 監聽發生錯誤: {e}")
            self.performance_stats['total_errors'] += 1
        finally:
            # 確保資源清理
            await self._cleanup_listener()
    
    async def _cleanup_listener(self):
        """清理監聽器資源"""
        poison_pill = WebSocketMessage(
            content=None,
            timestamp=time.time(),
            message_type="poison_pill"
        )
        
        try:
            await self.message_queue.put(poison_pill)
        except:
            logging.warning("無法放入終止訊號")
        
        self._update_connection_state(ConnectionState.DISCONNECTED)
        
        # 只有在非取消的情況下才重連
        if not isinstance(sys.exc_info()[1], asyncio.CancelledError):
            await asyncio.sleep(1.0)
            logging.info("\n\n***** 監聽器觸發重新連線!!! *****\n")
            await self.attempt_reconnect()
    
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
            self.performance_stats['total_errors'] += 1
    
    async def _process_websocket_message(self, message: WebSocketMessage):
        """處理單個 WebSocket 訊息"""
        try:
            content = message.content
            
            # 處理 PONG 回應
            if isinstance(content, str) and "pong" in content.lower():
                await self._handle_pong_message(content, message.timestamp)
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
            self.performance_stats['total_errors'] += 1
    
    async def _handle_pong_message(self, content: str, timestamp: float):
        """處理 PONG 回應"""
        # 只有在等待 ping 回應時才記錄時間
        if self.ping_sent_time is not None:
            response_time = (timestamp - self.ping_sent_time) * 1000
            self.ping_response_times.append(response_time)
            
            # 保持最近10次記錄
            if len(self.ping_response_times) > 10:
                self.ping_response_times.pop(0)
            
            self.last_pong_time = timestamp
            
            avg_response = sum(self.ping_response_times) / len(self.ping_response_times)
            logging.info(f"Pong 回應時間: {response_time:.2f}ms (平均: {avg_response:.2f}ms)")
        else:
            logging.debug("收到 PONG 回應，但未在等待檢查期間")
    
    async def _handle_json_message(self, data: Dict, timestamp: float):
        """處理 JSON 格式訊息"""
        action = data.get("action", "")
        print(f"action:{action}", flush=True)
        
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
            
            # 登入成功時確保通知狀態重置
            if status == "OK" and self.connection_failed_since is not None:
                self._reset_notification_state()
        
        logging.info(f"處理 JSON 訊息: {data}")
    
    async def _handle_text_message(self, content: str, timestamp: float):
        """處理文字格式訊息"""
        if "ping" in content.lower():
            if "ping" in content.lower() and "pong" not in content.lower():
                await self._send_pong_response(content)
        elif "update" in content.lower():
            logging.info(f"收到更新訊息: {content}")
        else:
            logging.debug(f"處理文字訊息: {content[:100]}{'...' if len(content) > 100 else ''}")
    
    async def _send_pong_response(self, ping_message: str):
        """回應 ping 請求"""
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
        """改進的連線品質檢查"""
        if self.connection_state != ConnectionState.CONNECTED or not self.ws:
            return {"response_time_ms": None, "quality_ok": False, "reason": "not_connected"}
        
        try:
            # 方法1: 使用 WebSocket 內建 ping/pong
            ping_start = time.time()
            await self.ws.ping()
            
            # 等待一小段時間看是否有回應
            wait_start = time.time()
            while time.time() - wait_start < 5:
                if (self.last_pong_time is not None and 
                    ping_start is not None and
                    self.last_pong_time > ping_start):
                    response_time = (self.last_pong_time - ping_start) * 1000
                    quality_ok = response_time < 1000
                    return {
                        "response_time_ms": round(response_time, 2),
                        "quality_ok": quality_ok,
                        "method": "builtin_ping"
                    }
                await asyncio.sleep(0.1)
            
            # 方法2: 發送自訂 ping 訊息
            self.ping_sent_time = time.time()
            ping_msg = f"{self.client_id},ping"
            logging.info(f"send:{ping_msg}")
            await self.ws.send(ping_msg)
            
            # 等待回應
            wait_start = time.time()
            while time.time() - wait_start < self.quality_check_timeout:
                if (self.last_pong_time is not None and 
                    self.ping_sent_time is not None and
                    self.last_pong_time > self.ping_sent_time):
                    
                    response_time = (self.last_pong_time - self.ping_sent_time) * 1000
                    quality_ok = response_time < 1000
                    
                    # 重置狀態以便下次檢查
                    self.last_pong_time = None
                    self.ping_sent_time = None
                    
                    return {
                        "response_time_ms": round(response_time, 2),
                        "quality_ok": quality_ok,
                        "method": "custom_ping"
                    }
                await asyncio.sleep(0.1)
            
            # 方法3: 基於最後訊息時間的啟發式檢查
            if self.last_message_time and (time.time() - self.last_message_time) < 120:
                return {
                    "response_time_ms": None,
                    "quality_ok": True,
                    "method": "heuristic",
                    "reason": "recent_messages_received"
                }
            
            # 所有方法都失敗
            logging.warning("所有品質檢查方法都失敗")
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
    
    async def safe_close(self):
        """安全關閉連線和任務"""
        self._update_connection_state(ConnectionState.DISCONNECTED)
        
        # 取消任務
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
        
        # 關閉 WebSocket 連線
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
        
        # 清空佇列
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except:
                break
        
        logging.info("安全關閉完成")
    
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
        except asyncio.TimeoutError:
            logging.error("Telegram 通知發送逾時")
        except Exception as e:
            logging.error(f"發送 Telegram 通知時發生錯誤: {e}")
    
    def should_send_notification(self) -> bool:
        """判斷是否應該發送通知"""
        # 只有在確實斷線且沒有成功重連的情況下才發送通知
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
        """處理連線失敗邏輯"""
        current_time = time.time()
    
        if self.connection_failed_since is None:
            self.connection_failed_since = current_time
            self.next_notification_index = 0
            logging.warning("開始記錄連線失敗時間")
            
            # 立即顯示斷線訊息
            print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 連線失敗計時開始...")
    
        if self.should_send_notification():
            downtime = int(current_time - self.connection_failed_since)
            message = (
                f"🔴 WebSocket 連線異常\n"
                f"• 伺服器: {self.ws_url}\n"
                f"• 持續時間: {downtime} 秒\n"
                f"• 最後檢查: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.send_telegram_notification(message)
            self.last_notification_time = current_time
            self.next_notification_index += 1
            
            # 顯示發送通知的訊息
            print(f"📢 [{datetime.now().strftime('%H:%M:%S')}] 已發送 Telegram 通知 (斷線 {downtime} 秒)")
            logging.warning(f"發送連線異常通知，下次通知索引: {self.next_notification_index}")
    
    async def attempt_reconnect(self) -> bool:
        """嘗試重新連線，使用指數退避"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logging.error(f"達到最大重連嘗試次數 {self.max_reconnect_attempts}，停止重連")
            return False
            
        if self.reconnect_attempts > 0:
            delay = min(2 ** self.reconnect_attempts, self.max_reconnect_delay)
            print(f"🟡 [{datetime.now().strftime('%H:%M:%S')}] 重連嘗試 #{self.reconnect_attempts}, 等待 {delay} 秒")
            logging.info(f"重連嘗試 #{self.reconnect_attempts}, 等待 {delay} 秒")
            await asyncio.sleep(delay)
    
        try:
            # 添加連線超時控制
            try:
                async with asyncio.timeout(30):  # Python 3.11+
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
                
                # 成功重連時重置通知狀態
                self._reset_notification_state()
                
                return True
            else:
                self.reconnect_attempts += 1
                print(f"🔴 [{datetime.now().strftime('%H:%M:%S')}] 重連失敗，當前嘗試次數: {self.reconnect_attempts}")
                logging.warning(f"重連失敗，當前嘗試次數: {self.reconnect_attempts}")
                return False
        except Exception as e:
            logging.error(f"重連過程中發生錯誤: {e}")
            self.reconnect_attempts += 1
            self.performance_stats['total_errors'] += 1
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
        json_log_file = self.config['logging']['file'].replace('.log', '_json.log')
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"寫入 JSON 日誌失敗: {e}")
        
        # 根據檢查類型輸出適當的日誌
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
                
                # 更清晰的日誌輸出
                if quality_result["quality_ok"]:
                    if quality_result["response_time_ms"] is not None:
                        logging.info(f"連線品質良好: 延遲 {quality_result['response_time_ms']:.2f}ms (方法: {quality_result['method']})")
                    else:
                        logging.info(f"連線品質良好: 方法 {quality_result['method']} (原因: {quality_result.get('reason', 'N/A')})")
                else:
                    logging.warning(f"連線品質檢查失敗: {quality_result}")
                
                self.log_check_result("連線品質", quality_result["quality_ok"], quality_result)
                self.last_quality_check = current_time
                
            except Exception as e:
                logging.error(f"品質檢查過程中發生錯誤: {e}")
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
    
    async def run_monitoring(self):
        """主監控循環"""
        logging.info("啟動 WebSocket 監控程式")
        print("🟡 啟動 WebSocket 監控程式...")
        
        # 添加啟動保護
        startup_attempts = 0
        max_startup_attempts = 3
        
        while startup_attempts < max_startup_attempts:
            try:
                initial_success = await self.connect_and_login()
                if initial_success:
                    break
                else:
                    startup_attempts += 1
                    if startup_attempts < max_startup_attempts:
                        logging.warning(f"初始連線失敗，等待重試 ({startup_attempts}/{max_startup_attempts})")
                        await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"初始連線異常: {e}")
                startup_attempts += 1
                if startup_attempts < max_startup_attempts:
                    await asyncio.sleep(5)
        
        if startup_attempts >= max_startup_attempts:
            logging.error("初始連線完全失敗，程式退出")
            return
        
        # 主循環添加健康檢查
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                current_time = time.time()
                
                # 健康檢查：如果連續錯誤太多，重啟監控
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("連續錯誤過多，重啟監控循環")
                    await self.safe_close()
                    await asyncio.sleep(10)
                    consecutive_errors = 0
                    await self.connect_and_login()
                    continue
                
                # 執行監控循環
                await self._monitoring_cycle(current_time)
                
                # 定期狀態報告（每30分鐘）
                if current_time - self._last_status_report >= self.config['monitoring']['status_report_interval']:
                    self._report_current_status()
                    self._last_status_report = current_time
                
                consecutive_errors = 0  # 重置錯誤計數
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logging.info("監控循環被取消")
                break
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"監控循環發生錯誤 ({consecutive_errors}/{max_consecutive_errors}): {e}")
                self.performance_stats['total_errors'] += 1
                await asyncio.sleep(5)


# 配置部分 - 使用環境變數增強安全性
# client_id = 'z0002'
client_id = 'z0001'

CONFIG = {
    "websocket": {
        "url": os.getenv('WEBSOCKET_URL', "wss://cmb-caller-frontend-306511771181.asia-east1.run.app/"),
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

async def main():
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