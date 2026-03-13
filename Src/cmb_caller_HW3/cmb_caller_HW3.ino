/*
 * 修改紀錄:
 * 2025-xx-xx: Roy Ching  初始版本.
 * 2025-03-11: Roy Ching  增加資料BUFFER.
 * 2025-03-12: Roy Ching  加強斷線斷訊重傳功能.
 * 2025-03-12: Roy Ching  Webscok重連時傳送系統資訊.
 * 2025-03-13: Roy Ching  程式重整.
 * 2025-03-14: Roy Ching  GCE IP 改用DNS轉址.
 * 2025-03-24: Roy Ching  Websocket LIB 由 <ArduinoWebsockets.h>  改為用  <WebSocketsClient.h> (For GCR).
 * 2025-03-24: Roy Ching  支援 GCE 或 GCR.
 * 2025-03-24: Roy Ching  可支援直接使用鍵盤訊號訊號.
 * 2025-03-26: Roy Ching  只支援 H/W Ver.2.0.
 * 2025-03-27: Roy Ching  顯示 scan 資訊.
 * 2025-03-27: Roy Ching  convertToNumber delay 50 us.
 * 2025-03-28: Roy Ching  增加藍色LED(版上)與紅色LED(外加)反向顯示.
 * 2025-03-28: Roy Ching  支援 H/W Ver.2.0 & H/W Ver.1.0.
 * 2025-03-31: Roy Ching  移除 "支援直接使用鍵盤訊號訊號" 功能.
 * 2025-03-31: Roy Ching  硬體錯誤顯示紅燈.
 * 2025-04-07: Roy Ching  修正 1000000 歸零當機問題.
 * 2025-04-16: Roy Ching  加入 'auth' 及 'info' 通訊支援.
 * 2025-04-24: Roy Ching  只支援HW 3.0 , 藍牙傳輸(ESP32 * 3)
 * 2025-06-12: Roy Ching  增加遠端及 STA 設定 WiFi 連線功能.
 * 2025-06-12: Roy Ching  自動連線會依順序並依掃描結果連線是否存在來連線.
 * 2025-06-12: Roy Ching  修正 Websocket 斷線 WiFi 也重連之問題.
 * 2025-06-12: Roy Ching  修正雲端傳入後又上傳雲端的問題.
 * 2025-06-12: Roy Ching  加入使用按鍵開啟STA功能.
 * 2025-06-13: Roy Ching  先設 WIFI_AP_STA 再換 WIFI_STA, (機號 a0105 需如此才不會切換至 WIFI_AP_STA 時 Reboot)
 * 2025-06-16: Roy Ching  WiFi 設定改 WIFI_AP_STA 固定不變換，直接enable ' disable AP，避免reboot問題.
 * 2025-06-16: Roy Ching  增加狀態 STATE_RESTORE.
 * 2025-06-17: Roy Ching  增加 login 時 get 同步號碼.
 * 2025-06-17: Roy Ching  cldUR2Send 改 0~999
 * 2025-06-17: Roy Ching  開機 WiFi 設 WIFI_AP_STA ' WiFi.softAPdisconnect(true).
 * 2025-06-17: Roy Ching  支援近端 WiFi 設定.
 * 2025-06-26: Roy Ching  參數 device_id 改 caller_id, 變數 deviceId 改 callerId
 * 2025-06-27: Roy Ching  wifi_get_status 增加回覆 password 參數.
 * 2025-06-27: Roy Ching  支援遠端 WiFi 設定.
 * 2025-07-07: Roy Ching  設定 webSocketClient.setReconnectInterval(1) , 加快斷線重連速度.
 * 2025-07-08: Roy Ching  顯示斷線時間.
 * 2025-09-01: Roy Ching  login 時比對最後兩組號碼以避免重複叫號.
 */


#define VERSION "HW3_20250901"


// 引入必要的函式庫
#include <WebSocketsClient.h>    // 用於 WebSocket 通訊
#include <Arduino.h>             // Arduino 核心函式庫
#include <WiFi.h>                // ESP32 WiFi 功能
#include <ArduinoOTA.h>          // OTA 更新功能
// #include "freertos/FreeRTOS.h"   // FreeRTOS 相關功能
// #include "freertos/task.h"       // FreeRTOS 任務管理
// #include "esp_freertos_hooks.h"  // FreeRTOS 鉤子函數
#include "sdkconfig.h"           // ESP32 SDK 配置
#include <WebServer.h>           // Web 伺服器功能
#include <Preferences.h>         // 用於存儲偏好設定
#include <ESPping.h>             // Ping 功能
// #include <ESPmDNS.h>
#include <ArduinoJson.h>  // 用於 JSON 解析和產生

// 引入自定義的憑證檔案（WiFi SSID 和密碼...）
#include "credentials.h"

// 程式版本資訊
#ifndef LOCAL_TEST
String Version = VERSION;
#else
String Version = String(VERSION) + " Local Test!";
#endif

// 宣告外部函數（用於獲取任務運行時間統計）
extern void vTaskGetRunTimeStats(char* pcWriteBuffer);

// 呼叫號碼（用於識別設備）
String Caller_Number = "00000";  // 會變

#define LED_RED 33    // 紅色 LED
#define LED_GREEN 32  // 綠色 LEDSCAN_NUM
#define LED_BLUE 2    // 藍色 LED

// 計時器和網路相關設定
const long WIFI_TIMEOUT = 7000;  // WiFi 連接超時時間（7 秒）
// const long WS_TIMEOUT = 5000;             // WebSocket 連接超時時間（5 秒）
const long STATE_UPDATE_INTERVAL = 500;  // 狀態更新間隔（500 毫秒）
const long PING_INTERVAL = 30000;        // Ping 間隔（30 秒）
// const long ON_MESSAGE_TIMEOUT = 10000;    // onMessage 超時時間（10 秒）
const long printInterval = (60 * 60000);  // 系統訊息列印間隔（60 分鐘）
// const long CHECK_DISPLAY_INTERVAL = 100;  // 中斷取樣間隔（100 毫秒）
// const long SCAN_NUM = 3;                  // 中斷取樣次數, 2025/03/28, 6->3
const long CHECK_NUMBER_INTERVAL = 50;  // 數值變動取樣間隔（50 毫秒）

// 系統變數
unsigned long lastPING = 0;  // 上次 Ping 時間
// unsigned long delayStart = 0;                     // 延遲起始時間
// int currentNetwork = 0;                           // 當前 WiFi 網路索引
volatile unsigned long onMessage_time = 0;  // onMessage 計時器
unsigned long lastPrintTime = millis();     // 上次列印系統訊息時間
unsigned long lastCheckNumber = 0;          // 上次檢查數字時間
// volatile unsigned long InterruptCount = 0;        // 中斷計數器
// volatile unsigned long scanDisplayCount = 0;      // 數字掃描計數器
volatile unsigned long currentMillis = millis();  // 當前時間
// volatile unsigned long lastScanDisplayTime = 0;   // 上次數字掃描時間
// volatile int scanCallCount = 0;                   // 數字掃描呼叫次數

// 呼叫號碼相關定義
const char Caller_Prefix[] = "CMB";                                   // 呼叫號碼前綴
char Caller_SSID[sizeof(Caller_Prefix) + sizeof(Caller_Number) - 1];  // 呼叫號碼 SSID

// CPU 負載量變數
volatile uint32_t idleCount[portNUM_PROCESSORS] = { 0 };      // 空閒計數
volatile uint32_t idleCountLast[portNUM_PROCESSORS] = { 0 };  // 上次空閒計數

/*
// 數字顯示相關變數
int fe[3] = { 0 };                       // 數字顯示狀態
volatile int n1 = -1, n2 = -1, n3 = -1;  // 當前數字
int pn1 = -2, pn2 = -2, pn3 = -2;        // 上次數字
volatile bool has_interrupted = false;   // 中斷標記
hw_timer_t* timer0;                      // 硬體計時器
String preStr = "0";                     // 上次數字字串
int matchCt = 0;                         // 數字匹配計數器
*/

String nowStr = "0";           // 當前數字字串
String nowStrDemo = "0";       // Demo 模式數字字串
String sendStr = "000";        // 發送數字字串
String lastSendStr = sendStr;  // 前一次發送數字字串
bool bypassLast = false;

// WebSocket 客戶端
WebSocketsClient webSocketClient;


// Demo 模式相關設定
const int BUTTON_PIN = 0;  // 按鈕腳位
// const int LED_PIN = 32;                    // LED 腳位
const long CHECK_IO0_INTERVAL = 100;       // 按鈕檢測間隔（100 毫秒）
const long MULTI_CLICK_INTERVAL = 1000;    // 連續按壓有效時間（500 毫秒）
const int CLICK_COUNT_TARGET = 2;          // 目標按壓次數
const unsigned long MIN_INTERVAL = 30000;  // 最小更新間隔（30 秒）
const unsigned long MAX_INTERVAL = 90000;  // 最大更新間隔（90 秒）
const int MIN_CHANGE = -1;                 // 最小變化值
const int MAX_CHANGE = 2;                  // 最大變化值
const int MIN_VALUE = 1;                   // 最小允許值
const int MAX_VALUE = 999;                 // 最大允許值

// 狀態變數STA
bool demoState = false;             // Demo 模式狀態
int clickCount = 0;                 // 按鈕計數
unsigned long lastCheckIO0 = 0;     // 上次按鈕檢查時間
unsigned long lastButtonPress = 0;  // 上次按鈕按下時間
unsigned long lastUpdateTime = 0;   // 上次更新時間
unsigned long nextUpdateInterval;   // 下次更新間隔
bool lastButtonState = HIGH;        // 上次按鈕狀態


// 系統狀態枚舉
enum SystemState {
  STATE_INIT,                  // 初始狀態
  STATE_WIFI_CONNECTING,       // WiFi 連接中
  STATE_WIFI_CONNECTED,        // WiFi 已連接
  STATE_WEBSOCKET_CONNECTING,  // WebSocket 連接中
  STATE_WEBSOCKET_CONNECTED,   // WebSocket 已連接
  STATE_ERROR,                 // 錯誤狀態
  STATE_DEMO,                  // Demo 模式
  STATE_TRANS,                 // 傳輸狀態
  STATE_AP_STA,                // AP_STA 模式, 8
  STATE_AP_STA_C,              // AP_STA_C 模式, 已連線. 9
  STATE_NUMBER_ERROR,          // 數字掃描硬體錯誤, 10
  STATE_RESTORE,               // 回復舊值, 11
  STATE_COUNT                  // 狀態總數
};

// 系統狀態結構
struct Status {
  SystemState state;              // 當前系統狀態
  unsigned long lastStateChange;  // 上次狀態變更時間
  String lastError;               // 最後錯誤訊息
  int wifiAttempts;               // WiFi 連接嘗試次數
  int websocketAttempts;          // WebSocket 連接嘗試次數
  String currentSSID;             // 當前 WiFi SSID
} status;

// LED 控制結構
struct LedState {
  bool isOn;                 // LED 當前狀態
  bool isBlinking;           // 是否閃爍
  unsigned long onTime;      // 亮持續時間（毫秒）
  unsigned long offTime;     // 滅持續時間（毫秒）
  unsigned long lastToggle;  // 最後切換時間
};

// LED 配置
struct LedConfig {
  LedState red;    // 紅色 LED 狀態
  LedState green;  // 綠色 LED 狀態
} ledConfigs[STATE_COUNT];

// FreeRTOS 計時器
TimerHandle_t redTimer;    // 紅色 LED 計時器
TimerHandle_t greenTimer;  // 綠色 LED 計時器
// bool setup_finish = false;  // 初始化完成標記

/*
// IP 地址列表
int xxx = 0;  // 預留 IP 地址
IPAddress ipList[] = {
  IPAddress(xxx, xxx, xxx, 128),
  IPAddress(xxx, xxx, xxx, 118),
  IPAddress(xxx, xxx, xxx, 108)
};
const int IP_COUNT = sizeof(ipList) / sizeof(ipList[0]);
*/

// 當前 IP 索引與循環計數
int currentIpIndex = 0;
int loopCount;         // 循環次數 !!!@@@
IPAddress* ipListPtr;  // 指向選擇的 IP 列表 !!!@@@
bool useDhcp = false;  // 是否使用 DHCP

// IP 地址相關變數
IPAddress apIP;     // AP IP 地址
IPAddress LocalIP;  // 本地 IP 地址
IPAddress gateway;  // 閘道 IP 地址
IPAddress subnet;   // 子網掩碼
IPAddress dns;      // DNS 伺服器

// Web 伺服器實例
// WebServer server(80);     // Web 伺服器端口 80
// Preferences preferences;  // 偏好設定

// 存儲的資料
String savedData1 = "";        // 存儲資料 1
String savedData2 = "";        // 存儲資料 2
String savedData3 = "";        // 存儲資料 3
volatile bool NullId = false;  // 空 ID 標記

// 開機時間與失效時間
unsigned long startTime = 0;                           // 開機時間
const unsigned long expireMinutes = 10;                // Maint_mode 失效時間（10 分鐘）
unsigned long expireTime = expireMinutes * 60 * 1000;  // Maint_mode 失效時間（毫秒）


// 資料緩衝區設定
#define NUM_BUFFER_SIZE 60
int num_buffer[NUM_BUFFER_SIZE];
int num_head = 0;
int num_tail = 0;

// 其他變數
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 10;  // 設定發送偵測間隔時間，例如 10 ms
unsigned long randomInterval = 0;
unsigned long sendTime;
bool waitingResponse = false;
int retryValue;
bool retryMode = false;
const int retryTimeout = 5;  // 重試超時時間 (秒)

// 網路狀態監控變數
bool wasConnected = false;
unsigned long lastWifiCheckTime = 0;
const int wifiCheckInterval = 5000;  // 檢查WiFi狀態的間隔時間(毫秒)
unsigned long lastReconnectTime = 0;
const int reconnectCooldown = 10000;  // 避免頻繁重連的冷卻時間(毫秒)
int reconnectAttempts = 0;
const int maxReconnectAttempts = 5;  // 最大重試次數

// WebSocket 狀態監控變數
// unsigned long lastWebSocketCheckTime = 0;
// const int webSocketCheckInterval = 3000;  // 檢查WebSocket狀態的間隔時間(毫秒)
// unsigned long lastWSReconnectAttempt = 0;
// const int wsReconnectCooldown = 5000;  // WebSocket重連冷卻時間(毫秒)
// unsigned long lastPingTime = 0;
// const int pingInterval = 10000;  // Ping間隔時間(毫秒)
// int wsReconnectAttempts = 0;
// const int maxWSReconnectAttempts = 5;  // 最大WebSocket重試次數

