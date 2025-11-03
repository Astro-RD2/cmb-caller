import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import os
from enum import Enum
from PIL import Image, ImageDraw

class SerialStatus(Enum):
    UNUSED = 0
    USED = 1
    ERROR = 2

class ESP32FlasherApp:
    def __init__(self, root):
        self.root = root
        self.init_variables()
        self.setup_ui()
        self.scan_ports()
        self.load_serials()
        
    def init_variables(self):
        self.serial_port = None
        self.ser = None
        self.serial_file = "serials.txt"
        self.log_file = "flasher.log"
        self.current_serial = None
        self.serial_list = []
        self.auto_mode = False
        self.port_check_thread = None
        self.target_port = "COM4"  # 設定目標端口為 COM4
        
    def setup_ui(self):
        self.root.title("ESP32 量產燒錄工具 v1.0")
        self.root.geometry("1000x700")
        self.root.iconbitmap('default_icon.ico')

        # 主框架
        main_frame = tk.Frame(self.root, bg='white', padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制面板
        control_frame = tk.LabelFrame(main_frame, text="控制面板", bg='white', padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # COM PORT選擇
        tk.Label(control_frame, text="COM PORT:", bg='white').grid(row=0, column=0, sticky=tk.W)
        self.port_combobox = ttk.Combobox(control_frame, state="readonly")
        self.port_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        refresh_btn = tk.Button(
            control_frame,
            text="刷新 COM PORT",
            command=self.scan_ports,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        refresh_btn.grid(row=1, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 連接控制
        self.connect_btn = tk.Button(
            control_frame, 
            text="連接狀態: 未連接", 
            command=self.toggle_connection,
            bg='#f44336',
            fg='white',
            padx=10,
            pady=10
        )
        self.connect_btn.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.EW)
        
        # 操作按鈕
        self.flash_btn = tk.Button(
            control_frame,
            text="燒錄序號",
            command=self.start_flashing,
            bg='#e0e0e0',
            fg='black',
            state='disabled',
            padx=10,
            pady=5
        )
        self.flash_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        self.auto_btn = tk.Button(
            control_frame,
            text="自動模式: 關閉",
            command=self.toggle_auto_mode,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        self.auto_btn.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        reset_btn = tk.Button(
            control_frame,
            text="重置設備",
            command=self.reset_device,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        reset_btn.grid(row=5, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 狀態顯示
        status_frame = tk.LabelFrame(control_frame, text="設備狀態", bg='white', padx=10, pady=10)
        status_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky=tk.EW)
        
        tk.Label(status_frame, text="當前序號:", bg='white').grid(row=0, column=0, sticky=tk.W)
        self.serial_label = tk.Label(status_frame, text="無", font=('Arial', 10, 'bold'), fg="blue", bg='white')
        self.serial_label.grid(row=0, column=1, sticky=tk.W)
        
        tk.Label(status_frame, text="連接狀態:", bg='white').grid(row=1, column=0, sticky=tk.W)
        self.conn_status = tk.Label(status_frame, text="未連接", font=('Arial', 10), fg="red", bg='white')
        self.conn_status.grid(row=1, column=1, sticky=tk.W)
        
        # LED 狀態指示
        self.led = tk.Canvas(status_frame, width=24, height=24, bg='#e0e0e0', bd=0, highlightthickness=0)
        self.led.grid(row=2, column=0, columnspan=2, pady=5)
        self.led.create_oval(2, 2, 22, 22, fill='gray', outline='')
        
        # 序號列表
        tk.Label(control_frame, text="序號列表:", bg='white').grid(row=7, column=0, columnspan=2, sticky=tk.W)
        self.serial_listbox = tk.Listbox(control_frame, height=12, font=('Arial', 10), bg='white')
        self.serial_listbox.grid(row=8, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 序號文件
        tk.Label(control_frame, text="序號文件:", bg='white').grid(row=9, column=0, sticky=tk.W)
        self.serial_file_entry = tk.Entry(control_frame)
        self.serial_file_entry.grid(row=9, column=1, padx=5, pady=5, sticky=tk.EW)
        self.serial_file_entry.insert(0, "serials.txt")
        
        browse_btn = tk.Button(
            control_frame,
            text="瀏覽...",
            command=self.browse_serial_file,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        browse_btn.grid(row=10, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 日誌面板
        log_frame = tk.LabelFrame(main_frame, text="系統日誌", bg='white', padx=10, pady=10)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, font=('Arial', 10), bg='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 日誌控制
        log_control = tk.Frame(log_frame, bg='white')
        log_control.pack(fill=tk.X, pady=5)
        
        clear_btn = tk.Button(
            log_control,
            text="清除日誌",
            command=self.clear_log,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        clear_btn.pack(side=tk.LEFT)
        
        save_btn = tk.Button(
            log_control,
            text="保存日誌",
            command=self.save_log,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        test_btn = tk.Button(
            log_control,
            text="測試LED",
            command=self.test_led,
            bg='#e0e0e0',
            fg='black',
            padx=10,
            pady=5
        )
        test_btn.pack(side=tk.LEFT)
        
        self.log("系統初始化完成，準備就緒")

    def update_led(self, color):
        self.led.itemconfig(1, fill=color)
        
    def log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
        print(log_entry.strip())

    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log("日誌已清除")

    def save_log(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")],
            initialfile="flasher.log"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"日誌已保存到: {file_path}")

    def scan_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        if ports:
            # 優先選擇目標端口
            if self.target_port in ports:
                self.port_combobox.set(self.target_port)
            else:
                self.port_combobox.set(ports[0])
        self.log(f"掃描到可用 COM PORT: {', '.join(ports) if ports else '無'}")

    def browse_serial_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="serials.txt"
        )
        if file_path:
            self.serial_file = file_path
            self.serial_file_entry.delete(0, tk.END)
            self.serial_file_entry.insert(0, file_path)
            self.load_serials()

    def load_serials(self):
        self.serial_file = self.serial_file_entry.get()
        if not os.path.exists(self.serial_file):
            self.log(f"錯誤: 序號文件 {self.serial_file} 不存在")
            return False
        
        with open(self.serial_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.serial_list = []
        self.serial_listbox.delete(0, tk.END)
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                status = SerialStatus.UNUSED
                display_text = line
                
                if line.startswith('!'):
                    line = line[1:]
                    status = SerialStatus.ERROR
                    display_text = f"{line} (錯誤)"
                elif line.startswith('*'):
                    line = line[1:]
                    status = SerialStatus.USED
                    display_text = f"{line} (已使用)"
                
                self.serial_list.append({'serial': line, 'status': status})
                self.serial_listbox.insert(tk.END, display_text)
        
        return True

    def save_serials(self):
        with open(self.serial_file, 'w', encoding='utf-8') as f:
            for item in self.serial_list:
                if item['status'] == SerialStatus.USED:
                    f.write(f"*{item['serial']}\n")
                elif item['status'] == SerialStatus.ERROR:
                    pass
                else:
                    f.write(f"{item['serial']}\n")
        self.log("序號列表已保存")

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
            return
            
        port = self.port_combobox.get()
        if not port:
            messagebox.showerror("錯誤", "請選擇 COM PORT")
            return
            
        try:
            self.ser = serial.Serial(port, 115200, timeout=2)
            time.sleep(2)
            
            self.connect_btn.config(
                text="連接狀態: 已連接",
                bg='#4CAF50',
                fg='white'
            )
            self.flash_btn.config(state='normal')
            self.conn_status.config(text="已連接", fg="green")
            self.update_led('#4CAF50')
            self.log(f"已成功連接到 {port}")
            
            current_serial = self.get_serial_from_device()
            if current_serial:
                self.serial_label.config(text=current_serial)
                self.log(f"設備當前序號: {current_serial}")
        except Exception as e:
            self.log(f"連接錯誤: {str(e)}")
            messagebox.showerror("連接錯誤", f"無法連接至 {port}:\n{str(e)}")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        self.connect_btn.config(
            text="連接狀態: 未連接",
            bg='#f44336',
            fg='white'
        )
        self.flash_btn.config(state='disabled')
        self.conn_status.config(text="未連接", fg="red")
        self.update_led('gray')
        self.serial_label.config(text="無")
        self.log("已斷開連接")

    def get_serial_from_device(self):
        if not self.ser or not self.ser.is_open:
            return None
            
        response = self.send_command("GET_SERIAL")
        if response and response.startswith("CURRENT_SERIAL:"):
            return response[15:]
        return None

    def send_command(self, command, timeout=2):
        if not self.ser or not self.ser.is_open:
            self.log("錯誤: 未連接到設備")
            return None
            
        try:
            self.ser.write((command + '\n').encode('utf-8'))
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        if line.startswith("[") and "]" in line:
                            continue
                        self.log(f"設備回應: {line}")
                        return line
                time.sleep(0.1)
                
            self.log("等待回應超時")
            return None
        except Exception as e:
            self.log(f"通訊錯誤: {str(e)}")
            return None

    def start_flashing(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showerror("錯誤", "請先連接設備")
            return
            
        serial_num = self.get_next_serial()
        if not serial_num:
            messagebox.showerror("錯誤", "沒有可用的序號")
            return
            
        existing_serial = self.get_serial_from_device()
        if existing_serial:
            if not messagebox.askyesno("確認", f"設備已有序號: {existing_serial}\n是否要覆寫為 {serial_num}?"):
                self.log("使用者取消操作")
                return
        
        self.current_serial = serial_num
        self.serial_label.config(text=serial_num)
        
        original_text = self.flash_btn['text']
        self.flash_btn.config(
            text="燒錄中...",
            bg='#2196F3',
            fg='white',
            state='disabled'
        )
        self.update_led('#2196F3')
        self.root.update()
        
        threading.Thread(
            target=self.execute_flashing,
            args=(serial_num, original_text),
            daemon=True
        ).start()

    def execute_flashing(self, serial_num, original_text):
        self.log(f"開始燒錄序號: {serial_num}")
        
        retries = 3
        success = False
        
        for attempt in range(1, retries+1):
            self.log(f"嘗試 {attempt}/{retries}")
            
            response = self.send_command(f"SET_SERIAL:{serial_num}")
            if response == "RESULT:SUCCESS":
                success = True
                break
                
            time.sleep(1)
        
        self.root.after(0, lambda: self.flash_btn.config(
            text=original_text,
            state='normal'
        ))
        
        if success:
            self.mark_serial(serial_num, SerialStatus.USED)
            self.log(f"序號 {serial_num} 燒錄成功")
            self.update_led('#4CAF50')
            self.root.after(0, lambda: self.flash_btn.config(
                bg='#8BC34A',
                fg='white'
            ))
        else:
            self.mark_serial(serial_num, SerialStatus.ERROR)
            self.log(f"序號 {serial_num} 燒錄失敗")
            self.update_led('#F44336')
            self.root.after(0, lambda: self.flash_btn.config(
                bg='#F44336',
                fg='white'
            ))
        
        self.root.after(2000, lambda: self.flash_btn.config(
            bg='#e0e0e0',
            fg='black'
        ))
        self.root.after(0, self.update_serial_list)

    def get_next_serial(self):
        for item in self.serial_list:
            if item['status'] == SerialStatus.UNUSED:
                return item['serial']
        return None

    def mark_serial(self, serial, status):
        for item in self.serial_list:
            if item['serial'] == serial:
                item['status'] = status
                self.save_serials()
                return True
        return False

    def update_serial_list(self):
        self.load_serials()

    def reset_device(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showerror("錯誤", "請先連接設備")
            return
            
        if messagebox.askyesno("確認", "確定要重置設備嗎？這將清除所有設定"):
            response = self.send_command("RESET")
            if response == "RESETTING":
                self.log("設備正在重置...")
                self.update_led('#FF9800')
            else:
                self.log("重置命令失敗")

    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
        
        if self.auto_mode:
            self.auto_btn.config(
                text="自動模式: 啟用",
                bg='#FF9800',
                fg='black'
            )
            self.update_led('#FF9800')
            self.log("自動模式已啟用")
            
            self.port_check_thread = threading.Thread(
                target=self.auto_detect_devices,
                daemon=True
            )
            self.port_check_thread.start()
        else:
            self.auto_btn.config(
                text="自動模式: 關閉",
                bg='#e0e0e0',
                fg='black'
            )
            self.update_led('#4CAF50' if self.ser and self.ser.is_open else 'gray')
            self.log("自動模式已停用")

    def auto_detect_devices(self, check_interval=1):
        known_ports = set()
        
        while self.auto_mode:
            current_ports = set([p.device for p in serial.tools.list_ports.comports()])
            new_ports = current_ports - known_ports
            
            # 只處理目標端口
            if self.target_port in new_ports:
                self.log(f"檢測到目標設備: {self.target_port}")
                self.root.after(0, lambda p=self.target_port: self.process_auto_device(p))
            
            known_ports = current_ports
            time.sleep(check_interval)

    def process_auto_device(self, port):
        if not self.auto_mode:
            return
            
        if not (self.ser and self.ser.is_open):
            try:
                self.ser = serial.Serial(port, 115200, timeout=2)
                time.sleep(2)
                
                self.root.after(0, lambda: [
                    self.connect_btn.config(
                        text="連接狀態: 已連接",
                        bg='#4CAF50',
                        fg='white'
                    ),
                    self.flash_btn.config(state='normal'),
                    self.conn_status.config(text="已連接", fg="green"),
                    self.update_led('#4CAF50'),
                    self.log(f"已自動連接到 {port}")
                ])
            except Exception as e:
                self.log(f"自動連接錯誤: {str(e)}")
                return
                
        serial_num = self.get_next_serial()
        if not serial_num:
            self.log("錯誤: 沒有可用的序號")
            self.disconnect()
            return
            
        existing_serial = self.get_serial_from_device()
        if existing_serial:
            self.log(f"設備已有序號: {existing_serial}")
            if not self.ask_auto_overwrite(existing_serial, serial_num):
                self.log("自動模式跳過已燒錄設備")
                self.disconnect()
                return
                
        self.root.after(0, lambda: [
            self.serial_label.config(text=serial_num),
            self.flash_btn.config(
                text="燒錄中...",
                bg='#2196F3',
                fg='white',
                state='disabled'
            ),
            self.update_led('#2196F3')
        ])
        
        success = False
        for attempt in range(1, 4):
            response = self.send_command(f"SET_SERIAL:{serial_num}")
            if response == "RESULT:SUCCESS":
                success = True
                break
            time.sleep(1)
            
        if success:
            self.mark_serial(serial_num, SerialStatus.USED)
            self.log(f"自動燒錄成功: {serial_num}")
            self.root.after(0, lambda: [
                self.flash_btn.config(
                    bg='#8BC34A',
                    fg='white'
                ),
                self.update_led('#4CAF50')
            ])
        else:
            self.mark_serial(serial_num, SerialStatus.ERROR)
            self.log(f"自動燒錄失敗: {serial_num}")
            self.root.after(0, lambda: [
                self.flash_btn.config(
                    bg='#F44336',
                    fg='white'
                ),
                self.update_led('#F44336')
            ])
            
        self.root.after(2000, lambda: [
            self.flash_btn.config(
                text="燒錄序號",
                bg='#e0e0e0',
                fg='black',
                state='normal'
            ),
            self.update_serial_list()
        ])
        
        self.disconnect()

    def ask_auto_overwrite(self, existing, new):
        self.root.attributes('-topmost', True)
        result = messagebox.askyesno(
            "自動模式確認",
            f"檢測到設備已有序號:\n{existing}\n\n是否要覆寫為:\n{new}",
            parent=self.root
        )
        self.root.attributes('-topmost', False)
        return result

    def test_led(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showerror("錯誤", "請先連接設備")
            return
            
        commands = [
            "GET_SERIAL",
            "DEBUG_LEVEL:2",
            "SET_SERIAL:TEST",
            "INVALID_CMD"
        ]
        
        for cmd in commands:
            self.log(f"測試LED指令: {cmd}")
            self.send_command(cmd)
            time.sleep(2)

if __name__ == "__main__":
    # 建立預設圖示
    img = Image.new('RGB', (64, 64), color='blue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([16, 16, 48, 48], fill='white')
    img.save('default_icon.ico')
    
    root = tk.Tk()
    app = ESP32FlasherApp(root)
    root.mainloop()