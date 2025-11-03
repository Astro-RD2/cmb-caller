# Caller module 開發環境建置
本文件描述如何於個人 PC 建置 **Caller moduler (ESP32)** 開發環境.

## 基本需求
- PC
  - Windows 10 or later version
  - RAM 4G, Disk 128G least
- Caller module
  - ESP32 (WiFi/Bluetooth, 4K flash least)
  - USB cable between Caller module and PC

## 步驟
1. 安裝 Arduino IDE (文件撰寫時版本 2.3.4) (https://www.arduino.cc/en/software)
2. 安裝指定 Board manager
    - 於 Arduino IDE->File->Preferences->Additional boards manager URL's, 填入如下:  
      https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json
    - 於 Arduino IDE->左邊側欄->Boards Manager->搜索 "esp32"  
      選擇安裝 "esp32 by Espressit" (文件撰寫時版本 3.1.1, 更新後 3.2.0-RC2)
3. 安裝 virtual comm driver  
   因為所使用的 ESP32 使用相容 CP2102 USB/UART bridge controller, 所以請參考如下安裝驅動程式:  
   https://sites.google.com/site/arduinochutiyan/esp32_%E5%9F%BA%E7%A4%8E/1-cp2102x-%E9%A9%85%E5%8B%95%E7%A8%8B%E5%BC%8F%E5%AE%89%E8%A3%9D  
   *註: 我這裡實際例子, 會安裝 arduino-ide_2.3.4_Windows_64bit.exe*
4. USB cable 連接 ESP32 Caller module  
   於裝置管理員 (device manager), 應該會自動出現某一項目例如:  
   CP2102 USB to UART bridge controler (COM3)  
   *註: 不一定是 COM3, 也可能是其它, 例如 COM4, COM5*
5. 選擇 Board 與 Port  
   於 Arduino IDE->Tools->Board:/Port:  
       Board: "ESP32 Dev Module"  
       Port: "COM3" ```     ```<-- 選擇該 USB 對應的 Virtual COM port, e.g COM3
6. 編譯然後上傳至 Caller module  
   Arduino IDE->Sketch->Verify/Compile [Ctrl-R] 進行程式碼驗證.  
   Arduino IDE->Sketch->Upload [Ctrl-U] 進行編譯並會於成功時自動上傳至 Caller module.

## 開發架構圖
```
Caller device                    Development PC/Laptop                       
+-----------------+              +-----------------------------------------------------------+
| Caller module   |              | Windows 10/11 (64bit)             [Source directory]      |
| (ESP32)         |--------------| (Arduino IDE)                     cmb-caller/             |
|                 |  USB cable   |         ^                           Src/                  |
|                 |              |         |                             cmb-caller/         |
+-----------------+              |         +----------- Open ------------- cmb-caller.ino    |
        .                        |                                         credentials.h     |
        .                        +-----------------------------------------------------------+
        .WiFi
        .
        . 
+-----------------+
| WiFi AP         |
| SSID: CMBz0001  |
+-----------------+
```