unsigned long lastCheckTime = millis();  // 記錄最後一次掃描網路的時間

const int RETRY_COUNT = 1;
bool Maint_mode = true;

String ssid;
String password;
bool new_connect = false;
int ping_EX_no_reply_count = 0;
int sendPing_fail = 0;
// 在全域變數區域加入
#define MINIMUM_HEAP 20000  // 設定最小堆積記憶體門檻值（依需求調整）
portMUX_TYPE statsMutex = portMUX_INITIALIZER_UNLOCKED;
int idleRate[2] = { configTICK_RATE_HZ, configTICK_RATE_HZ };

unsigned long websocket_connect_time = millis();  // WebSocket 重連時間
// #define MAX_WEBS_RTY_TIME (60 * 1000)

int AP_mode = 0;

#define STATUS_INTERVAL 500  // 狀態顯示間隔(0.5秒)
static unsigned long lastCheck = 0;
bool WebSocket_init = false;

//======================================================================
// 函數原型宣告
void updateSystemState(SystemState newState, const String& error = "");
// bool connectToWiFi(const char* ssid_in, const char* password_in);
void GetSendCallerNumber(unsigned long currentMillis);
void initLedConfigs();
void updateLEDState();
void blinkLED(TimerHandle_t xTimer);
void setupOTA();
void setupWebSocket();
void scanAndValidateNetworks();
void handleRoot();
void handleStore();
void handleRetrieve();
void handleStatus();
// void checkConnections();
// void onMessageCallback(String message);
void onMessageCallback(const String& message);

void checkMemory();
void Ping_EX();
void printTaskStats();
void GetRunTimeStats();
void resetRuntimeStats();
void showTaskLoad();
void check_system(unsigned long lastCheckTime, unsigned long currentMillis);
void calculateCPULoad(unsigned long lastCheckTime, unsigned long currentMillis);
void handleButton(unsigned long currentMillis);
void handleDemoMode(unsigned long currentMillis);
void toggleDemoMode();
void client_send(const String& message);
void buffer_push(int value);
bool buffer_pop(int& value);
void sendBufferedData();
void sendWebSocketMessage(int value);
void checkResponse();
void add_profile(const char* ssid, const char* password);
void WiFi_reconnect();

void change_AP_mode();
bool UR2Recv();
void process_change_AP_mode(int code);
void parseUpdateMessage(const String& msg);
void num_LED_dis(const String& message);
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length);
void check_auth();
void cldUR2Send(unsigned long num);

//=========================================================================

#define TX2 17
#define RX2 16

HardwareSerial mySerial(2);  // 初始化硬體UART2

#define MAX_NETWORKS 15
#define MAX_USER_NETWORKS 10
#define WEBSOCKET_PORT 81  // WebSocket 伺服器端口

// 合併後的網路清單 (RAM中)
WiFiNetwork wifiNetworks[MAX_NETWORKS];
uint8_t networkCount = 0;

// 用戶新增網路 (永久儲存)
Preferences preferences;
WebServer server(80);

struct ScannedNetwork {
  String ssid;
  String bssid;
  int8_t rssi;
  int channel;
  String encryption;
};
std::vector<ScannedNetwork> scannedNetworks;  // 儲存掃描到的網路資訊


// !!!@@@
const unsigned long SCAN_INTERVAL = 60 * 60 * 1000;  // 每 xx 分鐘掃描一次
const unsigned long SCAN_MIN_INTERVAL = 30000;       // 最快 30 秒掃描一次

// unsigned long lastScanTime = 0;
unsigned long lastScanTime = millis() - SCAN_INTERVAL;
unsigned long lastScanTimeRun = millis() - SCAN_MIN_INTERVAL;

const int MIN_ACCEPTABLE_RSSI = -85;                // dBm，低於此值認為訊號微弱
const int MIN_SAVE_RSSI = MIN_ACCEPTABLE_RSSI - 0;  // dBm，低於此值認為訊號非常微弱

const unsigned long CONNECT_RETRY_DELAY = 1000;  // 連線失敗後重試的延遲

// unsigned long lastConnectAttempt = 0;
unsigned long lastConnectAttempt = millis() - CONNECT_RETRY_DELAY - 1000;
// unsigned long lastConnectAttempt = millis();

bool isScanning = false;  // 標記是否正在掃描中
unsigned long scanStartTime = 0;

unsigned long lastDisconnectTime = 0;
const unsigned long RECONNECT_DELAY = 1000;  // 1秒延遲後重試

// ====== 工具函式 ======
uint8_t min(uint8_t a, uint8_t b) {
  return (a < b) ? a : b;
}

// ====== 從 Preferences 載入用戶網路 ======
void loadNetworks() {
  preferences.begin("wifi-config", false);

  uint8_t savedCount = preferences.getUChar("count", 0);
  savedCount = min(savedCount, MAX_USER_NETWORKS);

  for (int i = 0; i < savedCount; i++) {
    String prefix = "net" + String(i);
    String ssid = preferences.getString((prefix + "ssid").c_str(), "");
    String pass = preferences.getString((prefix + "pass").c_str(), "");

    if (ssid.length() > 0 && networkCount < MAX_NETWORKS) {
      strncpy(wifiNetworks[networkCount].ssid, ssid.c_str(), 31);
      strncpy(wifiNetworks[networkCount].password, pass.c_str(), 63);
      wifiNetworks[networkCount].enabled = true;
      wifiNetworks[networkCount].rssi = 0;
      wifiNetworks[networkCount].isUserAdded = true;
      // Serial.printf("loadUserNetworks isUserAdded: %s\n", wifiNetworks[i].ssid);
      Serial.printf("loadUserNetworks isUserAdded: %s\n", wifiNetworks[networkCount].ssid);
      networkCount++;
    }
  }

  preferences.end();
}

// ====== 保存用戶網路到 Preferences ======
void saveNetworks() {
  Serial.printf("saveNetworks()!\n");
  preferences.begin("wifi-config", false);

  // 先計算用戶新增的網路數量
  uint8_t userCount = 0;
  for (int i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) userCount++;
  }

  preferences.putUChar("count", userCount);

  // 只保存用戶新增的網路
  uint8_t savedIndex = 0;
  Serial.printf("saveNetworks():networkCount=%d,savedIndex=%d,userCount=%d\n", networkCount, savedIndex, userCount);
  for (int i = 0; i < networkCount && savedIndex < userCount; i++) {
    Serial.printf("saveNetworks Check: %s\n", wifiNetworks[i].ssid);

    if (wifiNetworks[i].isUserAdded) {
      String prefix = "net" + String(savedIndex);
      preferences.putString((prefix + "ssid").c_str(), String(wifiNetworks[i].ssid));
      preferences.putString((prefix + "pass").c_str(), String(wifiNetworks[i].password));
      savedIndex++;
      Serial.printf("saveNetworks Save: %s\n", wifiNetworks[i].ssid);
    }
  }

  preferences.end();
}

const char* getPasswordForSsid(const char* ssid) {
  for (uint8_t i = 0; i < networkCount; i++) {
    if (strcmp(wifiNetworks[i].ssid, ssid) == 0) {
      return wifiNetworks[i].password;
    }
  }
  return "";  // 如果找不到對應的SSID，返回空密碼
}

void addNetwork(const char* ssid, const char* password) {
  Serial.printf("addNetwork:%s,%s\n", ssid, password);
  // 先檢查是否已存在
  for (uint8_t i = 0; i < networkCount; i++) {
    if (strcmp(wifiNetworks[i].ssid, ssid) == 0) {
      Serial.printf("addNetwork 用戶已存在:%s\n", ssid);
      // 已存在則更新密碼
      strncpy(wifiNetworks[i].password, password, 63);
      wifiNetworks[i].password[63] = 0;

      // 一律設成用戶新增的
      wifiNetworks[i].isUserAdded = true;
      // 如果是用戶新增的，移到最前面
      if (wifiNetworks[i].isUserAdded) {
        WiFiNetwork temp = wifiNetworks[i];
        for (uint8_t j = i; j > 0; j--) {
          wifiNetworks[j] = wifiNetworks[j - 1];
        }
        wifiNetworks[0] = temp;
      }
      // saveNetworks();
      // 添加後立即嘗試連接新熱點
      // attemptConnectNewNetwork(ssid);
      return;
    }
  }

  // 不存在則新增到最前面
  if (networkCount < MAX_NETWORKS) {
    Serial.printf("addNetwork 添加新用戶:%s\n", ssid);
    // 將現有網路向後移動
    for (uint8_t i = networkCount; i > 0; i--) {
      wifiNetworks[i] = wifiNetworks[i - 1];
    }

    // 添加新網路到首位
    strncpy(wifiNetworks[0].ssid, ssid, 31);
    wifiNetworks[0].ssid[31] = 0;
    strncpy(wifiNetworks[0].password, password, 63);
    wifiNetworks[0].password[63] = 0;
    wifiNetworks[0].enabled = true;
    wifiNetworks[0].rssi = 0;
    wifiNetworks[0].isUserAdded = true;
    networkCount++;

    // saveNetworks();
    // 添加後立即嘗試連接新熱點
    // attemptConnectNewNetwork(ssid);
  }
}

void deleteNetwork(uint8_t idx) {
  uint8_t userNetworkIndex = 0;
  uint8_t foundIndex = 255;  // 標記要刪除的用戶網路在 user-added 列表中的索引

  // 找到要刪除的用戶網路在用戶列表中的索引
  for (uint8_t i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) {
      if (userNetworkIndex == idx) {
        foundIndex = i;
        break;
      }
      userNetworkIndex++;
    }
  }

  if (foundIndex != 255) {
    // 將後面的網路向前移動
    for (uint8_t i = foundIndex; i < networkCount - 1; i++) {
      wifiNetworks[i] = wifiNetworks[i + 1];
    }
    networkCount--;
    saveNetworks();
  }
}

void moveNetwork(uint8_t from, uint8_t to) {
  uint8_t userFromIndex = 0;
  uint8_t userToIndex = 0;
  uint8_t foundFromIndex = 255;
  uint8_t foundToIndex = 255;
  uint8_t currentUserIndex = 0;

  // 找到要移動的兩個用戶網路在完整列表中的索引
  for (uint8_t i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) {
      if (userFromIndex == from) foundFromIndex = i;
      if (userToIndex == to) foundToIndex = i;
      userFromIndex++;
      userToIndex++;
    }
  }

  if (foundFromIndex != 255 && foundToIndex != 255 && foundFromIndex != foundToIndex) {
    WiFiNetwork temp = wifiNetworks[foundFromIndex];
    if (foundFromIndex < foundToIndex) {
      for (uint8_t i = foundFromIndex; i < foundToIndex; i++) {
        wifiNetworks[i] = wifiNetworks[i + 1];
      }
    } else {
      for (uint8_t i = foundFromIndex; i > foundToIndex; i--) {
        wifiNetworks[i] = wifiNetworks[i - 1];
      }
    }
    wifiNetworks[foundToIndex] = temp;
    saveNetworks();
  }
}

// ====== 合併預設網路 ======
void mergeDefaultNetworks() {
  // 添加預設網路到最後面 (只添加不存在的)
  for (uint8_t i = 0; i < defaultNetworkCount; i++) {
    bool exists = false;
    for (uint8_t j = 0; j < networkCount; j++) {
      if (strcmp(wifiNetworks[j].ssid, defaultNetworks[i].ssid) == 0) {
        exists = true;
        break;
      }
    }

    if (!exists && networkCount < MAX_NETWORKS) {
      wifiNetworks[networkCount] = defaultNetworks[i];
      networkCount++;
    }
  }
}

// ====== AP模式啟用 ======
void setupAP() {
  WiFi.softAP("CMB Caller", "88888888");
  updateSystemState(STATE_AP_STA);
  Serial.print("AP 啟動，IP：");
  Serial.println(WiFi.softAPIP());
  delay(500);  // 等待 !!!@@@
}

