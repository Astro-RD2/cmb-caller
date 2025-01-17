import socket
import time
from datetime import datetime
from websocket_server import WebsocketServer
import json
import threading
import websocket

# 設定 WebSocket 伺服器的 IP 和端口
wsip = '0.0.0.0'
# port = 38000

A = 0

def ma_print(s):
    now = datetime.now()
    str_h = now.strftime("%H:%M:%S.%f")[:-3]
    print(str_h + " " + s)

def on_message(ws, message):
    ma_print(f'receive(CMB): \n{message}')

def on_error(ws, error):
    ma_print(f"WebSocket error: {error}")

def on_close(ws):
    ma_print("### WebSocket closed ###")
    reconnect(ws)

def on_open(ws):
    ma_print("### WebSocket opened ###")

def reconnect(ws):
    """重連 WebSocket"""
    ma_print("Attempting to reconnect...")
    while True:
        try:
            ws.close()  # 確保關閉現有的連線
            time.sleep(5)  # 等待一段時間再嘗試重連
            ws.run_forever()
            break
        except Exception as e:
            ma_print(f"Reconnect failed: {e}")

class ws_cmb:
    def __init__(self, wsIP):
        self.wsIP = wsIP
        self.ws = websocket.WebSocketApp(self.wsIP,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)
        self.ws.on_open = on_open

    def start(self):
        threading.Thread(target=self.queryframe, daemon=True).start()

    def queryframe(self):
        try:
            self.ws.run_forever()
        except Exception as e:
            ma_print(f"WebSocket run_forever error: {e}")
            reconnect(self.ws)

class ws:
    def __init__(self):
        self.status = False
        self.vendor_id = "tawe"
        self.caller_id = "CMB66666"
        self.call_num = 0
        self.change = True
        self.last_update = 0
        self.ws_cmb_instance = None  # 初始化 ws_cmb_instance

    def start(self):
        threading.Thread(target=self.queryframe, daemon=True).start()

    def check_json_format(self, raw_msg):
        if isinstance(raw_msg, str):
            try:
                json.loads(raw_msg)
            except ValueError:
                return False
            return True
        else:
            return False

    def send_all(self):
        try:
            global A
            A += 1
            self.server.send_message_to_all(str(A))
        except Exception as e:
            ma_print(f"send_all failed. (socket error: {e})")

    def new_client(self, client, server):
        # print(f'new_client, client: {client}, server: {server}')
        str1 = datetime.now().strftime("%Y%m%d-%H_%M_%S_%f")[:-3]
        str1 += f' new_client {client["id"]}, {client["address"]} OK'
        ma_print(str1)
    '''
    def message_received(self, client, server, message):
        # print(f'message_received, client: {client}, server: {server}, message: {message}')
        try:
            self.caller_id ='CMBXXXXX'
            self.call_num = 0
            self.caller_id, self.call_num = message.split(',')
            self.call_num = str(int(self.call_num))
            data = {
                "vendor_id": self.vendor_id,
                "caller_id": self.caller_id,
                "call_num": self.call_num,
                "change": self.change,
                "last_update": self.last_update
            }
            print('')
            ma_print(f'Receive(Caller {client["id"]}): {message}')
            # 將資料轉換為 JSON 並列印
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            ma_print(f'Send(CMB): \n{json_data}')
            self.ws_cmb_instance.ws.send(f'{json_data}')           # 使用 ws_cmb_instance 來發送消息
            str1 = str(client["address"])
            str1 += ' ' + str(message)
            ma_print(f'Send(Caller {client["id"]}): {str1}')
            self.server.send_message(client, str1)      # 回覆 Caller
        except Exception as e:
            ma_print(f"message_received failed. (socket error: {e})")
    '''


    def message_received(self, client, server, message):
        try:
            self.caller_id = 'CMBXXXXX'
            self.call_num = 0
            
            # 記錄接收到的消息
            ma_print(f'Receive(Caller {client["id"]}): {message}')

            if message == 'ping':
                return
            
            # 驗證 message 是否符合預期的格式
            if ',' not in message:
                raise ValueError(f"Message format invalid, expected 'caller_id,call_num', '{message}'")
    
            # 拆分 message 並進行進一步驗證
            parts = message.split(',')
            if len(parts) != 2:
                raise ValueError(f"Message split error, expected 2 parts but got {len(parts)}, '{message}'")
    
            self.caller_id, call_num_str = parts
            if not call_num_str.isdigit():
                raise ValueError(f"Call number is not a valid integer: {call_num_str}, '{message}'")
    
            self.call_num = str(int(call_num_str))
            
            data = {
                "vendor_id": self.vendor_id,
                "caller_id": self.caller_id,
                "call_num": self.call_num,
                "change": self.change,
                "last_update": self.last_update
            }
    
            # 將資料轉換為 JSON 並列印
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            ma_print(f'Send(CMB): \n{json_data}')
            self.ws_cmb_instance.ws.send(f'{json_data}')  # 使用 ws_cmb_instance 來發送消息
    
            str1 = str(client["address"])
            str1 += ' ' + str(message)
            ma_print(f'Send(Caller {client["id"]}): {str1}')
            self.server.send_message(client, str1)  # 回覆 Caller
    
        except ValueError as ve:
            ma_print(f"Value error in message_received: {ve}")
        except Exception as e:
            ma_print(f"message_received failed. (socket error: {e})")
    


    def queryframe(self):
        global wsip
        try:
            self.server = WebsocketServer(host=wsip, port=port)
            self.server.set_fn_new_client(self.new_client)
            self.server.set_fn_message_received(self.message_received)
            self.server.run_forever()
        except Exception as e:
            ma_print(f"WebSocket server error: {e}")