void disableAP() {
  Serial.print("AP 關閉!\n");
  // WiFi.softAP("CMB Caller Disable", "xxxx");
  WiFi.softAPdisconnect(true);  // true = 完全關閉
  updateSystemState(STATE_RESTORE);
  // delay(500);  // 等待資源釋放
  // 方法1: 直接關閉
}
String scanWiFiListJSON(const String& callerId, const String& uuid = "") {
  // DynamicJsonDocument jsonDoc(2048);
  JsonDocument jsonDoc = DynamicJsonDocument(2048);

  jsonDoc["action"] = "wifi_scan_list";
  jsonDoc["caller_id"] = callerId;
  if (!uuid.isEmpty()) {
    jsonDoc["uuid"] = uuid;
  }
  jsonDoc["result"] = "OK";
  JsonObject data = jsonDoc.createNestedObject("data");
  JsonArray networks = data.createNestedArray("networks");

  // 使用已掃描的網路資料
  for (const auto& network : scannedNetworks) {
    JsonObject net = networks.createNestedObject();
    net["ssid"] = network.ssid;
    net["bssid"] = network.bssid;
    net["rssi"] = network.rssi;
    net["channel"] = network.channel;
    net["encryption"] = network.encryption;
  }

  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

// ====== 取得 WiFi 狀態並回傳 JSON ======
String getWiFiStatusJSON(const String& callerId, const String& uuid = "") {
  DynamicJsonDocument jsonDoc(256);
  jsonDoc["action"] = "wifi_get_status";
  jsonDoc["caller_id"] = callerId;
  if (!uuid.isEmpty()) {
    jsonDoc["uuid"] = uuid;
  }
  jsonDoc["result"] = "OK";
  JsonObject data = jsonDoc.createNestedObject("data");
  data["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  if (WiFi.status() == WL_CONNECTED) {
    data["current_ssid"] = WiFi.SSID();
    data["password"] = password;
    data["ip_address"] = WiFi.localIP().toString();
    data["rssi"] = WiFi.RSSI();
  } else {
    data["current_ssid"] = "";
    data["password"] = "";
    data["ip_address"] = "";
    data["rssi"] = 0;
  }

  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

// ====== 取得已儲存 WiFi 設定並回傳 JSON ======
String getWiFiProfilesJSON(const String& callerId, const String& uuid = "") {
  DynamicJsonDocument jsonDoc(1024);
  jsonDoc["action"] = "wifi_get_profiles";
  jsonDoc["caller_id"] = callerId;
  if (!uuid.isEmpty()) {
    jsonDoc["uuid"] = uuid;
  }
  jsonDoc["result"] = "OK";
  JsonObject data = jsonDoc.createNestedObject("data");           // 先創建 data 物件
  JsonArray credentials = data.createNestedArray("credentials");  // 再在 data 中創建 credentials 陣列

  uint8_t userNetworkIndex = 0;
  for (uint8_t i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) {
      JsonObject credential = credentials.createNestedObject();
      credential["ssid"] = wifiNetworks[i].ssid;
      // credential["password"] = "********";  // 隱藏密碼
      credential["password"] = wifiNetworks[i].password;
      credential["priority"] = userNetworkIndex + 1;
      userNetworkIndex++;
    }
  }

  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

// ====== 產生成功回應 JSON ======
String generateSuccessResponse(const String& action, const String& callerId, const String& uuid = "") {
  DynamicJsonDocument jsonDoc(128);
  jsonDoc["action"] = action;
  jsonDoc["caller_id"] = callerId;
  if (!uuid.isEmpty()) {
    jsonDoc["uuid"] = uuid;
  }
  jsonDoc["result"] = "OK";
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

// ====== 產生錯誤回應 JSON ======
String generateErrorResponse(const String& action, const String& callerId, const String& uuid, const String& errorCode, const String& errorMessage = "") {
  DynamicJsonDocument jsonDoc(256);
  jsonDoc["action"] = action;
  jsonDoc["caller_id"] = callerId;
  if (!uuid.isEmpty()) {
    jsonDoc["uuid"] = uuid;
  }
  jsonDoc["result"] = "Fail, " + errorCode + ":" + errorMessage;
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

void handleRoot() {
  Serial.println("handleRoot");
  String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>WiFi 連線設定</title>";

  // 加入響應式 meta 標籤和 CSS 樣式
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<style>";
  html += "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; box-sizing: border-box; width: 100%; max-width: 100%; }";
  html += "h2 { color: #333; }";
  html += "form { margin: 20px 0; }";
  // html += "select, input[type='password'], input[type='submit'] { width: 100%; padding: 8px; margin: 5px 0 15px; box-sizing: border-box; }";
  html += "select, input[type='text'], input[type='submit'] { width: 100%; padding: 8px; margin: 5px 0 15px; box-sizing: border-box; }";
  html += "table { width: 100%; border-collapse: collapse; margin: 15px 0; }";
  html += "th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }";
  html += "a { margin-right: 10px; color: #0066cc; text-decoration: none; }";
  html += "a:hover { text-decoration: underline; }";
  html += "hr { margin: 20px 0; border: 0; border-top: 1px solid #eee; }";
  html += "@media (min-width: 768px) { body { padding: 20px 10%; } }";
  html += "</style></head><body>";

  html += "<h2>WiFi 連線設定</h2>";
  html += "叫號機號碼：" + Caller_Number + "<br>";
  html += "<b>目前連線狀態：</b><br>";
  if (WiFi.status() == WL_CONNECTED) {
    html += "已連線至 " + WiFi.SSID() + "<br>";
    html += "IP位址：" + WiFi.localIP().toString() + "<br>";
  } else {
    html += "尚未連線<br>";
  }
  // html += "AP模式 IP：" + WiFi.softAPIP().toString() + "<br><hr>";

  html += "<h3>新增 WiFi 熱點</h3>";
  html += "<form method='POST' action='/add_http'>";
  html += "選擇熱點：<select name='ssid'>";

  for (const auto& network : scannedNetworks) {
    html += "<option value='" + network.ssid + "'>" + network.ssid + " (" + network.rssi + "dBm)</option>";
  }

  html += "</select><br>";
  // html += "密碼：<input type='password' name='password'><br>";
  html += "密碼：<input type='text' name='password'><br>";
  html += "<input type='submit' value='加入熱點'>";
  html += "</form>";

  // 新增手動輸入按鍵
  html += "<form method='GET' action='/add_manual'>";
  html += "<input type='submit' value='手動輸入WiFi熱點'>";
  html += "</form><hr>";

  html += "<h3>已儲存 WiFi 熱點</h3>";
  html += "<table><tr><th>#</th><th>SSID</th><th>操作</th></tr>";
  uint8_t userNetworkIndex = 0;
  for (uint8_t i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) {
      html += "<tr><td>" + String(userNetworkIndex + 1) + "</td>";
      html += "<td>" + String(wifiNetworks[i].ssid) + "</td>";
      html += "<td><a href='/delete_http?idx=" + String(userNetworkIndex) + "'>刪除</a> ";
      if (userNetworkIndex > 0) html += "<a href='/move_up_http?idx=" + String(userNetworkIndex) + "'>↑</a> ";
      uint8_t totalUserNetworks = 0;
      for (int j = 0; j < networkCount; j++)
        if (wifiNetworks[j].isUserAdded) totalUserNetworks++;
      if (userNetworkIndex < totalUserNetworks - 1) html += "<a href='/move_down_http?idx=" + String(userNetworkIndex) + "'>↓</a> ";
      html += "</td></tr>";
      userNetworkIndex++;
    }
  }
  html += "</table>";
  // html += "<hr><small>CMB Caller</small></body></html>";
  server.send(200, "text/html", html);

  Serial.printf("handleRoot 設定立即 WiFi 掃描!\n");  // 可能熱點剛啟動.
  lastScanTime = millis() - SCAN_INTERVAL;
  lastScanTimeRun = lastScanTime - SCAN_MIN_INTERVAL;
}

void handleAddManual() {
  Serial.println("handleAddManual");

  // 如果是POST請求，處理表單提交
  if (server.method() == HTTP_POST) {
    String ssid = server.arg("ssid");
    String password = server.arg("password");

    if (ssid.length() > 0) {
      add_profile(ssid.c_str(), password.c_str());
      // 重定向回主頁面
      server.sendHeader("Location", "/");
      server.send(302, "text/plain", "");
      WiFi_reconnect();
      return;
    }
  }

  // 顯示手動輸入表單
  String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>手動輸入WiFi熱點</title>";

  // 使用相同的CSS樣式
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<style>";
  html += "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; box-sizing: border-box; width: 100%; max-width: 100%; }";
  html += "h2 { color: #333; }";
  html += "form { margin: 20px 0; }";
  // html += "input[type='text'], input[type='password'], input[type='submit'] { width: 100%; padding: 8px; margin: 5px 0 15px; box-sizing: border-box; }";
  html += "input[type='text'], input[type='text'], input[type='submit'] { width: 100%; padding: 8px; margin: 5px 0 15px; box-sizing: border-box; }";
  html += "a { margin-right: 10px; color: #0066cc; text-decoration: none; }";
  html += "a:hover { text-decoration: underline; }";
  html += "@media (min-width: 768px) { body { padding: 20px 10%; } }";
  html += "</style></head><body>";

  html += "<h2>手動輸入WiFi熱點</h2>";
  html += "<form method='POST' action='/add_manual'>";
  html += "WiFi名稱(SSID)：<input type='text' name='ssid' required><br>";
  // html += "密碼：<input type='password' name='password'><br>";
  html += "密碼：<input type='text' name='password'><br>";
  html += "<input type='submit' value='新增WiFi熱點'>";
  html += "</form>";
  html += "<a href='/'>返回主頁面</a>";
  html += "</body></html>";

  server.send(200, "text/html", html);
}

void handleScan() {
  Serial.println("2_開始背景 Wi-Fi 掃描...");
  WiFi.scanNetworks(true);  // 非阻塞掃描 !!!@@@
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleAddHTTP() {
  if (server.method() == HTTP_POST) {
    String ssid = server.arg("ssid");
    String password = server.arg("password");
    if (ssid.length() > 0 && password.length() <= 63) {
      add_profile(ssid.c_str(), password.c_str());
      server.sendHeader("Location", "/", true);
      server.send(302, "text/plain", "");
      // connectToWiFi();
      // attemptWiFiConnect();
      WiFi_reconnect();
    } else {
      // 可以在這裡回傳錯誤訊息到網頁
      server.send(200, "text/html", "新增失敗，SSID 或密碼錯誤。");
    }
  } else {
    server.sendHeader("Location", "/", true);
    server.send(302, "text/plain", "");
  }
}

void handleDeleteHTTP() {
  bool need_reconnect = false;
  char logBuffer[128];
  if (server.hasArg("idx")) {
    uint8_t idx = server.arg("idx").toInt();
    if (WiFi.SSID() == wifiNetworks[idx].ssid) {
      snprintf(logBuffer, sizeof(logBuffer), "handleDeleteHTTP: 移除連線中之SSID %s,%s\n", WiFi.SSID().c_str(), wifiNetworks[idx].ssid);
      need_reconnect = true;
    } else {
      // Serial.printf("handleDeleteHTTP: %s,%s\n", WiFi.SSID().c_str(), wifiNetworks[idx].ssid);
    }
    deleteNetwork(idx);
  }
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
  if (need_reconnect) {
    Serial.print(logBuffer);  // 到這裡再印
    WiFi_reconnect();
  }
}

void handleMoveUpHTTP() {
  if (server.hasArg("idx")) {
    uint8_t idx = server.arg("idx").toInt();
    if (idx > 0) {
      moveNetwork(idx, idx - 1);
    }
  }
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleMoveDownHTTP() {
  if (server.hasArg("idx")) {
    uint8_t idx = server.arg("idx").toInt();
    uint8_t totalUserNetworks = 0;
    for (int j = 0; j < networkCount; j++)
      if (wifiNetworks[j].isUserAdded) totalUserNetworks++;
    if (idx < totalUserNetworks - 1) {
      moveNetwork(idx, idx + 1);
    }
  }
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

// 儲存的 Wi-Fi 設定 (假設您已經從 Preferences 加載)
struct StoredNetwork {
  String ssid;
  String password;
  int priority;  // 連線優先級
};

std::vector<StoredNetwork> storedNetworks;

const char* getEncryptionType(wifi_auth_mode_t type) {
  switch (type) {
    case WIFI_AUTH_OPEN: return "Open";
    case WIFI_AUTH_WEP: return "WEP";
    case WIFI_AUTH_WPA_PSK: return "WPA";
    case WIFI_AUTH_WPA2_PSK: return "WPA2";
    case WIFI_AUTH_WPA_WPA2_PSK: return "WPA/WPA2";
    case WIFI_AUTH_WPA2_ENTERPRISE: return "WPA2 Enterprise";
    default: return "Unknown";
  }
}

void scanWiFiInBackground() {
  // Serial.printf("\nscanWiFiInBackground:%d\n", WiFi.getMode());
  // 確保WiFi處於正確模式WiFi.disconnect
  if (WiFi.getMode() == WIFI_OFF) {
    Serial.printf(" 0_強制 AP 切換到 %i 模式!\n", AP_mode);
    change_AP_mode();
  }

  // 檢查是否該啟動新掃描
  // Serial.print("\nS");
  if (!isScanning && (millis() - lastScanTime) >= SCAN_INTERVAL) {
    Serial.println("\n啟動背景 Wi-Fi 掃描...");

    // 嘗試多次掃描
    for (int retry = 0; retry < 3; retry++) {
      // esp_task_wdt_reset();                                         // 喂狗
      if (millis() - lastScanTimeRun <= SCAN_MIN_INTERVAL) {
        int delay = (SCAN_MIN_INTERVAL - (millis() - lastScanTimeRun));
        Serial.printf("設定延後 %dms WiFi 掃描!!\n", delay);
        lastScanTime = millis() - SCAN_INTERVAL + delay;  // !!!@@@
        return;
      }
      // int scanResult = WiFi.scanNetworks(true, false, false, 300);  // 增加掃描時間
      int scanResult = WiFi.scanNetworks(true, false, false, 100);  // 增加掃描時間 !!!@@@
      if (scanResult == WIFI_SCAN_RUNNING) {
        // Serial.println("1_開始背景 Wi-Fi 掃描...");

        isScanning = true;
        scanStartTime = millis();
        Serial.printf("掃描啟動成功 (嘗試 %d)\n", retry + 1);
        lastScanTime = millis();
        lastScanTimeRun = lastScanTime;
        break;
      } else {
        Serial.printf("掃描啟動失敗，錯誤碼: %d (嘗試 %d)\n", scanResult, retry + 1);
        // 失敗處理
        if (retry < 2) {
          WiFi.scanDelete();  // 清理可能殘留的掃描
          // esp_task_wdt_reset();       // 喂狗
          delay(500 * (retry + 1));  // 指數退避
          // esp_task_wdt_reset();       // 喂狗

          // 重置WiFi驅動
          if (retry == 1) {
            // Serial.println("強制切換到 AP+STA 模式");
            // Serial.printf(" 1_強制 AP 切換到 %i 模式!\n", AP_mode);
            // WiFi.disconnect(true);
            // delay(500);
            // WiFi.mode(WIFI_OFF);
            // delay(500);
            // // WiFi.mode(AP_mode);
            // change_AP_mode();
            delay(500);
          }
        } else {
          isScanning = false;
        }
      }
    }
  }
  // Serial.println("s");

  // // 處理進行中的掃描
  // if (isScanning) {
  //   int scanStatus = WiFi.scanComplete();

  //   // 處理掃描結果...
  //   // (保持您原有的結果處理邏輯)
  // }

  // 處理進行中的掃描
  if (isScanning) {
    int scanStatus = WiFi.scanComplete();

    // 掃描仍在進行中
    if (scanStatus == WIFI_SCAN_RUNNING) {
      // Serial.print("掃描仍在進行中... ");
      // Serial.print("s");
      // 檢查是否超時（例如超過 10 秒）
      if (millis() - scanStartTime > 10000) {
        Serial.println("掃描超時，取消本次掃描");
        WiFi.scanDelete();
        isScanning = false;
      }
      return;
    }

    // 掃描完成（成功或失敗）
    // isScanning = false;

    if (scanStatus < 0) {
      Serial.printf("掃描失敗，錯誤碼: %d\n", scanStatus);
      isScanning = false;
      return;
    }

    // 成功掃描到網路
    Serial.printf("\n掃描完成，找到 %d 個網路\n", scanStatus);
    scannedNetworks.clear();

    for (int i = 0; i < scanStatus; ++i) {
      ScannedNetwork network;
      network.ssid = WiFi.SSID(i);
      network.bssid = WiFi.BSSIDstr(i);
      network.rssi = WiFi.RSSI(i);
      network.channel = WiFi.channel(i);
      network.encryption = getEncryptionType(WiFi.encryptionType(i));

      Serial.printf("%2d | %-16s | %s | %4d | %4d | %s      ",
                    i + 1,
                    network.ssid.c_str(),
                    network.bssid.c_str(),
                    network.rssi,
                    network.channel,
                    // getEncryptionType(WiFi.encryptionType(i)));
                    network.encryption);

      // 檢查是否為重複 SSID 或 RSSI 太弱
      bool isDuplicate = false;
      bool isWeakSignal = (network.rssi < MIN_SAVE_RSSI);
      bool isSSIDEmpty = network.ssid.isEmpty();

      for (const auto& existing : scannedNetworks) {
        if (existing.ssid == network.ssid) {
          isDuplicate = true;
          break;
        }
      }

      if (!isDuplicate && !isWeakSignal && !isSSIDEmpty) {
        scannedNetworks.push_back(network);
        Serial.print(" ***已儲存*** ");
      } else {
        if (isDuplicate) Serial.print(" 重複 ");
        if (isWeakSignal) Serial.print(" 訊號弱 ");
        if (isSSIDEmpty) Serial.print(" 無SSID ");
      }
      Serial.println();
    }
    // 釋放掃描結果緩存
    WiFi.scanDelete();
    // delay(1000);  // !!!@@@ 看看是否需要
    Serial.printf("當前已儲存的有效網路數量: %d\n", scannedNetworks.size());
    isScanning = false;
  }
}

bool isAcceptableSignal(const String& ssid) {
  // Serial.printf("isAcceptableSignal: %s\n", ssid);
  // Serial.printf("當前已儲存的有效網路數量: %d\n", scannedNetworks.size());
  if (scannedNetworks.size() == 0)
    return true;
  for (const auto& network : scannedNetworks) {
    if (network.ssid == ssid) {
      if (network.rssi >= MIN_ACCEPTABLE_RSSI) {
        return true;
      } else {
        Serial.printf("%s 訊號強度不足.(%d dBm)\n", ssid.c_str(), network.rssi);
        return false;
      }
    }
  }
  Serial.printf("%s 無訊號.\n", ssid.c_str());
  return false;
}


int8_t getRSSI(const String& ssid) {
  for (const auto& network : scannedNetworks) {
    // if (network.first == ssid) {
    //   return network.second;
    // }
    if (network.ssid == ssid) {
      return network.rssi;
    }
  }
  return -127;  // 代表未找到
}


//=============================


// 設定 LED 引腳（ESP32 內建 LED 通常是 GPIO2）
#define LED_PIN 2
bool scanSet = false;

void attemptWiFiConnect() {
// #define STATUS_INTERVAL 500  // 狀態顯示間隔(0.5秒)
  // const uint8_t MAX_ATTEMPTS = 3;  // 最大嘗試次數
  const uint8_t MAX_ATTEMPTS = 1;  // 1, 最大嘗試次數. 其它數值有問題
  static unsigned long lastStatusTime = 0;
  if (WiFi.status() != WL_CONNECTED && millis() - lastConnectAttempt >= CONNECT_RETRY_DELAY) {
    updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
    if (isScanning) {  // 網路掃描中!
      if (millis() - lastStatusTime >= STATUS_INTERVAL) {
        lastStatusTime = millis();
        Serial.print(" sc");  // 連線 等待掃描
      }
      return;
    }
    scanSet = false;
    bool ledState = false;
    Serial.printf("\n連線 Wi-Fi...\n");

    for (uint8_t attemptCount = 1; attemptCount <= MAX_ATTEMPTS; attemptCount++) {
      Serial.printf("[嘗試 %d/%d] 連線 Wi-Fi...\n", attemptCount, MAX_ATTEMPTS);
      // 遍歷已儲存的網路
      for (uint8_t i = 0; i < networkCount; i++) {
        if (!wifiNetworks[i].enabled) continue;

        String currentSSID = String(wifiNetworks[i].ssid);
        if (isAcceptableSignal(currentSSID)) {
          if (isScanning) {
            Serial.printf("測試網路(無WiFi掃描資料) #%d: %s\n", i + 1, currentSSID.c_str());
          } else {
            int8_t rssi = getRSSI(currentSSID);
            Serial.printf("測試網路 #%d: %s (%d dBm)\n", i + 1, currentSSID.c_str(), rssi);
          }
          // updateSystemState(STATE_WIFI_CONNECTING);
          updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
          Serial.printf("WiFi.begin: %s\n", wifiNetworks[i].ssid);
          WiFi.begin(wifiNetworks[i].ssid, wifiNetworks[i].password);
          password = wifiNetworks[i].password;
          unsigned long startAttempt = millis();
          unsigned long lastBlink = 0;
          const unsigned long blinkInterval = 500;

          while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < WIFI_TIMEOUT) {
            unsigned long now = millis();
            // 非阻塞
            if (now - lastBlink >= blinkInterval) {
              lastBlink = now;
              Serial.print(".");
            }
            // 處理 WebServer 請求（讓它不中斷）
            server.handleClient();
            GetSendCallerNumber(now);
          }

          if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("\n\n========================================\n");
            Serial.printf("(%s,%s,%s,%s)連線成功！\n", Caller_Number, wifiNetworks[i].ssid, WiFi.localIP().toString().c_str(), password);
            Serial.printf("========================================\n\n");
            digitalWrite(LED_PIN, HIGH);  // 常亮
            lastConnectAttempt = millis();
            return;
          } else {
            digitalWrite(LED_PIN, LOW);
            Serial.println("\n連線失敗");
            WiFi.disconnect(true);  // 清除之前的連接
            // delay(1000);  // OK:1000,       !!!@@@
            // lastScanTime = millis() - SCAN_INTERVAL;
            // Serial.println("設定 WiFi 掃描!!");
          }
        }
      }
      // delay(1000);
      if (WiFi.status() == WL_CONNECTED) {
        // Serial.println("\n連線成功！");
        // digitalWrite(LED_PIN, HIGH);  // 常亮
        // lastConnectAttempt = millis();
        // return;
      } else {
        digitalWrite(LED_PIN, LOW);
        Serial.println("\n全部連線失敗!!!");
        delay(1000);  // OK:1000,       !!!@@@
        Serial.println("全部連線失敗,設定 WiFi 立即掃描!!");
        lastScanTime = millis() - SCAN_INTERVAL;
        lastScanTimeRun = lastScanTime - SCAN_MIN_INTERVAL;
        return;
      }
    }
    lastConnectAttempt = millis();

    Serial.println("attemptWiFiConnect,設定 10 秒後 WiFi 掃描!!");
    lastScanTime = millis() - SCAN_INTERVAL + 10000;
    lastScanTimeRun = lastScanTime - SCAN_MIN_INTERVAL;
  }
}

const char* getWiFiStatusString(wl_status_t status) {
  switch (status) {
    case WL_NO_SHIELD: return "WL_NO_SHIELD";
    case WL_IDLE_STATUS: return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL: return "WL_NO_SSID_AVAIL";
    case WL_SCAN_COMPLETED: return "WL_SCAN_COMPLETED";
    case WL_CONNECTED: return "WL_CONNECTED";
    case WL_CONNECT_FAILED: return "WL_CONNECT_FAILED";
    case WL_CONNECTION_LOST: return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED: return "WL_DISCONNECTED";
    default: return "UNKNOWN_STATUS";
  }
}

void monitorWiFiStatus() {
  static wl_status_t lastStatus = WL_IDLE_STATUS;
  wl_status_t currentStatus = WiFi.status();

  if (currentStatus != lastStatus) {
    lastStatus = currentStatus;
    Serial.printf("WiFi 狀態變更: %s\n", getWiFiStatusString(currentStatus));
    if (currentStatus == WL_CONNECTION_LOST || currentStatus == WL_DISCONNECTED) {
      // Serial.println("WiFi 連接中斷，準備重新連接...");
      Serial.println("WiFi 連接中斷!");
      // lastDisconnectTime = millis();
    }
  }
}

// 數字讀取發送函數
void GetSendCallerNumber(unsigned long currentMillis) {
  if (currentMillis - lastCheckNumber < CHECK_NUMBER_INTERVAL)
    return;
  bool get_num = UR2Recv();
  // if (nowStr != sendStr) {  // 資料有變動,沒連線一樣傳送至buffer
  if (get_num) {  // 有新資料,沒連線一樣傳送至buffer
    // Serial.printf("GetSendCallerNumber nowStr:'%s', sendStr:'%s'\n", nowStr, sendStr);
    client_send(nowStr);
    // Serial.printf("GetSendCallerNumber set sendStr: '%s' -> '%s'\n", sendStr, nowStr);
    lastSendStr = sendStr;
    sendStr = nowStr;
    nowStrDemo = nowStr;
    onMessage_time = currentMillis;  // 重置 onMessage 計時器
    process_change_AP_mode(sendStr.toInt());
  }
}

void setupOTA() {
  // ArduinoOTA.setHostname("esp32-ota");
  ArduinoOTA.setHostname(savedData1.c_str());
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {  // U_SPIFFS
      type = "filesystem";
    }
    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });
  ArduinoOTA.begin();
}


/*
// LED 控制結構
struct LedState {
  bool isOn;                 // LED 當前狀態
  bool isBlinking;           // 是否閃爍
  unsigned long onTime;      // 亮持續時間（毫秒）
  unsigned long offTime;     // 滅持續時間（毫秒）
  unsigned long lastToggle;  // 最後切換時間
};
*/
// 初始化 LED 設定
void initLedConfigs() {
  // STATE_INIT, 0
  ledConfigs[STATE_INIT].red = { true, false, 0, 0, 0 };     // 紅燈持續亮
  ledConfigs[STATE_INIT].green = { false, false, 0, 0, 0 };  // 綠燈持續滅

  // STATE_WIFI_CONNECTING, 1
  ledConfigs[STATE_WIFI_CONNECTING].red = { false, true, 100, 100, 0 };  // 紅燈快速閃爍
  ledConfigs[STATE_WIFI_CONNECTING].green = { false, false, 0, 0, 0 };   // 綠燈持續滅

  // STATE_WIFI_CONNECTED, 2
  ledConfigs[STATE_WIFI_CONNECTED].red = { true, false, 0, 0, 0 };     // 紅燈持續亮
  ledConfigs[STATE_WIFI_CONNECTED].green = { false, false, 0, 0, 0 };  // 綠燈持續滅

  // STATE_WEBSOCKET_CONNECTING, 3, 交互閃爍
  ledConfigs[STATE_WEBSOCKET_CONNECTING].red = { true, true, 750, 750, 0 };     // 紅燈慢速閃爍
  ledConfigs[STATE_WEBSOCKET_CONNECTING].green = { false, true, 750, 750, 0 };  // 綠燈慢速閃爍

  // STATE_WEBSOCKET_CONNECTED, 4                 亮    閃
  ledConfigs[STATE_WEBSOCKET_CONNECTED].red = { false, false, 0, 0, 0 };   // 紅燈持續滅
  ledConfigs[STATE_WEBSOCKET_CONNECTED].green = { true, false, 0, 0, 0 };  // 綠燈持續亮

  // STATE_ERROR, 5
  ledConfigs[STATE_ERROR].red = { false, false, 0, 0, 0 };    // 紅燈滅
  ledConfigs[STATE_ERROR].green = { false, false, 0, 0, 0 };  // 綠燈滅

  // STATE_DEMO, 6
  ledConfigs[STATE_DEMO].red = { false, false, 0, 0, 0 };       // 紅燈持續滅
  ledConfigs[STATE_DEMO].green = { true, true, 1900, 100, 0 };  // 綠燈慢速閃爍

  // STATE_TRANS, 7                 亮    閃   亮     暗
  ledConfigs[STATE_TRANS].red = { true, true, 100, 10000, 0 };  // 紅燈快速亮一下
  ledConfigs[STATE_TRANS].green = { true, false, 0, 0, 0 };     // 綠燈持續亮

  // STATE_AP_STA,8 , 交互閃爍
  ledConfigs[STATE_AP_STA].red = { true, true, 100, 400, 0 };     // 紅燈快速閃爍
  ledConfigs[STATE_AP_STA].green = { false, true, 500, 500, 0 };  // 綠燈慢速閃爍

  // STATE_AP_STA_C,9 ,
  ledConfigs[STATE_AP_STA_C].red = { false, false, 0, 0, 0 };      // 紅燈持續滅
  ledConfigs[STATE_AP_STA_C].green = { true, true, 500, 500, 0 };  // 綠燈慢速閃爍

  // STATE_NUMBER_ERROR,10
  ledConfigs[STATE_NUMBER_ERROR].red = { true, false, 0, 0, 0 };     // 紅燈持續亮
  ledConfigs[STATE_NUMBER_ERROR].green = { false, false, 0, 0, 0 };  // 綠燈持續滅
}

// LED 先亮後滅 !!!@@@
void blinkLED_on(TimerHandle_t timer) {
  LedState* ledState = (LedState*)pvTimerGetTimerID(timer);
  if (ledState->isBlinking) {
    ledState->isOn = false;
    ledState->lastToggle = currentMillis - ledState->offTime;
  }
  blinkLED(timer);
}

// 更新 LED 狀態
void updateLEDState() {
  LedState* redState = &ledConfigs[status.state].red;
  LedState* greenState = &ledConfigs[status.state].green;

  // 更新紅燈計時器 ID
  vTimerSetTimerID(redTimer, redState);
  // 更新綠燈計時器 ID
  vTimerSetTimerID(greenTimer, greenState);

  // 立即觸發一次計時器回調，以應用新的 LED 狀態
  currentMillis = millis();
  // blinkLED(redTimer);
  // blinkLED(greenTimer);
  blinkLED_on(redTimer);
  blinkLED_on(greenTimer);
}

// 更新系統狀態
void updateSystemState(SystemState newState, const String& error) {
  static SystemState previousState = STATE_INIT;
  static SystemState previousDisState = STATE_INIT;

  if (newState == STATE_AP_STA) {
    if (WiFi.status() == WL_CONNECTED) {
      newState = STATE_AP_STA_C;
      // Serial.println("連線中!");
    } else {
      // Serial.println("未連線!");
    }
  }

  if (newState == previousDisState)  // 狀態未變
    return;
  previousDisState = newState;

  // 列印狀態
  Serial.printf(" _S%d ", newState);
  if (error.length() > 0) {
    status.lastError = error;
    // Serial.println("\nError: " + error);
    Serial.println(error);
  }
  if (newState == STATE_ERROR) {
    // Serial.printf(" Pass! ");
    return;
  }

  if (newState != STATE_AP_STA && newState != STATE_AP_STA_C && newState != STATE_DEMO) {  // STATE_AP_STA ' STATE_AP_STA_C ' STATE_DEMO 不儲存
    if (newState == STATE_RESTORE) {
      newState = previousState;
      Serial.printf(" __S%d ", newState);
    } else {
      previousState = newState;
    }
  }
  status.lastStateChange = currentMillis;
  // 更新 LED 狀態
  status.state = newState;
  updateLEDState();
}

// LED 閃動函數
// LED_RED:33, LED_GREEN:32
// LOW LED亮
void blinkLED(TimerHandle_t xTimer) {
  unsigned long currentMillis = millis();
  LedState* ledState = (LedState*)pvTimerGetTimerID(xTimer);

  int selectedLED = (ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN);
  if (ledState->isBlinking) {
    if (ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->onTime)) {
      ledState->isOn = false;
      ledState->lastToggle = currentMillis;
      digitalWrite(selectedLED, HIGH);  // LED滅
      if (selectedLED == LED_RED)       //
        digitalWrite(LED_BLUE, HIGH);   // LED亮
      // Serial.printf("LED(%d)滅! ", selectedLED);
    } else if (!ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->offTime)) {
      ledState->isOn = true;
      ledState->lastToggle = currentMillis;
      digitalWrite(selectedLED, LOW);  // LED亮
      if (selectedLED == LED_RED)      //
        digitalWrite(LED_BLUE, LOW);   // LED滅
      // Serial.printf("LED(%d)亮! ", selectedLED);
    }
  } else {  // 不閃爍時用
    int status = (ledState->isOn ? LOW : HIGH);
    digitalWrite(selectedLED, status);
    if (selectedLED == LED_RED)        //
      digitalWrite(LED_BLUE, status);  // LED滅
    // Serial.printf("LED(%d)切換%d! ", selectedLED, status);
  }
}

void onMessageCallback(const String& message) {  // cmb-caller-frontend 傳入資料
  onMessage_time = 0;
  // 快速處理 Ping
  if (message == "pong") {
    Serial.print("B");
    return;
  }
  // 狀態更新
  updateSystemState(demoState ? STATE_DEMO : STATE_WEBSOCKET_CONNECTED);
  updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WEBSOCKET_CONNECTED);
  Serial.println("接收: " + message);
  // 快速回應確認
  if (message.startsWith("OK,")) {
    waitingResponse = false;
    // return;    // 必續繼續往下執行
  }
  // 解析資料
  parseUpdateMessage(message);
}

// void executeWifiCommand(uint8_t* payload);
void executeWifiCommand(const String& payload);

void parseUpdateMessage(const String& msg) {  // 雲端接收
  // 先嘗試解析為 JSON 格式
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, msg);

  if (!error) {
    // 如果是有效的 JSON，檢查是否有 "action" 欄位
    if (doc.containsKey("action")) {
      String action = doc["action"].as<String>();
      if (action.startsWith("wifi_")) {
        // 執行處理 wifi_ 開頭指令的函數
        executeWifiCommand(msg);
        return;
      }
    }
  }

  String parts[4];
  int count = 0;
  int start = 0;
  while (count < 4 && start < msg.length()) {
    int end = msg.indexOf(',', start);
    if (end == -1) end = msg.length();
    parts[count++] = msg.substring(start, end);
    start = end + 1;
  }
  // if (count == 4 && parts[3] == "update" && parts[2] != sendStr) {
  //   Serial.printf("更新值:%s, old sendStr:%s \n", parts[2], sendStr);
  //   // 改只需顯示 !!!@@@
  //   // send_and_dis(parts[2]);
  //   num_LED_dis(parts[2]);
  // }
  if (count == 4 && (parts[3] == "update" || parts[3] == "get")) {
    Serial.printf("Websocket 已連線時間:%lu\n", millis() - websocket_connect_time);
    bypassLast = false;
    if (((millis() - websocket_connect_time) >= 1000) || (parts[2] != sendStr && parts[2] != lastSendStr)) {  // 新輸入 OR 有變動
      if ((millis() - websocket_connect_time) < 1000) {                                                       // Web 改動 Server 上叫號資料
        bypassLast = true;
        Serial.printf("bypassLast = true\n");
      }
      Serial.printf("%s   資料變動:%s, old sendStr:%s,%s \n", parts[3], parts[2], lastSendStr, sendStr);  //
      num_LED_dis(parts[2]);
    } else {
      Serial.printf("%s 資料未變動:%s, old sendStr:%s,%s \n", parts[3], parts[2], lastSendStr, sendStr);  //
      // delay(500);                                                                                         // 大於 0.4秒 ， 以防止 Server 回傳.   ~~~~~~~~~
    }
  }
}