class ma_ws500ms_timer:
    def __init__(self):
        pass

    def start(self):
        threading.Thread(target=self.queryframe, daemon=True).start()

    def queryframe(self):
        tt = 1
        mta = 0
        global WS
        while True:
            try:
                mt1 = datetime.now().timestamp()
                mt2 = int(mt1)
                mt3 = (mt1 - mt2) * 1000000
                mt4 = int(mt3)
                if mt4 < 10000 and mta == 0:
                    mta = 1
                elif mt4 < 510000 and mt4 >= 500000 and mta == 1:
                    mta = 0
                time.sleep(0.001)
            except Exception as ex:
                tt += 1
                ss = str(ex) + " err " + str(tt)
                ma_print(ss)
                time.sleep(tt)

import platform, os, requests
def check_platform():
    os_name = platform.system()
    if os_name == 'Windows':
        return "Running on Windows PC", 'Windows'
    if os_name == 'Linux':
        if 'K_SERVICE' in os.environ:
            return "Running in GCP's Cloud Run", 'Cloud_Run'
        if check_gcp_vm():
            return "Running in GCP's Compute Engine", 'Compute_Engine'
        return "Running on Linux PC", 'Linux'
    return "Unknown environment", 'Unknown'

def check_gcp_vm():
    try:
        with requests.get('http://metadata.google.internal/computeMetadata/v1/', timeout=15, headers={'Metadata-Flavor': 'Google'}) as response:
            if response.status_code == 200:
                return True
    except:
        pass
    return False


port = 8080

#[live site]   https://callnum-receiver-410240967190.asia-east1.run.app
#[trial site]  https://callnum-receiver-306511771181.asia-east1.run.app

if __name__ == '__main__':
    try:
        ma_print("cmb-caller-frontend start")
        DESCRIBE, PLATFORM_NAME = check_platform()
        print(f'PLATFORM_NAME: {PLATFORM_NAME}')
        if PLATFORM_NAME == 'Compute_Engine':
            port = 8765    # for caller
            # ws_cmbIP = "ws://127.0.0.1:8080"  # Local OK
            ws_cmbIP = "wss://callnum-receiver-410240967190.asia-east1.run.app/"    # [live site] 
            # ws_cmbIP = "wss://callnum-receiver-306511771181.asia-east1.run.app"     # [trial site]
        else:
            port = 38000    # for caller
            # ws_cmbIP = "ws://192.168.1.2:8080"  # Roy PC, WiFi AP
            # ws_cmbIP = "ws://127.0.0.1:8080"  # Local OK
            ws_cmbIP = "ws://35.187.148.66:8080"     #
            # ws_cmbIP = "wss://callnum-receiver-410240967190.asia-east1.run.app/"    # [live site] 
            # ws_cmbIP = "wss://callnum-receiver-306511771181.asia-east1.run.app"     # [trial site]
            # ws_cmbIP = "216.239.38.53:443"  # Fail
            # ws_cmbIP = "xxx"  # ?
        print(f'port: {port}, ws_cmbIP: {ws_cmbIP}')            
        WS = ws()
        WS.start()
        tm7 = ma_ws500ms_timer()
        tm7.start()
        
        ws_cmb_instance = ws_cmb(ws_cmbIP)
        ws_cmb_instance.start()
        
        WS.ws_cmb_instance = ws_cmb_instance  # 將 ws_cmb_instance 賦值給 WS

        while True:
            time.sleep(2)
    except socket.gaierror as e:
        ma_print(f'err socket.gaierror {e}')
    except Exception as e:
        ma_print(f'err {e}')
    finally:
        ma_print('err cmb-caller-frontend END')