bool webSocketClient_sendTXT(String& message) {
  Serial.print("[WebSocket 發送] ");
  Serial.println(message);
  webSocketClient.sendTXT(message);
  return true;
}

// ====== 處理 WebSocket 事件 ======
// void webSocketEvent_XXXX(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
// void executeWifiCommand(uint8_t* payload) {
void executeWifiCommand(const String& payload) {
  // Serial.printf("get Text: %s\n", payload);

  // Serial.print("收到原始 payload: ");
  // Serial.println(payload);  // 先印出原始訊息確認

  // 檢查 payload 是否為空
  if (payload.length() == 0) {
    Serial.println("錯誤: payload 為空");
    String response = generateErrorResponse("", "", "", "002", "empty payload");
    webSocketClient_sendTXT(response);
    return;
  }

  // 增加清除空白字元（如果需要）
  String trimmedPayload = payload;
  trimmedPayload.trim();


  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.print("JSON 解析失敗: ");
    Serial.println(error.c_str());
    String response = generateErrorResponse(doc["action"] | "", doc["caller_id"] | "", doc["uuid"] | "", "001", "format error");
    webSocketClient_sendTXT(response);
    return;
  }

  String action = doc["action"] | "";
  String callerId = doc["caller_id"] | "";
  String uuid = doc["uuid"] | "";

  // Serial.printf("doc:'%s'\n", doc);

  // 正確輸出 JSON 內容的方式
  // Serial.println("解析成功的 JSON 內容:");
  // serializeJson(doc, Serial);  // 使用 serializeJson 輸出整個 JSON
  // Serial.println();            // 換行

  // 或者輸出格式化後的內容
  // Serial.printf("action: %s, caller_id: %s, uuid: %s\n",
  //               action.c_str(), callerId.c_str(), uuid.c_str());

  // Serial.printf("0_action = %s\n", action.c_str());
  if (action == "wifi_get_status") {
    Serial.printf("1_action = %s\n", action.c_str());
    String response = getWiFiStatusJSON(callerId, uuid);
    webSocketClient_sendTXT(response);
    Serial.println("wifi_get_status 設定 WiFi 掃描!!");
    lastScanTime = millis() - SCAN_INTERVAL;
  } else if (action == "wifi_scan_list") {
    Serial.printf("2_action = %s\n", action.c_str());
    String response = scanWiFiListJSON(callerId, uuid);
    webSocketClient_sendTXT(response);
  } else if (action == "wifi_get_profiles") {
    Serial.printf("3_action = %s\n", action.c_str());
    String response = getWiFiProfilesJSON(callerId, uuid);
    webSocketClient_sendTXT(response);
  } else if (action == "wifi_add_profile") {
    Serial.printf("4_action = %s\n", action.c_str());
    if (doc.containsKey("data") && doc["data"].is<JsonObject>()) {
      JsonObject data = doc["data"].as<JsonObject>();
      if (data.containsKey("ssid") && data["ssid"].is<String>() && data.containsKey("password") && data["password"].is<String>()) {
        String ssid = data["ssid"].as<String>();
        String password = data["password"].as<String>();
        if (ssid.length() == 0 || ssid.length() > 31) {
          String response = generateErrorResponse(action, callerId, uuid, "005", "invalid ssid");
          webSocketClient_sendTXT(response);
        } else if (password.length() > 63) {
          String response = generateErrorResponse(action, callerId, uuid, "006", "invalid password");
          webSocketClient_sendTXT(response);
        } else {
          add_profile(ssid.c_str(), password.c_str());
          String response = generateSuccessResponse(action, callerId, uuid);
          // Serial.printf("action: %s, %s\n", action.c_str(), response.c_str());
          webSocketClient_sendTXT(response);
          WiFi_reconnect();
        }
      } else {
        String response = generateErrorResponse(action, callerId, uuid, "001", "format error");
        webSocketClient_sendTXT(response);
      }
    } else {
      String response = generateErrorResponse(action, callerId, uuid, "001", "format error");
      webSocketClient_sendTXT(response);
    }
  } else if (action == "wifi_delete_profile") {
    Serial.printf("5_action = %s\n", action.c_str());
    if (doc.containsKey("data") && doc["data"].is<JsonObject>() && doc["data"].as<JsonObject>().containsKey("ssid") && doc["data"].as<JsonObject>()["ssid"].is<String>()) {
      String ssidToDelete = doc["data"]["ssid"].as<String>();
      bool found = false;
      uint8_t userNetworkIndexToDelete = 0;
      uint8_t currentUserNetworkIndex = 0;
      for (uint8_t i = 0; i < networkCount; i++) {
        if (wifiNetworks[i].isUserAdded) {
          if (strcmp(wifiNetworks[i].ssid, ssidToDelete.c_str()) == 0) {
            // String response = generateSuccessResponse(action, callerId, uuid);
            // webSocketClient_sendTXT(response);  // 先傳 !!!@@@
            deleteNetwork(currentUserNetworkIndex);
            found = true;
            break;
          }
          currentUserNetworkIndex++;
        }
      }

      if (found) {
        String response = generateSuccessResponse(action, callerId, uuid);
        webSocketClient_sendTXT(response);
        if (WiFi.SSID() == ssidToDelete.c_str()) {
          Serial.printf("delete: 移除連線中之SSID %s,%s\n", WiFi.SSID().c_str(), ssidToDelete.c_str());
          WiFi_reconnect();
        } else {
          // Serial.printf("delete: %s,%s\n", WiFi.SSID().c_str(), ssidToDelete.c_str());
        }
      } else {
        String response = generateErrorResponse(action, callerId, uuid, "008", "credential not found");
        webSocketClient_sendTXT(response);
      }

    } else {
      String response = generateErrorResponse(action, callerId, uuid, "001", "format error");
      webSocketClient_sendTXT(response);
    }
  } else {
    String response = generateErrorResponse(action, callerId, uuid, "003", "not support");
    webSocketClient_sendTXT(response);
  }
}

void add_profile(const char* ssid, const char* password) {
  addNetwork(ssid, password);
  saveNetworks();
}

void WiFi_reconnect() {
  delay(500);
  Serial.println("斷開 WebSocket 連接!");
  webSocketClient.disconnect();
  delay(500);
  Serial.println("斷開 WiFi 連接!");
  WiFi.disconnect(false, false);  // 只斷開 Station 連接，不影響 SoftAP
}

// 記憶體檢查函數
void checkMemory() {
  uint32_t freeHeap = ESP.getFreeHeap();
  Serial.printf("Free Heap: %u bytes\n", freeHeap);
  if (freeHeap < MINIMUM_HEAP) {
    updateSystemState(STATE_ERROR, "Low memory warning");
  }
}

// WebSocket 初始化
void setupWebSocket() {
  Serial.println("setupWebSocket()!");
  updateSystemState(STATE_WEBSOCKET_CONNECTING, "開始嘗試連接 WebSocket 伺服器...");

  for (int i = 0; i < SERVER_COUNT; i++) {
    const char* host = servers[i].host;
    uint16_t port = servers[i].port;
    bool useSSL = servers[i].useSSL;

    Serial.printf("嘗試連接伺服器 %d: %s:%d (SSL: %s)\n", i + 1, host, port, useSSL ? "是" : "否");

    if (useSSL) {
      webSocketClient.beginSSL(host, port, "/");  // 開始 SSL 連接
    } else {
      webSocketClient.begin(host, port, "/");  // 開始非 SSL 連接
    }

    webSocketClient.onEvent(webSocketEvent);

    // 啟用自動重連（每x.xx秒嘗試一次）
    webSocketClient.setReconnectInterval(1);  // !!!@@@, 1ms : 0.7 ' 0.72 ' 0.748 ' 0.719 ' 0.716 ' 0.698 ' 0.666 Sec
    // webSocketClient.enableReconnect(true);   // Error

    // 等待連接成功或超時
    unsigned long startTime = millis();
    while (millis() - startTime < 10000) {  // 10 秒超時
      if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\nWiFi 已斷線！跳出 setupWebSocket!!!");
        return;
      }
      webSocketClient.loop();
      if (webSocketClient.isConnected()) {
        Serial.printf("[狀態] 連接成功！(%s:%d/)\n", host, port);
        updateSystemState(STATE_WEBSOCKET_CONNECTED, "WebSocket 已連接！");
        return;  // 連接成功，退出函數
      }
      vTaskDelay(pdMS_TO_TICKS(100));  // n + 1000, OK:100,200    Fail: 1000,500,300
    }

    Serial.println("[狀態] 連接失敗,斷開當前連接,嘗試下一個伺服器...");
    webSocketClient.disconnect();  // 斷開當前連接
    updateSystemState(STATE_WEBSOCKET_CONNECTING, "連接失敗，嘗試下一個伺服器...");
  }
  Serial.println("[錯誤] 所有伺服器連接失敗！");
  // updateSystemState(STATE_WIFI_CONNECTED, "所有伺服器連接失敗！");
  updateSystemState(STATE_WEBSOCKET_CONNECTING, "所有伺服器連接失敗！");
}

// bool isWebSocketConnected = false;
unsigned long disconnected_time = millis();
// WebSocket 事件處理
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      // isWebSocketConnected = false;
      disconnected_time = millis();
      Serial.printf("\nWebSocket Disconnected! (WStype_DISCONNECTED) (%lu Sec)\n", (millis() - websocket_connect_time) / 1000);
      updateSystemState(STATE_ERROR, "STATE_ERROR WebSocket Disconnected!");
      // vTaskDelay(pdMS_TO_TICKS(500));  // !!!@@@
      // Serial.printf("\nWebsocket 斷線會自動重連!\n");
      // Serial.println("\n0_Websocket 斷線設定重新連線!!!");   // 較慢 ~= 2.36 Sec
      // WebSocket_init = false;
      break;
    case WStype_CONNECTED:
      // isWebSocketConnected = true;
      Serial.printf("\nWebSocket Connected!(%lu ms)\n", millis() - disconnected_time);
      websocket_connect_time = millis();
      new_connect = true;
      updateSystemState(STATE_WEBSOCKET_CONNECTED);
      break;
    case WStype_TEXT:
      // Serial.printf("Received: %s\n", (char*)payload);
      onMessageCallback(String((char*)payload));
      break;
    case WStype_PING:
      // pong will be send automatically
      // Serial.print("Ping Received");
      Serial.print("I");
      Serial.print("o");  // Pass
      // webSocketClient.sendPong();
      // webSocketClient.sendPing();  // 發送 PING 訊息
      break;
    case WStype_PONG:
      // Serial.print("Pong Received");
      Serial.print("O");
      ping_EX_no_reply_count = 0;
      break;
  }
}

void Ping_EX() {
  if (webSocketClient.sendPing()) {
    Serial.print("i");
    sendPing_fail = 0;
    ping_EX_no_reply_count += 1;
    if (ping_EX_no_reply_count >= 3) {
      Serial.printf("\n已超過%d次未回覆 Pong_EX!,  reconnecting...\n", ping_EX_no_reply_count - 1);
      ping_EX_no_reply_count = 0;
      Serial.println("1_斷開 WebSocket 連接");
      webSocketClient.disconnect();
      delay(500);
      setupWebSocket();
      return;
    }
  } else {
    sendPing_fail += 1;
    if (sendPing_fail >= 3) {
      sendPing_fail = 0;
      // Serial.println("Ping failed!!!");
      Serial.printf("\n已超過%d次 sendPing 失敗!, reconnecting...\n", sendPing_fail);
      // Serial.println("Ping failed, reconnecting...");
      Serial.println("2_斷開 WebSocket 連接");
      webSocketClient.disconnect();
      setupWebSocket();
    }
  }
  String message = "";
  if (!demoState)
    message = String(Caller_Number) + "," + "ping" + "," + sendStr;
  else
    message = String(Caller_Number) + "," + "ping" + "," + nowStrDemo;
  if (webSocketClient.isConnected()) {
    check_auth();
    webSocketClient_sendTXT(message);  // PING
    Serial.print("E");
    lastPING = currentMillis;
    onMessage_time = lastPING;  // 重置 onMessage 計時器
  }
}

// 定義任務狀態數組的最大大小
#define MAX_TASKS 20

// 全局變量，用於存儲上一次的任務運行時間
TaskStatus_t previousTaskStatus[MAX_TASKS];
UBaseType_t previousTaskCount = 0;
/*
// 列印任務狀態
void printTaskStats() {
  TaskStatus_t taskStatusArray[MAX_TASKS];
  UBaseType_t taskCount = uxTaskGetNumberOfTasks();

  if (taskCount > MAX_TASKS) {
    taskCount = MAX_TASKS;  // 防止數組溢出
  }

  // 獲取當前任務狀態
  UBaseType_t copiedTaskCount = uxTaskGetSystemState(taskStatusArray, taskCount, NULL);

  // 計算總時間增量
  static TickType_t previousTotalTime = 0;
  TickType_t totalTime = xTaskGetTickCount();
  TickType_t timeIncrement = totalTime - previousTotalTime;
  previousTotalTime = totalTime;

  // 計算每個任務的 CPU 使用百分比
  for (UBaseType_t i = 0; i < copiedTaskCount; i++) {
    const char* taskName = taskStatusArray[i].pcTaskName;
    TickType_t currentRunTime = taskStatusArray[i].ulRunTimeCounter;

    // 查找上一次的運行時間
    TickType_t previousRunTime = 0;
    for (UBaseType_t j = 0; j < previousTaskCount; j++) {
      if (strcmp(previousTaskStatus[j].pcTaskName, taskName) == 0) {
        previousRunTime = previousTaskStatus[j].ulRunTimeCounter;
        break;
      }
    }

    // 計算運行時間增量
    TickType_t runTimeIncrement = currentRunTime - previousRunTime;

    // 計算 CPU 使用百分比
    float cpuUsage = 0.0;
    if (timeIncrement > 0) {
      cpuUsage = (float)runTimeIncrement / (float)timeIncrement * 100.0;
    }

    // 列印任務信息
    Serial.printf("Task: %s, CPU Usage: %.2f%%\n", taskName, cpuUsage);
  }

  // 保存當前任務狀態，供下一次使用
  memcpy(previousTaskStatus, taskStatusArray, copiedTaskCount * sizeof(TaskStatus_t));
  previousTaskCount = copiedTaskCount;
}

// 獲取運行時間統計
void GetRunTimeStats() {
  char buffer[1024];  // 假設 buffer 大小為 1024
  vTaskGetRunTimeStats(buffer);
  // 將 buffer 轉換為字串
  String stats = String(buffer);
  // 使用換行符分割字串
  int start = 0;
  int end = stats.indexOf('\n');
  int count = 0;
  while (end != -1 && count < 3) {
    String line = stats.substring(start, end);
    // 找到百分比的位置
    int percentIndex = line.lastIndexOf('\t') + 1;
    String percentStr = line.substring(percentIndex);
    // 去掉百分比符號並轉換為整數
    percentStr.trim();
    percentStr.replace("%", "");
    int percent = percentStr.toInt();
    // 如果百分比大於等於 1，則列印該行並增加計數
    if (percent >= 1) {
      Serial.println(line);
      count++;
    }
    // 更新起始和結束位置
    start = end + 1;
    end = stats.indexOf('\n', start);
  }
}

// 重置運行時間統計
void resetRuntimeStats() {
  // 使用互斥鎖進入臨界區
  taskENTER_CRITICAL(&statsMutex);
  // 重置所有任務的執行時間計數器
  UBaseType_t uxArraySize = uxTaskGetNumberOfTasks();
  TaskStatus_t* pxTaskStatusArray = (TaskStatus_t*)pvPortMalloc(uxArraySize * sizeof(TaskStatus_t));
  if (pxTaskStatusArray != NULL) {
    uxTaskGetSystemState(pxTaskStatusArray, uxArraySize, NULL);
    // 遍歷所有任務並重置其執行時間
    for (UBaseType_t i = 0; i < uxArraySize; i++) {
      pxTaskStatusArray[i].ulRunTimeCounter = 0;
    }
    vPortFree(pxTaskStatusArray);
  }
  // 離開臨界區
  taskEXIT_CRITICAL(&statsMutex);
  Serial.println("🔄 運行時間統計數據已重置");
}

// 顯示任務負載
void showTaskLoad() {
  // 獲取任務數量
  UBaseType_t taskCount = uxTaskGetNumberOfTasks();
  TaskStatus_t* taskStatusArray = (TaskStatus_t*)pvPortMalloc(taskCount * sizeof(TaskStatus_t));
  uint32_t totalRunTime;

  if (taskStatusArray != NULL) {
    // 獲取系統狀態
    UBaseType_t actualCount = uxTaskGetSystemState(taskStatusArray, taskCount, &totalRunTime);

    // 計算每個任務的負載百分比
    if (totalRunTime > 0) {  // 避免除以零
      for (UBaseType_t i = 0; i < actualCount; i++) {
        uint32_t taskRunTime = taskStatusArray[i].ulRunTimeCounter;
        float percentage = (taskRunTime * 100.0) / totalRunTime;

        Serial.printf("Task: %s, Load: %.2f%%\n",
                      taskStatusArray[i].pcTaskName,
                      percentage);
      }
    }

    vPortFree(taskStatusArray);
  }
}
*/

// 檢查系統狀態
void check_system(unsigned long lastCheckTime, unsigned long currentMillis) {
  calculateCPULoad(lastCheckTime, currentMillis);
  checkMemory();
  // Serial.printf("InterruptCount:%lu, scanDisplayCount:%lu \n", InterruptCount, scanDisplayCount);
}

// 計算 CPU 負載
void calculateCPULoad(unsigned long lastCheckTime, unsigned long currentMillis) {
  float minute = ((currentMillis - lastCheckTime) / 1000.0);
  for (int i = 0; i < portNUM_PROCESSORS; i++) {
    uint32_t idleDiff = idleCount[i] - idleCountLast[i];
    if (idleDiff > int(idleRate[i] * minute)) {
      idleRate[i] = ((float)idleDiff / minute) + 1;
    }
    float load = (1.0f - (float)idleDiff / (float)(idleRate[i] * minute));
    Serial.printf("\nidleCount - idleCountLast:%lu, idleRate:%lu\n", idleCount[i] - idleCountLast[i], idleRate[i]);
    Serial.printf("Core %d Load: %.2f%%\n", i, load);
    idleCountLast[i] = idleCount[i];
  }
}

// **首頁**
void cmb_handleRoot() {
  // 檢查是否超過失效時間
  if (!Maint_mode) {
    server.send(403, "text/plain; charset=UTF-8", "功能已失效! (" + String(__func__) + ")");
    Serial.printf("功能已失效(%s)\n", __func__);
    return;
  }
  String html = "<!DOCTYPE html><html><head>"
                "<meta charset='UTF-8'>"
                "<title>ESP32 Flash 存儲</title>"
                "<style>"
                "label {display: inline-block; width: 100px; text-align: right; margin-right: 10px;}"
                "</style></head><body>"
                "<h2>ESP32 Flash 資料存儲</h2>"
                "<form action='/cmb_store' method='POST'>"
                "<div><label for='data1'>ID:</label>"
                "<input type='text' id='data1' name='data1' value='"
                + savedData1 + "'></div>"
                               "<div><label for='data2'>PASSWORD:</label>"
                               "<input type='text' id='data2' name='data2' value='"
                + savedData2 + "'></div>"
                               "<div><label for='data3'>data3:</label>"
                               "<input type='text' id='data3' name='data3' value='"
                + savedData3 + "'></div>"
                               "<div style='margin-left: 110px;'><input type='submit' value='儲存'></div></form><br>"
                               "<a href='/cmb_retrieve'>📄 讀取存儲的資料</a><br>"
                               "<a href='/cmb_status'>📊 查看裝置狀態</a>"
                               "</body></html>";
  server.send(200, "text/html; charset=UTF-8", html);
  Serial.println("cmb_handleRoot");
}

// **存儲資料**
void handleStore() {
  if (!Maint_mode) {
    server.send(403, "text/plain; charset=UTF-8", "功能已失效! (" + String(__func__) + ")");
    Serial.printf("功能已失效(%s)\n", __func__);
    return;
  }
  preferences.begin("storage", false);

  String response = "";
  if (server.hasArg("data1")) {
    String data1 = server.arg("data1");
    preferences.putString("saved_data1", data1);
    response += "資料 1 已存儲: " + data1 + "\n";
  }

  if (server.hasArg("data2")) {
    String data2 = server.arg("data2");
    preferences.putString("saved_data2", data2);
    response += "資料 2 已存儲: " + data2 + "\n";
  }

  if (server.hasArg("data3")) {
    String data3 = server.arg("data3");
    preferences.putString("saved_data3", data3);
    response += "資料 3 已存儲: " + data3 + "\n";
  }

  preferences.end();

  if (response == "") {
    server.send(400, "text/plain; charset=UTF-8", "錯誤: 缺少 data 參數");
    Serial.println("錯誤: 缺少 data 參數");
  } else {
    server.send(200, "text/plain; charset=UTF-8", response);
  }
  Serial.println("系統將在1秒後重啟...");
  delay(1000);
  ESP.restart();
}

// **讀取 Flash 中的資料**
void handleRetrieve() {
  // 檢查是否超過失效時間
  if (!Maint_mode) {
    server.send(403, "text/plain; charset=UTF-8", "功能已失效! (" + String(__func__) + ")");
    Serial.printf("功能已失效(%s)\n", __func__);
    return;
  }
  preferences.begin("storage", true);
  savedData1 = preferences.getString("saved_data1", "");
  savedData2 = preferences.getString("saved_data2", "");
  savedData3 = preferences.getString("saved_data3", "");
  preferences.end();
  String response = "      ID: " + savedData1 + "\n" + "PASSWORD: " + savedData2 + "\n" + "   data3: " + savedData3;
  // String response1 = "ID: " + savedData1;
  server.send(200, "text/plain; charset=UTF-8", response);
  // Serial.println(response1);
}

// 轉換 IP 為字串
String ipToString(IPAddress ip) {
  // return String(ip[0]) + "." + String(ip[1]) + "." + String(ip[2]) + "." + String(ip[3]);
  return ip.toString().c_str();
}

// **查看裝置狀態**
void handleStatus() {
  String ipStatus = "";

  // 建立IP狀態表格
  ipStatus = "<table border='1' style='border-collapse: collapse; width: 100%; max-width: 600px;'>"
             "<tr style='background-color: #f0f0f0;'>"
             "<th style='padding: 8px;'>IP位址</th>"
             "<th style='padding: 8px;'>狀態</th>"
             "</tr>";

  // 顯示所有可用的IP
  for (int i = 0; i < loopCount; i++) {
    ipStatus += "<tr>";
    ipStatus += "<td style='padding: 8px;'>" + ipToString(ipListPtr[i]) + "</td>";
    ipStatus += "<td style='padding: 8px;'>";

    if (useDhcp) {
      ipStatus += "嘗試失敗";
    } else if (i == currentIpIndex) {
      ipStatus += "<strong style='color: green;'>使用中 ✓</strong>";
    } else if (i < currentIpIndex) {
      ipStatus += "嘗試失敗";
    } else {
      ipStatus += "未嘗試";
    }

    ipStatus += "</td></tr>";
  }

  // 如果使用DHCP，添加當前IP資訊
  if (useDhcp) {
    ipStatus += "<tr style='background-color: #e8f5e9;'>"
                "<td style='padding: 8px;'>"
                + WiFi.localIP().toString() + "</td>"
                                              "<td style='padding: 8px;'><strong style='color: blue;'>DHCP分配 ✓</strong></td>"
                                              "</tr>";
  }

  ipStatus += "</table>";

  String statusPage = "<!DOCTYPE html>"
                      "<html>"
                      "<head>"
                      "<meta charset='UTF-8'>"
                      "<title>ESP32 狀態</title>"
                      "<style>"
                      "body { font-family: Arial, sans-serif; margin: 20px; }"
                      ".status-box { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }"
                      ".status-title { color: #333; margin-bottom: 10px; }"
                      "</style>"
                      "</head>"
                      "<body>"
                      "<h2>ESP32 工作狀態</h2>"
                      "<div class='status-box'>"
                      "<h3 class='status-title'>🌐 網路連接狀態</h3>"
                      "<p>WiFi SSID: "
                      + String(ssid) + "</p>"
                                       "<p>連接狀態: "
                      + String(WiFi.status() == WL_CONNECTED ? "已連接 ✓" : "未連接 ✗") + "</p>"
                                                                                          "<p>信號強度: "
                      + String(WiFi.RSSI()) + " dBm</p>"
                                              "</div>"
                                              "<div class='status-box'>"
                                              "<h3 class='status-title'>📍 IP配置狀態</h3>"
                      + ipStatus + "<p>目前IP: " + WiFi.localIP().toString() + "</p>"
                                                                               "<p>網路遮罩: "
                      + ipToString(subnet) + "</p>"
                                             "<p>預設閘道: "
                      + ipToString(gateway) + "</p>"
                                              "<p>IP模式: "
                      + String(useDhcp ? "DHCP" : "固定IP") + "</p>"
                                                              "</div>"
                                                              "<div class='status-box'>"
                                                              "<h3 class='status-title'>⚙️ 系統狀態</h3>"
                                                              "<p>機號: "
                      + String(savedData1) + "</p>"
                                             "<p>韌體版本: "
                      + String(Version) + "</p>"
                                          "<p>運行時間: "
                      + String(millis() / 1000) + " 秒</p>"
                                                  "<p>記憶體可用: "
                      + String(ESP.getFreeHeap()) + " bytes</p>"
                                                    "<p>CPU頻率: "
                      + String(ESP.getCpuFreqMHz()) + " MHz</p>"
                                                      "</div>"
                                                      "<div class='status-box'>"
                                                      "<h3 class='status-title'>🔄 操作選項</h3>"
                                                      "<p><a href='/cmb' style='background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>返回首頁</a></p>"
                                                      "</div>"
                                                      "</body>"
                                                      "</html>";
  server.send(200, "text/html; charset=UTF-8", statusPage);
}

// 掃描並驗證 WiFi 網路
void scanAndValidateNetworks() {
  Serial.println("PASS 掃描 WiFi 網路...");
  // 這裡可以加入實際的 WiFi 掃描邏輯
}

void IRAM_ATTR client_send(const String& message) {
  buffer_push(message.toInt());
}

// 將資料推入緩衝區
void IRAM_ATTR buffer_push(int value) {
  // Serial.printf("buffer_push(%d)\n", value);
  num_buffer[num_head] = value;
  num_head = (num_head + 1) % NUM_BUFFER_SIZE;
  if (num_head == num_tail) {
    num_tail = (num_tail + 1) % NUM_BUFFER_SIZE;  // Buffer 已滿，覆寫舊資料
    Serial.println("Buffer 已滿，覆寫舊資料");
  }
}

// 從緩衝區彈出資料
bool buffer_pop(int& value) {
  if (num_head == num_tail) {
    return false;  // Buffer 為空
  }
  // Serial.printf("buffer_pop(%d)\n", value);
  value = num_buffer[num_tail];
  num_tail = (num_tail + 1) % NUM_BUFFER_SIZE;
  return true;
}

int buffer_size() {
  // Serial.printf("\nnum_head:%i, num_tail:%i \n", num_head, num_tail);
  if (num_head >= num_tail) {
    return num_head - num_tail;
  } else {
    return NUM_BUFFER_SIZE - num_tail + num_head;
  }
}

unsigned long bufferSendTime = millis();
void sendBufferedData() {  // loop 定時呼叫
  static bool buffer_use = false;
  // 只有在WiFi和WebSocket都連接時才嘗試發送數據
  if (WiFi.status() == WL_CONNECTED && webSocketClient.isConnected() && !waitingResponse) {
    int value;
    if (retryMode) {
      value = retryValue;
      sendWebSocketMessage(value);
      bufferSendTime = millis();
      retryMode = false;  // 防止卡在重試模式
    } else if (((millis() - bufferSendTime) > 500) && buffer_pop(value)) {
      // Serial.printf(" num_buffer_size=%i ", buffer_size());
      sendWebSocketMessage(value);
      // vTaskDelay(pdMS_TO_TICKS(500));  // 不用太長，有 checkResponse, 2025/08/12 200 -> 500
      bufferSendTime = millis();
      if (buffer_size() > 0) {
        buffer_use = true;
      }
      if (buffer_use == true && buffer_size() == 0) {
        buffer_use = false;
        // 取號 get, 如斷線後叫號有變動將顯示號碼與 server 最新資料同步(因 loging 時會被更改)
        String message = String(Caller_Number) + ",get";
        updateSystemState(STATE_TRANS);
        Serial.println("查詢最新叫號號碼!");
        webSocketClient_sendTXT(message);  // INFO
        vTaskDelay(pdMS_TO_TICKS(200));    // 或使用 delay
      }
    }
  }
  checkResponse();
}

void check_auth() {
  String message = "";
  if (new_connect) {
    new_connect = false;
    char bssid[18];

    // login
    String caller_password = FPSTR(auth_password);
    message = String(Caller_Number) + ",auth," + caller_password;
    updateSystemState(STATE_TRANS);
    webSocketClient_sendTXT(message);  // AUTH
    vTaskDelay(pdMS_TO_TICKS(200));    // 或使用 delay

    // info
    sprintf(bssid, "%02X:%02X:%02X:%02X:%02X:%02X", WiFi.BSSID()[0], WiFi.BSSID()[1], WiFi.BSSID()[2], WiFi.BSSID()[3], WiFi.BSSID()[4], WiFi.BSSID()[5]);
    // message = String(Caller_Number) + ",info," + "'SSID:" + String(WiFi.SSID()) + " ; RSSI:" + String(WiFi.RSSI()) + "dBm" + " ; BSSID:" + String(bssid) + " ; Ver:" + String(Version) + "'";
    message = String(Caller_Number) + ",info," + "'SSID:" + String(WiFi.SSID()) + " ; RSSI:" + String(WiFi.RSSI()) + "dBm" + " ; BSSID:" + String(bssid) + " ; IP:" + String(WiFi.localIP().toString()) + " ; APIP:" + String(WiFi.softAPIP().toString()) + " ; Ver:" + String(Version) + "'";
    updateSystemState(STATE_TRANS);
    webSocketClient_sendTXT(message);  // INFO
    vTaskDelay(pdMS_TO_TICKS(200));    // 或使用 delay

    // 取號 get
    message = String(Caller_Number) + ",get";
    updateSystemState(STATE_TRANS);
    Serial.println("查詢最新叫號號碼!");
    webSocketClient_sendTXT(message);  // GET
    vTaskDelay(pdMS_TO_TICKS(200));    // 或使用 delay
  }
}

// 發送 WebSocket 訊息
void sendWebSocketMessage(int value) {
  String message = "";
  check_auth();
  message = String(Caller_Number) + ",send," + String(value);
  updateSystemState(STATE_TRANS);
  bool success = webSocketClient_sendTXT(message);  // NUMBER

  if (success) {
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
    sendTime = millis();
    waitingResponse = true;
    retryMode = false;
    Serial.printf(" 傳送：%s ", message.c_str());
  } else {
    updateSystemState(STATE_WEBSOCKET_CONNECTING);
    // Serial.println("傳送失敗，WebSocket 可能未連接");
    // 將數據放回 buffer
    retryValue = value;
    retryMode = true;
    waitingResponse = false;
    // 檢測到發送失敗，立即嘗試重新連接 WebSocket
    Serial.println("傳送失敗，立即嘗試重新連接 WebSocket");
    webSocketClient.disconnect();
    vTaskDelay(pdMS_TO_TICKS(500));  // 或使用 delay
    setupWebSocket();
  }
}

// 檢查回應
void checkResponse() {
  if (waitingResponse) {                               // 尚無回應
    if (millis() - sendTime >= retryTimeout * 2000) {  //!!!@@@
      waitingResponse = false;
      retryMode = true;
      retryValue = num_buffer[(num_tail == 0) ? NUM_BUFFER_SIZE - 1 : num_tail - 1];
      Serial.println("回應超時，啟動重試機制");

      // 連續超時可能表示連接有問題，嘗試重新連接
      static int timeoutCount = 0;
      timeoutCount++;

      if (timeoutCount >= 1) {
        Serial.println("多次超時，嘗試重新連接 WebSocket");
        webSocketClient.disconnect();
        delay(500);
        setupWebSocket();
        timeoutCount = 0;
      }
    }
  } else {
    // 非等待回應狀態，重置超時計數
    static int timeoutCount = 0;
    timeoutCount = 0;
  }
}

// 處理按鈕
void handleButton(unsigned long currentMillis) {
  if (currentMillis - lastCheckIO0 >= CHECK_IO0_INTERVAL) {
    lastCheckIO0 = currentMillis;
    bool buttonState = digitalRead(BUTTON_PIN);
    if (buttonState == LOW && lastButtonState == HIGH) {
      if (currentMillis - lastButtonPress <= MULTI_CLICK_INTERVAL) {
        clickCount++;
        Serial.printf("Click count: %d\n", clickCount);
      } else {
        Serial.println("Reset count");
        clickCount = 1;
      }
      lastButtonPress = currentMillis;
    }
    if (clickCount == CLICK_COUNT_TARGET) {
      toggleDemoMode();
      clickCount = 0;
    }
    lastButtonState = buttonState;
  }
}

// 處理 Demo 模式
void handleDemoMode(unsigned long currentMillis) {
  if (currentMillis - lastUpdateTime >= nextUpdateInterval) {
    // 生成非零隨機變化值
    int change;
    do {
      change = 1;  // 固定變化值
    } while (change == 0);

    int nowStrNum = nowStrDemo.toInt();
    nowStrNum = ((nowStrNum + change - MIN_VALUE) % (MAX_VALUE - MIN_VALUE + 1)) + MIN_VALUE;

    if (true) {  // 沒連線一樣傳送至buffer
      nowStrDemo = String(nowStrNum);
      // send_and_dis(nowStrDemo);
      client_send(nowStrDemo);
      num_LED_dis(nowStrDemo);
      onMessage_time = currentMillis;  // 重置 onMessage 計時器
    }
    lastUpdateTime = currentMillis;
    nextUpdateInterval = random(MIN_INTERVAL, MAX_INTERVAL + 1);
  }
}

void num_LED_dis(const String& message) {  // LED 顯示即設定最新值
  // Serial.printf("Set nowStr: '%s' -> '%s'\n", nowStr, message);
  nowStr = message;  // !!!@@@
  nowStrDemo = nowStr;
  // client_send(message);
  // Serial.printf("Set sendStr: '%s' -> '%s'\n", sendStr, message);
  if (bypassLast) {
    lastSendStr = "000";
    bypassLast = false;
  } else {
    lastSendStr = sendStr;
  }
  sendStr = message;  // !!!@@@
  cldUR2Send(message.toInt());
}

// 切換 Demo 模式
void toggleDemoMode() {
  demoState = !demoState;
  Serial.printf("Demo mode: %s\n", demoState ? "ON" : "OFF");
  if (demoState) {
    // 設定初始值
    randomSeed(millis());
    lastUpdateTime = millis();
    nextUpdateInterval = random(MIN_INTERVAL, MAX_INTERVAL + 1);
    updateSystemState(STATE_DEMO);
  } else {
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
  }
}

// 檢查 IP 是否可用
bool isIPAvailable(IPAddress ip) {
  bool available = true;
  int successCount = 0;

  for (int i = 0; i < RETRY_COUNT; i++) {
    if (Ping.ping(ip, 1)) {  // 發送1個ping包
      successCount++;
    } else {
      // Serial.printf("Ping測試(%s) %d: 失敗\n", ip.toString().c_str(), i + 1);
    }
    delay(100);  // 短暫延遲避免過度頻繁
  }
  // 如果超過一半的ping成功，認為IP在使用中
  if (successCount > RETRY_COUNT / 2) {
    available = false;
  }
  return available;
}

// ==========================================================
// WiFi 模式切換
// 定義可配置的參數
#define AP_TIMEOUT_MS (20 * 60 * 1000)  // 分鐘轉換為毫秒
const int CODE1_PART1 = 159;            // 第一組數字的第一部分
const int CODE1_PART2 = 357;            // 第一組數字的第二部分
const int CODE2_PART1 = 357;            // 第二組數字的第一部分
const int CODE2_PART2 = 159;            // 第二組數字的第二部分

enum WifiProcessStatus {
  IDLE,
  WAITING_FOR_SECOND_CODE,
  ACTIVE_MODE
};

unsigned long modeActivationTime = 0;
WifiProcessStatus currentState = IDLE;
unsigned long stateEnterTime = 0;
int firstCode = 0;

int AP_mode_now = 1;
// 不切換，一率 STATE_AP_STA mode
void change_AP_mode() {
  if (AP_mode_now == AP_mode) {
    return;
  }
  Serial.printf("切換 AP 到模式 %i\n", AP_mode);
  AP_mode_now = AP_mode;
  // updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WEBSOCKET_CONNECTED);
  // 檢查記憶體狀況
  if (ESP.getFreeHeap() < 20000) {
    Serial.println("警告: 記憶體不足，延遲切換");
    delay(1000);
    if (ESP.getFreeHeap() < 15000) {
      Serial.println("記憶體嚴重不足，重啟系統");
      ESP.restart();
      return;
    }
  }
  // 根據模式執行相應設定
  if (AP_mode == 1) {
    // Serial.println("設定 AP 模式...");
    setupAP();
  } else {
    // Serial.println("關閉 AP 模式...");
    disableAP();
  }
  Serial.printf("切換完成，剩餘記憶體: %d bytes\n", ESP.getFreeHeap());
}

void process_change_AP_mode(int code) {
  switch (currentState) {
    case IDLE:
      if (code == CODE1_PART1 || code == CODE2_PART1) {
        firstCode = code;
        currentState = WAITING_FOR_SECOND_CODE;
        stateEnterTime = millis();
        Serial.print("Waiting for second code. First code: ");
        Serial.println(code);
      }
      break;

    case WAITING_FOR_SECOND_CODE:
      // 檢查超時
      if (millis() - stateEnterTime > 30000) {  // 30秒超時
        currentState = IDLE;
        Serial.println("Timeout waiting for second code");
        break;
      }

      // 檢查匹配
      if ((firstCode == CODE1_PART1 && code == CODE1_PART2) || (firstCode == CODE2_PART1 && code == CODE2_PART2)) {

        if (firstCode == CODE1_PART1) {
          AP_mode = 1;
          modeActivationTime = millis();
          currentState = ACTIVE_MODE;
          Serial.println("AP_mode enabled by code combination 1");
          change_AP_mode();
        } else {
          AP_mode = 0;
          currentState = IDLE;
          Serial.println("AP_mode disabled by code combination 2");
          change_AP_mode();
        }
      } else {
        // 不匹配的代碼，回到IDLE
        currentState = IDLE;
        Serial.println("Invalid code combination");
      }
      break;

    case ACTIVE_MODE:
      // 在ACTIVE_MODE狀態下仍然可以接收代碼
      if (code == CODE2_PART1) {
        firstCode = code;
        currentState = WAITING_FOR_SECOND_CODE;
        stateEnterTime = millis();
        Serial.print("Waiting for second code to deactivate. First code: ");
        Serial.println(code);
      }
      break;
  }
}

// ==========================================================


// 通訊狀態標記
byte cld_flag = 1;  // CLD指令處理狀態(0:待命,1:成功,2:錯誤)

// 通訊數據緩衝
String bleValue = "";  // 儲存原始BLE數據
String cldValue = "";  // 儲存原始CLD數據

// 數值變數
unsigned int bleNum = 0;  // BLE轉換後的數值(0-999)
unsigned int cldNum = 1;  // CLD當前編號(0-999)

/**
 * UART2數據接收處理函式
 * 處理兩種指令格式：
 * 1. BLE_XXX_s (藍牙指令)
 * 2. CLD_XXX_s (雲端指令)
 */
bool UR2Recv() {
  bool result = false;
  // Serial.print("UR2Recv\n");
  if (mySerial.available()) {
    // 讀取直到換行符的數據
    String recMessage = mySerial.readStringUntil('\n');
    recMessage.trim();                          // 移除多餘空白字符
    Serial.printf("Get : '%s'\n", recMessage);  // 輸出原始數據用於調試
    // 只處理9字元長度的有效指令
    if (recMessage.length() == 9) {
      /* BLE指令處理區塊 */
      if (recMessage.startsWith("BLE_")) {
        // 提取數字部分(第4-6字元)
        bleValue = recMessage.substring(4);
        bleNum = bleValue.toInt();
        bleValue = String(bleNum);  // 去掉文字
        // 新的叫號輸入
        Serial.printf("Set nowStr: '%s' -> '%s' \n", nowStr, bleValue);  // 輸出原始數據用於調試
        nowStr = bleValue;                                               // OK

        // 數值有效性檢查(1-999)
        // if (bleNum != 0 && bleNum < 1000) {
        if (bleNum < 1000) {  // 改可以是 0
          // 組裝回覆字串(補零格式)
          String sendBleStr = "BLE_";
          if (bleNum <= 9) sendBleStr += "00";       // 個位數補兩個零
          else if (bleNum <= 99) sendBleStr += "0";  // 十位數補一個零
          sendBleStr += String(bleNum) + "_s";       // 添加結尾標記
          mySerial.println(sendBleStr);              // 回傳確認訊息
          // Serial.println("BLE_OK");   // 序列埠輸出狀態
          result = true;
        } else {
          bleNum = 0;                   // 無效數值重置
          Serial.println("BLE Fail!");  // 序列埠輸出狀態
        }
      }

      /* CLD指令處理區塊 */
      // 只在待命狀態(cld_flag=0)時處理
      if (cld_flag == 0) {
        // 組裝預期接收格式(補零格式)
        String expected = "CLD_";
        if (cldNum <= 9) expected += "00";
        else if (cldNum <= 99) expected += "0";
        expected += String(cldNum) + "_s";

        // 比對接收數據
        if (recMessage.startsWith(expected)) {
          cld_flag = 1;  // 標記成功狀態
          // Serial.println("CLD_OK");
        } else {
          cld_flag = 2;               // 標記錯誤狀態
          Serial.println("CLD_ERR");  // 輸出錯誤日誌
          Serial.println(expected);   // 輸出預期值用於調試
        }
      }
    }
  }
  return result;  // BLE_ 輸入才為 true
}

/**
 * 發送CLD格式指令
 * @param num 要發送的數值(1-999)
 * 格式範例：CLD_001_S
 */
void cldUR2Send(unsigned long num) {
  // 數值有效性檢查
  // if (num != 0 && num < 1000) {
  if (num < 1000) {  // 改可以是 0
    // 組裝發送字串(注意結尾是大寫S)
    String sendCldStr = "CLD_";
    if (num <= 9) sendCldStr += "00";
    else if (num <= 99) sendCldStr += "0";
    sendCldStr += String(num) + "_S";

    mySerial.println(sendCldStr);  // 透過UART2發送
    // Serial.printf(" To_LED:%s ",sendCldStr);    // 序列埠輸出用於調試

    // 狀態重置
    cld_flag = 0;  // 重置為待命狀態
    cldNum = num;  // 更新當前編號
  }
}






// 初始化函數
void setup() {
  Serial.begin(115200);
  startTime = millis();  // 記錄開機時間

  delay(250);
  Serial.println(".");
  Serial.println(".");
  delay(250);
  Serial.println(".");
  Serial.println(".");
  delay(250);
  Serial.println(".");
  Serial.println(".");
  Serial.println("----------------------------------");

  // 初始化UART2
  mySerial.begin(9600, SERIAL_8N1, RX2, TX2);  // 波特率9600,8資料位,無校驗,1停止位
  mySerial.setTimeout(200);                    // 設置讀取超時200ms
  Serial.println("mySerial Setup OK");         // 輸出初始化完成訊息

  // // 初始化看門狗
  // esp_task_wdt_config_t config = {
  //   .timeout_ms = 60000,
  //   .idle_core_mask = (1 << portNUM_PROCESSORS) - 1,
  //   .trigger_panic = true
  // };
  // esp_task_wdt_init(&config);
  // esp_task_wdt_add(NULL);  // 添加當前任務到監控
  // Serial.println("啟動看門狗(60秒超時)");

  // 初始化存儲資料
  handleRetrieve();
  if (savedData1 == "") {
    savedData1 = "z0000";
    savedData2 = "88888888";
    preferences.begin("storage", false);
    preferences.putString("saved_data1", savedData1);
    preferences.putString("saved_data2", savedData2);
    preferences.end();
    handleRetrieve();
  }
  if (savedData1 == "z0000") {
    NullId = true;
  }
  Caller_Number = savedData1;
  Serial.printf("cmb_caller Ver:%s, Caller Number %s.\n\n", Version.c_str(), Caller_Number);

  // 初始化 Caller_SSID
  strcpy(Caller_SSID, Caller_Prefix);
  strcat(Caller_SSID, Caller_Number.c_str());
  strncpy(defaultNetworks[0].ssid, Caller_SSID, sizeof(defaultNetworks[0].ssid) - 1);
  defaultNetworks[0].ssid[sizeof(defaultNetworks[0].ssid) - 1] = '\0';  // 確保結尾有 '\0'
  strncpy(defaultNetworks[0].password, "88888888", sizeof(defaultNetworks[0].password) - 1);
  defaultNetworks[0].password[sizeof(defaultNetworks[0].password) - 1] = '\0';

  // 初始化 LED 與按鈕
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  initLedConfigs();

  // 初始化 FreeRTOS 計時器
  redTimer = xTimerCreate("RedLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].red, blinkLED);
  greenTimer = xTimerCreate("GreenLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].green, blinkLED);
  xTimerStart(redTimer, 0);
  xTimerStart(greenTimer, 0);

  updateSystemState(STATE_INIT);
  // updateSystemState(STATE_WIFI_CONNECTING);

  // 初始化中斷與計時器
  const int inputs[] = { BUTTON_PIN };
  for (int pin : inputs) {
    pinMode(pin, INPUT);
    // Serial.printf("SET_Inmpt(%d) ", pin);
  }

  // 初始化 WiFi
  Serial.printf("WiFi 設定到 %i 模式!\n", WIFI_AP_STA);
  WiFi.mode(WIFI_AP_STA);
  setupAP();

  delay(200);
  AP_mode = 0;
  // change_AP_mode();     // 太快 disconnect 容易 reboot.(某些機器)

  WiFi.setSleep(false);
  bool result = false;
  bool boot = true;

  loadNetworks();
  mergeDefaultNetworks();


  // 初始化 OTA 與 WebSocket
  setupOTA();
  // setupWebSocket(); 移至 loop

  // 啟動 Web 伺服器
  server.on("/cmb", HTTP_GET, cmb_handleRoot);
  server.on("/cmb_store", HTTP_POST, handleStore);
  server.on("/cmb_retrieve", HTTP_GET, handleRetrieve);
  server.on("/cmb_status", HTTP_GET, handleStatus);

  server.on("/", handleRoot);
  server.on("/scan", handleScan);
  server.on("/add_http", handleAddHTTP);
  server.on("/delete_http", handleDeleteHTTP);
  server.on("/move_up_http", handleMoveUpHTTP);
  server.on("/move_down_http", handleMoveDownHTTP);
  server.on("/add_manual", handleAddManual);

  server.begin();

  // updateSystemState(STATE_WIFI_CONNECTING);
  updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
  Serial.println("\nSetup finish!");
  Serial.println("----------------------------------\n\n");
  // setup_finish = true;
}


// 主循環
void loop() {
  static unsigned long lastStatusTime = 0;
  // Serial.print("L");
  currentMillis = millis();

  // esp_task_wdt_reset();  // 喂狗

  scanWiFiInBackground();
  attemptWiFiConnect();

  if (WiFi.status() == WL_CONNECTED) {
    if (!WebSocket_init) {
      WebSocket_init = true;
      setupWebSocket();  // 設定連線至 WebSocket Server.
    }
    // Serial.printf("webSocketClient.loop()\n");
    webSocketClient.loop();  // 處理 WebSocket 事件, 必須有連線
  }

  server.handleClient();
  ArduinoOTA.handle();

  GetSendCallerNumber(currentMillis);

  // if (currentMillis - lastCheck >= STATE_UPDATE_INTERVAL) {
  //   lastCheck = currentMillis;
  //   checkConnections();
  // }

  if (currentMillis - lastPING >= PING_INTERVAL) {
    lastPING = currentMillis;
    Ping_EX();
  }

  if (currentMillis - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentMillis;
    sendBufferedData();
  }

  handleButton(currentMillis);

  if (demoState) {
    handleDemoMode(currentMillis);
  }

  // 斷線檢測與立即重連
  if (WiFi.status() != WL_CONNECTED) {
    // if (WiFi.status() != WL_CONNECTED || WiFi.RSSI() < -100) {
    // updateSystemState(STATE_WIFI_CONNECTING);
    // 每0.5秒顯示一次狀態
    if (millis() - lastStatusTime >= STATUS_INTERVAL) {
      lastStatusTime = millis();
      Serial.print(" D");  // 斷線中
    }
    if (lastDisconnectTime == 0) {  // 斷線時只做一次
      lastDisconnectTime = millis();
      digitalWrite(LED_PIN, LOW);
      Serial.printf("WiFi 連接中斷!(%s,%d dBm)\n", getWiFiStatusString(WiFi.status()), WiFi.RSSI());
      // 只斷開 Station 連接，不影響 SoftAP
      WiFi.disconnect(false, false);
      int scan_delay = 0;
      Serial.printf("scannedNetworks.size()=%d\n", scannedNetworks.size());
      if (scannedNetworks.size() <= 0) {
        // scan_delay = 0;
        //scan_delay = 0;  // !!!@@@  // 啟動已有預設立即掃描WiFi
      } else {
        scan_delay = 5000;  // 如不是剛開機則先嘗試連接之前掃描的網路
        Serial.printf("WiFi 連接中斷, 設定 %d 秒後 WiFi 掃描!", scan_delay / 1000);
        lastScanTime = millis() - SCAN_INTERVAL + scan_delay;
        lastScanTimeRun = lastScanTime - SCAN_MIN_INTERVAL;
      }
    } else if (millis() - lastDisconnectTime > RECONNECT_DELAY) {
      // attemptWiFiConnect();
      lastDisconnectTime = millis();  // 重置計時器
    }
  } else {  // == WL_CONNECTED)
    if (millis() - lastStatusTime >= STATUS_INTERVAL) {
      lastStatusTime = millis();
      if (webSocketClient.isConnected()) {
        Serial.print(" C");  // 連線中
      } else {
        Serial.print(" Cd");  // WiFi 連線中 但 Websocket 斷線中
      }
    }
    // if (!webSocketClient.isConnected()) {
    //   Serial.println("\n1_Websocket 斷線設定重新連線!!!");      // 較慢 ~= 2.36 Sec
    //   WebSocket_init = false;
    // }
    lastDisconnectTime = 0;  // 連接正常時重置
    digitalWrite(LED_PIN, HIGH);
    check_auth();
  }

  if (Maint_mode && ((currentMillis - startTime) > expireTime)) {
    Maint_mode = false;
    Serial.printf("\nMaint_mode(%d) off!\n", Maint_mode);
    if (NullId) {
      // Serial.printf("\n重新取得IP!\n");
      Serial.println("斷開 WiFi & WebSocket 連接");
      webSocketClient.disconnect();
      WiFi.disconnect();
    }
  }

  if (currentMillis - lastPrintTime >= printInterval) {
    Serial.printf("check_system()\n");
    check_system(lastPrintTime, currentMillis);
    lastPrintTime = currentMillis;
  }

  change_AP_mode();
  // 查AP_STA模式是否超時
  if (AP_mode == 1) {
    if (millis() - modeActivationTime > AP_TIMEOUT_MS) {
      AP_mode = 0;
      Serial.println("[Timeout] AP模式超時，自動 Disable");
      change_AP_mode();
    }
  }

  // vTaskDelay(pdMS_TO_TICKS(100));  // !!!@@@
}
