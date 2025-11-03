// 修改紀錄
/*
 * 修改紀錄:
 * 2025-xx-xx: Roy Ching  初始版本
 * 2025-03-11: Roy Ching  增加資料BUFFER.
 * 2025-03-12: Roy Ching  加強斷線斷訊重傳功能.
 * 2025-03-12: Roy Ching  Webscok重連時傳送系統資訊.
 * 2025-03-13: Roy Ching  程式重整.
 * 2025-03-14: Roy Ching  GCE IP 改用DNS轉址.
 * 2025-03-17: Roy Ching  Websocket LIB 由 <ArduinoWebsockets.h>  改為用  <WebSocketsClient.h>
 * 2025-03-18: Roy Ching  支援 GCE & GCR
 * 2025-03-18: Roy Ching  改直接使用鍵盤訊號訊號
 */

// 引入必要的函式庫
#include <WebSocketsClient.h>    // 用於 WebSocket 通訊
#include <Arduino.h>             // Arduino 核心函式庫
#include <WiFi.h>                // ESP32 WiFi 功能
#include <ArduinoOTA.h>          // OTA 更新功能
#include "freertos/FreeRTOS.h"   // FreeRTOS 相關功能
#include "freertos/task.h"       // FreeRTOS 任務管理
#include "esp_freertos_hooks.h"  // FreeRTOS 鉤子函數
#include "sdkconfig.h"           // ESP32 SDK 配置
#include <WebServer.h>           // Web 伺服器功能
#include <Preferences.h>         // 用於存儲偏好設定
#include <ESPping.h>             // Ping 功能

// 引入自定義的憑證檔案（例如 WiFi SSID 和密碼）
#include "credentials.h"

// 程式版本資訊
String Version = "2025032017_test";  // 當前韌體版本

// 宣告外部函數（用於獲取任務運行時間統計）
extern void vTaskGetRunTimeStats(char* pcWriteBuffer);

// 呼叫號碼（用於識別設備）
String Caller_Number = "00000";  // 會變

#ifdef USE_KEYBOARD_SIGNAL
#define BLED 2
#define SRV_P34 34
#else
// LED 腳位定義
#define LED_a 17
#define LED_b 5
#define LED_c 18
#define LED_d 19
#define LED_e 21
#define LED_f 22
#define LED_g 23
#define LED_1e 16
#define LED_2e 4
#define LED_3e 15
#endif
#define LED_RED 33    // 紅色 LED
#define LED_GREEN 32  // 綠色 LED

// 計時器和網路相關設定
const long WIFI_TIMEOUT = 7000;           // WiFi 連接超時時間（7 秒）
const long WS_TIMEOUT = 5000;             // WebSocket 連接超時時間（5 秒）
const long STATE_UPDATE_INTERVAL = 500;   // 狀態更新間隔（500 毫秒）
const long PING_INTERVAL = 30000;         // Ping 間隔（30 秒）
const long ON_MESSAGE_TIMEOUT = 10000;    // onMessage 超時時間（10 秒）
const long printInterval = (10 * 60000);  // 系統訊息列印間隔（10 分鐘）
const long CHECK_DISPLAY_INTERVAL = 100;  // 中斷取樣間隔（100 毫秒）
const long SCAN_NUM = 3;                  // 中斷取樣次數
const long CHECK_NUMBER_INTERVAL = 50;    // 數值變動取樣間隔（50 毫秒）

// 系統變數
unsigned long lastPING = 0;  // 上次 Ping 時間
// unsigned long delayStart = 0;                     // 延遲起始時間
int currentNetwork = 0;                           // 當前 WiFi 網路索引
volatile unsigned long onMessage_time = 0;        // onMessage 計時器
unsigned long lastPrintTime = millis();           // 上次列印系統訊息時間
unsigned long lastCheckNumber = 0;                // 上次檢查數字時間
volatile unsigned long InterruptCount = 0;        // 中斷計數器
volatile unsigned long scanDisplayCount = 0;      // 數字掃描計數器
volatile unsigned long currentMillis = millis();  // 當前時間
volatile unsigned long lastScanDisplayTime = 0;   // 上次數字掃描時間
volatile int scanCallCount = 0;                   // 數字掃描呼叫次數

// 呼叫號碼相關定義
const char Caller_Prefix[] = "CMB";                                   // 呼叫號碼前綴
char Caller_SSID[sizeof(Caller_Prefix) + sizeof(Caller_Number) - 1];  // 呼叫號碼 SSID

// CPU 負載量變數
volatile uint32_t idleCount[portNUM_PROCESSORS] = { 0 };      // 空閒計數
volatile uint32_t idleCountLast[portNUM_PROCESSORS] = { 0 };  // 上次空閒計數


// 數字顯示相關變數
int fe[3] = { 0 };  // 數字顯示狀態
// volatile int n1 = -1, n2 = -1, n3 = -1;  // 當前數字
int pn1 = -2, pn2 = -2, pn3 = -2;       // 上次數字
volatile bool has_interrupted = false;  // 中斷標記
hw_timer_t* timer0;                     // 硬體計時器
String preStr = "";                     // 上次數字字串
String nowStr = "";                     // 當前數字字串
String nowStrDemo = "0";                // Demo 模式數字字串
String sendStr = "";                    // 發送數字字串
int matchCt = 0;                        // 數字匹配計數器

int n1 = -1, n2 = -1, n3 = -1;

// WebSocket 客戶端
WebSocketsClient webSocketClient;


// Demo 模式相關設定
const int BUTTON_PIN = 0;                  // 按鈕腳位
const int LED_PIN = 32;                    // LED 腳位
const long CHECK_IO0_INTERVAL = 100;       // 按鈕檢測間隔（100 毫秒）
const long MULTI_CLICK_INTERVAL = 500;     // 連續按壓有效時間（500 毫秒）
const int CLICK_COUNT_TARGET = 2;          // 目標按壓次數
const unsigned long MIN_INTERVAL = 30000;  // 最小更新間隔（30 秒）
const unsigned long MAX_INTERVAL = 90000;  // 最大更新間隔（90 秒）
const int MIN_CHANGE = -1;                 // 最小變化值
const int MAX_CHANGE = 2;                  // 最大變化值
const int MIN_VALUE = 1;                   // 最小允許值
const int MAX_VALUE = 999;                 // 最大允許值

// 狀態變數
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
  STATE_COUNT                  // 狀態總數
};

// LED 控制結構
struct LedState {
  bool isOn;                 // LED 當前狀態
  bool isBlinking;           // 是否閃爍
  unsigned long onTime;      // 亮持續時間（毫秒）
  unsigned long offTime;     // 滅持續時間（毫秒）
  unsigned long lastToggle;  // 最後切換時間
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

// LED 配置
struct LedConfig {
  LedState red;    // 紅色 LED 狀態
  LedState green;  // 綠色 LED 狀態
} ledConfigs[STATE_COUNT];

// FreeRTOS 計時器
TimerHandle_t redTimer;     // 紅色 LED 計時器
TimerHandle_t greenTimer;   // 綠色 LED 計時器
bool setup_finish = false;  // 初始化完成標記


// IP 地址列表
int xxx = 0;  // 預留 IP 地址
IPAddress ipList[] = {
  IPAddress(xxx, xxx, xxx, 128),
  IPAddress(xxx, xxx, xxx, 118),
  IPAddress(xxx, xxx, xxx, 108)
};
const int IP_COUNT = sizeof(ipList) / sizeof(ipList[0]);

// 當前 IP 索引與循環計數
int currentIpIndex = 0;
int loopCount;         // 循環次數
IPAddress* ipListPtr;  // 指向選擇的 IP 列表
bool useDhcp = false;  // 是否使用 DHCP

// IP 地址相關變數
IPAddress apIP;     // AP IP 地址
IPAddress LocalIP;  // 本地 IP 地址
IPAddress gateway;  // 閘道 IP 地址
IPAddress subnet;   // 子網掩碼
IPAddress dns;      // DNS 伺服器

// Web 伺服器實例
WebServer server(80);     // Web 伺服器端口 80
Preferences preferences;  // 偏好設定

// 存儲的資料
String savedData1 = "";        // 存儲資料 1
String savedData2 = "";        // 存儲資料 2
String savedData3 = "";        // 存儲資料 3
volatile bool NullId = false;  // 空 ID 標記

// 開機時間與失效時間
unsigned long startTime = 0;                           // 開機時間
const unsigned long expireMinutes = 5;                 // 失效時間（5 分鐘）
unsigned long expireTime = expireMinutes * 60 * 1000;  // 失效時間（毫秒）


// 資料緩衝區設定
#define BUFFER_SIZE 60
int buffer[BUFFER_SIZE];
int head = 0;
int tail = 0;

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
unsigned long lastWebSocketCheckTime = 0;
const int webSocketCheckInterval = 3000;  // 檢查WebSocket狀態的間隔時間(毫秒)
unsigned long lastWSReconnectAttempt = 0;
const int wsReconnectCooldown = 5000;  // WebSocket重連冷卻時間(毫秒)
unsigned long lastPingTime = 0;
const int pingInterval = 10000;  // Ping間隔時間(毫秒)
int wsReconnectAttempts = 0;
const int maxWSReconnectAttempts = 5;  // 最大WebSocket重試次數

unsigned long lastScanTime = millis();     // 記錄最後一次掃描網路的時間
const unsigned long scanInterval = 60000;  // 掃描網路的時間間隔（毫秒）

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
#define MAX_WEBS_RTY_TIME (60 * 1000)

//======================================================================
// 函數原型宣告
void updateSystemState(SystemState newState, const String& error = "");
bool connectToWiFi(const char* ssid_in, const char* password_in);
void scanDisplayDigits();

void IRAM_ATTR isr_handler();
void IRAM_ATTR handleInterrupt();
void IRAM_ATTR sendCallerNumber(unsigned long currentMillis);

bool vApplicationIdleHook(void);
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
void checkConnections();
// void onEventsCallback(WebsocketsEvent event, String data);
// void onMessageCallback(WebsocketsMessage message);
void onMessageCallback(String message);
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


// 初始化函數
void setup() {
  Serial.begin(115200);
  startTime = millis();  // 記錄開機時間

#ifdef LOCAL_TEST
  Version += " Local Test!";
#endif

  delay(250);
  Serial.println(".");
  Serial.println(".");
  delay(250);
  Serial.println(".");
  Serial.println(".");
  delay(250);
  Serial.println(".");
  Serial.println(".");
  Serial.println("----------------------------------\n");
  // 初始化存儲資料
  handleRetrieve();
  if (savedData1 == "") {
    savedData1 = "z0000";
    savedData2 = "88888888";
    preferences.begin("storage", false);
    preferences.putString("saved_data1", savedData1);
    preferences.end();
    handleRetrieve();
  }
  if (savedData1 == "z0000") {
    NullId = true;
  }
  Caller_Number = savedData1;
  Serial.printf("cmb_caller Ver:%s, Caller Number %s.\n", Version.c_str(), Caller_Number);

  // 初始化 Caller_SSID
  strcpy(Caller_SSID, Caller_Prefix);
  strcat(Caller_SSID, Caller_Number.c_str());
  wifiNetworks[0].ssid = Caller_SSID;
  wifiNetworks[0].password = "88888888";

  // 初始化 LED 與按鈕
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  initLedConfigs();

  // 初始化 FreeRTOS 計時器
  redTimer = xTimerCreate("RedLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].red, blinkLED);
  greenTimer = xTimerCreate("GreenLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].green, blinkLED);
  xTimerStart(redTimer, 0);
  xTimerStart(greenTimer, 0);

  updateSystemState(STATE_INIT);

#ifdef USE_KEYBOARD_SIGNAL
  pinMode(BLED, OUTPUT);
  pinMode(SRV_P34, INPUT);
  pinMode(BUTTON_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(SRV_P34), isr_handler, RISING);
#else
  // 初始化中斷與計時器
  const int inputs[] = { LED_a, LED_b, LED_c, LED_d, LED_e, LED_f, LED_g, LED_1e, LED_2e, LED_3e, BUTTON_PIN };
  for (int pin : inputs) {
    pinMode(pin, INPUT);
    Serial.printf("SET_Inmpt(%d) ", pin);
  }
  // timer0 = timerBegin(1000000);         // 1MHz
  // timerAlarm(timer0, 500000, true, 0);  // 500ms
  // timerAttachInterrupt(timer0, &handleInterrupt);
  // // 設置外部中斷
  // attachInterrupt(digitalPinToInterrupt(LED_1e), handleInterrupt, RISING);
  // attachInterrupt(digitalPinToInterrupt(LED_2e), handleInterrupt, RISING);
  // attachInterrupt(digitalPinToInterrupt(LED_3e), handleInterrupt, RISING);

  // attachInterrupt(digitalPinToInterrupt(LED_1e), isr_handler, RISING);
  // attachInterrupt(digitalPinToInterrupt(LED_2e), isr_handler, RISING);
  // attachInterrupt(digitalPinToInterrupt(LED_3e), isr_handler, RISING);

#endif

  // 初始化 WiFi
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  bool result = false;
  bool boot = true;

  while (!result) {
    scanAndValidateNetworks();
    for (int i = 0; i < numNetworks; i++) {
      delay(500);
      if (boot && savedData1.startsWith("z0000")) {
        boot = false;
        continue;
      }
      currentNetwork = i;
      if (!wifiNetworks[i].isValid) continue;
      result = connectToWiFi(wifiNetworks[i].ssid, wifiNetworks[i].password);
      if (result) break;
    }
    if (!result) {
      Serial.printf("\nWiFi 無法連線，重新嘗試...\n");
      delay(2000);
    }
  }

  // 初始化 OTA 與 WebSocket
  setupOTA();
  setupWebSocket();

  // 啟動 Web 伺服器
  server.on("/cmb", HTTP_GET, handleRoot);
  server.on("/cmb_store", HTTP_POST, handleStore);
  server.on("/cmb_retrieve", HTTP_GET, handleRetrieve);
  server.on("/cmb_status", HTTP_GET, handleStatus);
  server.begin();

  setup_1();  // !!!@@@

  Serial.println("\n\nSetup finish!\n\n");
  setup_finish = true;
}

void numberGetter2();
void numberSend2();



// 主循環
void loop() {
  static unsigned long lastCheck = 0;
  currentMillis = millis();

  server.handleClient();
  ArduinoOTA.handle();

#ifdef USE_KEYBOARD_SIGNAL
  ma_1ms_timer2();
  ma_1ms_timer();
  ma_led_500ms();

// sNum=String(le_ok_number);
#else

#endif
  currentMillis = millis();
  sendCallerNumber(currentMillis);

  if (currentMillis - lastCheck >= STATE_UPDATE_INTERVAL) {
    lastCheck = currentMillis;
    checkConnections();
    numberGetter2();  //!!!@@@
    numberSend2();
  }

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

  if ((WiFi.status() != WL_CONNECTED) && (currentMillis - lastScanTime >= scanInterval)) {
    lastScanTime = currentMillis;
    scanAndValidateNetworks();
  }

  if (Maint_mode && ((currentMillis - startTime) > expireTime)) {
    Maint_mode = false;
    Serial.printf("\nMaint_mode(%d) off!\n", Maint_mode);
    if (NullId) {
      Serial.printf("\n重新取得IP!\n");
      webSocketClient.disconnect();
      WiFi.disconnect();
    }
  }

  if (currentMillis - lastPrintTime >= printInterval) {
    check_system(lastPrintTime, currentMillis);
    lastPrintTime = currentMillis;
  }

  webSocketClient.loop();  // 處理 WebSocket 事件
  // vTaskDelay(pdMS_TO_TICKS(1));  // !!!@@@
}

#ifdef USE_KEYBOARD_SIGNAL

// 定義常數
const int SIGNAL_LENGTH = 25;              // 訊號總長度
const int MAX_BATCH_COUNT = 30;            // 最大訊號批次數
const int DEBOUNCE_DELAY_MICROS = 500;     // 去抖動延遲時間（微秒）, >300us ~ <900us
const String VALID_HEADER = "000";         // 正確的頭部值
const String VALID_FOOTER = "0010000000";  // 正確的尾部值
const int DATA_START_INDEX = 10;           // 資料部分的起始索引
const int DATA_END_INDEX = 20;             // 資料部分的結束索引
const int LLH = 500;                       // 資料清除時間

// 狀態變數
volatile int currentSignalIndex = 0;                                    // 當前訊號的索引
volatile int currentBatchIndex = 0;                                     // 當前批次的索引
volatile bool isProcessingSignal = false;                               // 訊號處理狀態
volatile int signalBuffer[MAX_BATCH_COUNT][SIGNAL_LENGTH + 5] = { 0 };  // 訊號緩衝區

unsigned long delayStart = 0;                 // 延遲開始時間
unsigned long signalProcessingStartTime = 0;  // 延遲開始時間
unsigned long last500msTick = 0;              // 500 毫秒計數器
unsigned long last100msTick = 0;              // 100 毫秒計數器
bool isLedOn = false;                         // LED 開關狀態

int decodedNumber = 0;        // 解碼後的數值
int stableSignalCounter = 0;  // 穩定計數器
String previousSignal = "";   // 上一次的訊號
String decodedId = "";        // 解碼後的 ID

// 中斷處理函數
// void IRAM_ATTR isr_handler() {
//   // 去抖動延遲
//   delayMicroseconds(DEBOUNCE_DELAY_MICROS);
//   // 讀取訊號值
//   int signalValue = digitalRead(SRV_P34);
//   // Serial.printf("[ISR] Signal Value: %d\n", signalValue);  // 除錯資訊
//   // 如果訊號處理未開始，則開始處理
//   if (!isProcessingSignal) {
//     // 將訊號值存入緩衝區
//     signalBuffer[currentBatchIndex][currentSignalIndex] = signalValue;
//     currentSignalIndex++;
//     // Serial.printf("[ISR] Signal Index: %d, Value: %d\n", currentSignalIndex, signalValue);  // 除錯資訊
//     // 如果達到訊號長度，開始處理訊號
//     if (currentSignalIndex >= SIGNAL_LENGTH) {
//       isProcessingSignal = true;
//       signalProcessingStartTime = millis();
//       digitalWrite(BLED, LOW);
//       isLedOn = false;
//       // Serial.println("[ISR] Signal Processing Started");  // 除錯資訊
//     }
//     // 重置 500 毫秒計數器
//     last500msTick = 0;
//   }
//   sendCallerNumber(millis());  // 持續監測數字變化
// }

// 訊號處理函數
void processSignal() {
  String currentSignal = "";
  String currentHeader = "";
  String currentId = "";
  String currentFooter = "";

  for (int i = 0; i < (SIGNAL_LENGTH + 5); i++) {
    currentSignal += String(signalBuffer[currentBatchIndex][i]);
    if (i <= 2) {
      currentHeader += String(signalBuffer[currentBatchIndex][i]);
    } else if (i >= 3 && i < 10) {
      currentId += String(signalBuffer[currentBatchIndex][i]);
    } else if (i >= 20) {
      currentFooter += String(signalBuffer[currentBatchIndex][i]);
    }
  }
  // Serial.printf("[ProcessSignal] Signal: %s, Header: %s, Footer: %s\n", currentSignal.c_str(), currentHeader.c_str(), currentFooter.c_str());  // 除錯資訊
  // 驗證頭部和尾部
  if (currentHeader != VALID_HEADER || currentFooter != VALID_FOOTER) {
    Serial.println("[ProcessSignal] Header or Footer Mismatch, Resetting State");  // 除錯資訊
    printDecodedResult(currentSignal, currentHeader, currentFooter, decodedNumber, decodedId);
    resetState();
    return;
  }
  // 檢查訊號是否穩定
  if (currentSignal != previousSignal) {
    previousSignal = currentSignal;
    stableSignalCounter = 0;
    Serial.println("[ProcessSignal] Signal Changed, Resetting Stability Counter");  // 除錯資訊
    // printDecodedResult(currentSignal, currentHeader, currentFooter, decodedNumber, decodedId);
  } else {
    stableSignalCounter++;
    // Serial.printf("[ProcessSignal] Signal Stable, Counter: %d\n", stableSignalCounter);  // 除錯資訊
    // printDecodedResult(currentSignal, currentHeader, currentFooter, decodedNumber, decodedId);
  }
  // 如果訊號穩定，解碼資料部分
  if (stableSignalCounter == (MAX_BATCH_COUNT - 1)) {
    stableSignalCounter = 0;
    decodedNumber = 0;
    for (int i = DATA_START_INDEX; i < DATA_END_INDEX; i++) {
      decodedNumber <<= 1;
      if (signalBuffer[currentBatchIndex][i] == 1) {
        decodedNumber |= 1;
      }
    }
    decodedId = currentId;
    nowStr = String(decodedNumber);
    // Serial.println("[ProcessSignal] Decoding Complete, Printing Result");  // 除錯資訊
    printDecodedResult(currentSignal, currentHeader, currentFooter, decodedNumber, decodedId);
  }
  // 更新批次索引
  currentBatchIndex++;
  if (currentBatchIndex >= MAX_BATCH_COUNT) {
    // Serial.println("[ProcessSignal] Batch Index Overflow, Resetting State");  // 除錯資訊
    resetState();
  }
}

// 重置狀態函數
void resetState() {
  currentSignalIndex = 0;
  currentBatchIndex = 0;
  isProcessingSignal = false;
  stableSignalCounter = 0;
  previousSignal = "";
  decodedNumber = 0;
  decodedId = "";
  // Serial.println("[ResetState] State Reset");  // 除錯資訊
}

// 輸出解碼結果函數
void printDecodedResult(String signal, String header, String footer, int number, String id) {
  // Serial.println("Decoded Result:");
  Serial.printf("Number: %d\n", number);
  // Serial.printf("Signal: %s\n", signal.c_str());
  // Serial.printf("Header: %s\n", header.c_str());
  // Serial.printf("Footer: %s\n", footer.c_str());
  // Serial.printf("ID: %s\n", id.c_str());
  // Serial.println("-----------------------------");
}

void ma_1ms_timer2() {
  if ((millis() - signalProcessingStartTime) >= 1) {
    signalProcessingStartTime = millis();
    if (isProcessingSignal) {
      int signalValue = digitalRead(SRV_P34);
      signalBuffer[currentBatchIndex][currentSignalIndex] = signalValue;  // 應為0 (28-25=3個)
      currentSignalIndex++;
      // Serial.printf("[Timer2] Signal Index: %d, Value: %d\n", currentSignalIndex, signalValue);  // 除錯資訊
      if (currentSignalIndex >= (SIGNAL_LENGTH + 3)) {
        isProcessingSignal = false;
        currentSignalIndex = 0;
        processSignal();
        // Serial.println("[Timer2] Signal Processing Completed");  // 除錯資訊
      }
    }
  }
}

void ma_1ms_timer() {
  if ((millis() - delayStart) >= 1) {
    delayStart = millis();
    last500msTick++;
    last100msTick++;
    // Serial.printf("[Timer] 500ms Counter: %d, 100ms Counter: %d\n", last500msTick, last100msTick);  // 除錯資訊
  }
}

void ma_led_500ms() {
  if (last500msTick > LLH) {
    last500msTick = 0;
    isLedOn = !isLedOn;
    digitalWrite(BLED, isLedOn ? HIGH : LOW);
    resetState();
    // Serial.printf("[LED] LED State: %d\n", isLedOn);  // 除錯資訊
  }
}

// 數字發送函數
void IRAM_ATTR sendCallerNumber(unsigned long currentMillis) {
  if (currentMillis - lastCheckNumber < CHECK_NUMBER_INTERVAL)
    return;
  lastCheckNumber = currentMillis;

  // nowStr = decodedNumber;
  // Serial.printf("X.");                                                             // 除錯資訊
  // Serial.printf("nowStr=%s\n", nowStr.c_str());  // 除錯資訊
  if (nowStr != sendStr) {  // 沒連線一樣傳送至buffer
    // Serial.printf("[SendCallerNumber] Sending Number: %s\n", nowStr.c_str());  // 除錯資訊
    client_send(nowStr);
    sendStr = nowStr;
    nowStrDemo = nowStr;
    onMessage_time = currentMillis;  // 重置 onMessage 計時器
  }
}

#else  // not USE_KEYBOARD_SIGNAL



void IRAM_ATTR handleInterrupt_xxx() {
  // currentMillis = millis();
  InterruptCount += 1;
  if (!setup_finish)
    return;
  sendCallerNumber(millis());  // 持續監測數字變化

  // // 檢查是否超過100ms
  // if (currentMillis - lastScanDisplayTime >= CHECK_DISPLAY_INTERVAL) {
  //   lastScanDisplayTime = currentMillis;
  //   scanCallCount = 0;  // 重置計數器
  // }

  // // 只在計數器小於3時呼叫scanDisplayDigits
  // if (scanCallCount < SCAN_NUM) {
  //   has_interrupted = true;
  //   scanCallCount++;
  //   scanDisplayDigits();  // 數字掃描
  // }
  has_interrupted = true;
  scanDisplayDigits();  // 數字掃描
}


// 數字轉換函數
int convertToNumber() {
  const int pins[] = { LED_a, LED_b, LED_c, LED_d, LED_e, LED_f, LED_g };
  int values[7];

  for (int i = 0; i < 7; i++) {
    values[i] = digitalRead(pins[i]);
  }

  // 七段顯示器解碼邏輯
  struct {
    int pattern[7];
    int number;
  } patterns[] = {
    { { 0, 0, 0, 0, 0, 0, 1 }, 0 },
    { { 1, 1, 1, 1, 1, 1, 0 }, 0 },
    { { 0, 1, 1, 0, 0, 0, 0 }, 1 },
    { { 1, 1, 0, 1, 1, 0, 1 }, 2 },
    { { 1, 1, 1, 1, 0, 0, 1 }, 3 },
    { { 0, 1, 1, 0, 0, 1, 1 }, 4 },
    { { 1, 0, 1, 1, 0, 1, 1 }, 5 },
    { { 1, 0, 1, 1, 1, 1, 1 }, 6 },
    { { 1, 1, 1, 0, 0, 0, 0 }, 7 },
    { { 1, 1, 1, 1, 1, 1, 1 }, 8 },
    { { 1, 1, 1, 1, 0, 1, 1 }, 9 }
  };

  for (const auto& p : patterns) {
    bool match = true;
    for (int i = 0; i < 7; i++) {
      if (values[i] != p.pattern[i]) {
        match = false;
        break;
      }
    }
    if (match) return p.number;
  }

  return -1;
}

int int_count = 0;

// 數字顯示函數
void scanDisplayDigits() {
  const int enablePins[3] = { LED_1e, LED_2e, LED_3e };
  volatile int* numbers[3] = { &n1, &n2, &n3 };
  int_count++;

  scanDisplayCount += 1;
  for (int i = 0; i < 3; ++i) {
    int state = digitalRead(enablePins[i]);
    if (state == 1 && fe[i] == 0) {
      fe[i] = 1;
      *numbers[i] = convertToNumber();
      if (int_count == 100) {
        Serial.printf("numbers(%i)= %i\r", i, *numbers[i]);
        int_count = 0;
      }
    }
    fe[i] = state;
  }
}

// 數字發送函數
void sendCallerNumber(unsigned long currentMillis) {
  if (currentMillis - lastCheckNumber < CHECK_NUMBER_INTERVAL)
    return;
  lastCheckNumber = currentMillis;
  if (!has_interrupted) return;

  if (n1 >= 0 && n2 >= 0 && n3 >= 0) {
    nowStr = String(n1) + String(n2) + String(n3);
    matchCt = (nowStr == preStr) ? matchCt + 1 : 1;
    preStr = nowStr;

    if (matchCt >= 3 && (pn1 != n1 || pn2 != n2 || pn3 != n3)) {
      pn1 = n1;
      pn2 = n2;
      pn3 = n3;

      if (nowStr != sendStr) {  // 沒連線一樣傳送至buffer
        client_send(nowStr);

        sendStr = nowStr;
        nowStrDemo = nowStr;
        onMessage_time = currentMillis;  // 重置 onMessage 計時器
      }
      matchCt = 0;
    }
    n1 = n2 = n3 = -1;
  }
  has_interrupted = false;
}


#endif


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


void checkConnections() {
  // 檢查 WiFi 連接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi 未連接，嘗試重新連接...");  // !!!@@
    websocket_connect_time = millis();
    if (status.state != STATE_WIFI_CONNECTING) {
      bool result = false;
      if (wifiNetworks[currentNetwork].isValid) {
        result = connectToWiFi(wifiNetworks[currentNetwork].ssid, wifiNetworks[currentNetwork].password);
      }
      if (!result) {
        updateSystemState(STATE_INIT);
        currentNetwork = (currentNetwork + 1) % numNetworks;
        vTaskDelay(pdMS_TO_TICKS(1000));
      }
    }
    return;
  }

  // 檢查 WebSocket 連接
  webSocketClient.loop();
  if (!webSocketClient.isConnected()) {
    if (status.state != STATE_WEBSOCKET_CONNECTING) {
      // connectToWebSocket();
      // status.state = STATE_INIT;
      Serial.println("WebSocket 未連接，嘗試重新連接...");  // !!!@@
      webSocketClient.disconnect();
      setupWebSocket();
    }
    return;
  } else {
    websocket_connect_time = millis();
  }
}

// WiFi 連接函數
bool connectToWiFi(const char* ssid_in, const char* password_in) {
  ssid = ssid_in;
  password = password_in;

  // 先使用 DHCP 連接 Wi-Fi 以獲取 AP 的 LAN IP 地址
  updateSystemState(STATE_WIFI_CONNECTING);
  Serial.printf("\n***** Connecting to WiFi: %s *****\n", ssid.c_str());
  WiFi.begin(ssid.c_str(), password.c_str());

  unsigned long ConnectStartTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - ConnectStartTime > WIFI_TIMEOUT) {
      updateSystemState(STATE_ERROR, "WiFi connection_0 timeout");
      status.wifiAttempts++;
      return false;
    }
    Serial.print(".");
    delay(500);
  }
  websocket_connect_time = millis();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n\n***********************************\n");
    Serial.printf("Connected to WiFi: %s\n", ssid.c_str());
    Serial.printf("***********************************\n\n");

    apIP = WiFi.gatewayIP();  // 獲取 AP 的 LAN IP 地址
    LocalIP = WiFi.localIP();
    gateway = WiFi.gatewayIP();
    subnet = WiFi.subnetMask();
    dns = WiFi.dnsIP();

    Serial.println("\nWi-Fi connected successfully with DHCP!");
    Serial.print("AP LAN IP Address: ");
    Serial.println(apIP);
    Serial.println("STA Configured successfully");
    Serial.print("Local IP: ");
    Serial.println(LocalIP);
    Serial.print("Gateway IP: ");
    Serial.println(gateway);
    Serial.print("Subnet: ");
    Serial.println(subnet);
    Serial.print("DNS: ");
    Serial.println(dns);
    updateSystemState(STATE_WIFI_CONNECTED);

    // 將 AP 的 LAN IP 地址前三碼填入 ipList
    for (int i = 0; i < IP_COUNT; i++) {
      ipList[i] = IPAddress(apIP[0], apIP[1], apIP[2], ipList[i][3]);
    }

    loopCount = IP_COUNT;
    ipListPtr = ipList;  // 指向 ipList
    Serial.printf("剩餘堆積記憶體: %d\n", ESP.getFreeHeap());

    if (NullId == true) {
      if (NullId != true) {
        Serial.printf("IP 無須更換(%s)!\n", LocalIP.toString().c_str());
        return true;
      }
      Serial.printf("使用自訂IP.\n");
      for (currentIpIndex = 0; currentIpIndex < loopCount; currentIpIndex++) {
        IPAddress newlocalIP = ipListPtr[currentIpIndex];
        if ((LocalIP == newlocalIP) || (NullId != true)) {
          Serial.printf("IP 無須更換(%s).\n", LocalIP.toString().c_str());
          return true;
        }

        // 檢查 IP 是否可用
        if (!isIPAvailable(newlocalIP)) {
          Serial.println("IP 衝突: " + newlocalIP.toString() + " 已被使用，跳過！");
          continue;  // 跳過已被使用的 IP
        }

        // 斷開 Wi-Fi 連接，以便重新使用固定 IP 地址連接
        Serial.printf("需斷線重連\n");
        webSocketClient.disconnect();
        WiFi.disconnect(false);
        while (WiFi.status() != WL_DISCONNECTED) {
          delay(100);
        }
        delay(100);

        updateSystemState(STATE_WIFI_CONNECTING);

        // 配置靜態 IP
        gateway = apIP;
        subnet = IPAddress(255, 255, 255, 0);
        if (!WiFi.config(newlocalIP, gateway, subnet, dns)) {
          Serial.println("STA Failed to configure");
          return false;
        }

        Serial.printf("使用自訂IP完成\n");
        LocalIP = WiFi.localIP();
        gateway = WiFi.gatewayIP();
        subnet = WiFi.subnetMask();
        dns = WiFi.dnsIP();
        Serial.print("Local IP: ");
        Serial.println(LocalIP);
        Serial.print("Gateway IP: ");
        Serial.println(gateway);
        Serial.print("Subnet: ");
        Serial.println(subnet);
        Serial.print("DNS: ");
        Serial.println(dns);

        // 嘗試連接 Wi-Fi
        WiFi.begin(ssid.c_str(), password.c_str());
        Serial.printf("Connecting to WiFi_1: %s\n", ssid.c_str());

        ConnectStartTime = millis();
        while (WiFi.status() != WL_CONNECTED) {
          if (millis() - ConnectStartTime > WIFI_TIMEOUT) {
            updateSystemState(STATE_ERROR, "WiFi connection_1 timeout");
            status.wifiAttempts++;
            return false;
          }
          Serial.print(".");
          delay(500);
        }

        if (WiFi.status() == WL_CONNECTED) {
          Serial.println("\nWi-Fi connected successfully!");
          Serial.print("ESP32 IP Address: ");
          Serial.println(WiFi.localIP());
          useDhcp = false;  // 使用固定 IP 地址
          updateSystemState(STATE_WIFI_CONNECTED);
          return true;  // 連接成功，退出函數
        } else {
          Serial.println("\nFailed to connect to Wi-Fi with IP: " + newlocalIP.toString());
        }
      }

      // 如果所有 IP 地址都不可用，系統指定一個 IP 地址
      Serial.println("All fixed IP addresses failed. Using DHCP.");
      WiFi.begin(ssid.c_str(), password.c_str());
      while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
      }
      Serial.println("\nWi-Fi connected successfully with DHCP!");
      Serial.print("ESP32 IP Address: ");
      Serial.println(WiFi.localIP());
      useDhcp = true;  // 使用 DHCP
      return true;
    }
  } else {
    Serial.printf("\nFailed to connect to WiFi: %s !\n", ssid.c_str());
    return false;
  }
}

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

  // STATE_WEBSOCKET_CONNECTING, 3
  ledConfigs[STATE_WEBSOCKET_CONNECTING].red = { true, true, 750, 750, 0 };     // 紅燈慢速閃爍
  ledConfigs[STATE_WEBSOCKET_CONNECTING].green = { false, true, 750, 750, 0 };  // 綠燈慢速閃爍

  // STATE_WEBSOCKET_CONNECTED, 4
  ledConfigs[STATE_WEBSOCKET_CONNECTED].red = { false, false, 0, 0, 0 };   // 紅燈持續滅
  ledConfigs[STATE_WEBSOCKET_CONNECTED].green = { true, false, 0, 0, 0 };  // 綠燈持續亮

  // STATE_ERROR, 5
  ledConfigs[STATE_ERROR].red = { false, false, 0, 0, 0 };    // 紅燈滅
  ledConfigs[STATE_ERROR].green = { false, false, 0, 0, 0 };  // 綠燈滅

  // STATE_DEMO, 6
  ledConfigs[STATE_DEMO].red = { false, false, 0, 0, 0 };       // 紅燈持續滅
  ledConfigs[STATE_DEMO].green = { true, true, 1900, 100, 0 };  // 綠燈慢速閃爍

  // STATE_TRANS, 7
  ledConfigs[STATE_TRANS].red = { true, true, 100, 10000, 0 };  // 紅燈快速亮一下
  ledConfigs[STATE_TRANS].green = { true, false, 0, 0, 0 };     // 綠燈持續亮
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
  // void updateSystemState(SystemState newState, const String& error = "") {
  // 打印狀態
  Serial.printf("S%d ", newState);
  if (error.length() > 0) {
    status.lastError = error;
    // Serial.println("\nError: " + error);
    Serial.println(error);
  }
  if (newState == STATE_ERROR) {
    // Serial.printf(" Pass! ");
    return;
  }
  status.state = newState;
  status.lastStateChange = currentMillis;
  // 更新 LED 狀態
  updateLEDState();
}

// LED 閃動函數
// LED_RED:33, LED_GREEN:32
// LOW LED亮
void blinkLED(TimerHandle_t xTimer) {
  currentMillis = millis();
  LedState* ledState = (LedState*)pvTimerGetTimerID(xTimer);

  int LED = (ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN);
  if (ledState->isBlinking) {
    if (ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->onTime)) {
      ledState->isOn = false;
      ledState->lastToggle = currentMillis;
      digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, HIGH);  // LED滅
      // Serial.printf("LED(%d)滅! ", LED);
    } else if (!ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->offTime)) {
      ledState->isOn = true;
      ledState->lastToggle = currentMillis;
      digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, LOW);  // LED亮
      // Serial.printf("LED(%d)亮! ", LED);
    }
  } else {  // 不閃爍時用
    // digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, ledState->isOn ? HIGH:LOW );
    int status = (ledState->isOn ? LOW : HIGH);
    digitalWrite(LED, status);
    // Serial.printf("LED(%d)切換%d! ", LED, status);
  }
}

// WebSocket 事件回調函數
// void onEventsCallback(WebsocketsEvent event, String data) {
//   if (event == WebsocketsEvent::ConnectionOpened) {
//     Serial.println("Event:Connection Opened");
//   } else if (event == WebsocketsEvent::ConnectionClosed) {
//     Serial.println("\nEvent:Connection Closed");
//   } else if (event == WebsocketsEvent::GotPing) {
//     Serial.print("I");
//     client.pong();
//     Serial.print("o ");
//   } else if (event == WebsocketsEvent::GotPong) {
//     Serial.print("O");
//     ping_EX_no_reply_count = 0;
//   }
// }

// WebSocket 消息回調函數
// void onMessageCallback(WebsocketsMessage message) {
//   onMessage_time = 0;
//   if (message.data() != "pong") {
//     if (demoState) {
//       updateSystemState(STATE_DEMO);
//     } else {
//       updateSystemState(STATE_WEBSOCKET_CONNECTED);
//     }
//     Serial.println("Received: " + message.data());
//     if (message.data().startsWith("OK,")) {
//       waitingResponse = false;
//     }
//   } else Serial.print("B ");  // Ping_EX Back.
// }

// WebSocket 消息回調函數
void onMessageCallback(String message) {
  onMessage_time = 0;
  if (message != "pong") {
    if (demoState) {
      updateSystemState(STATE_DEMO);
    } else {
      updateSystemState(STATE_WEBSOCKET_CONNECTED);
    }
    Serial.println("Received: " + message);
    if (message.startsWith("OK,")) {
      waitingResponse = false;
    }
  } else Serial.print("B ");  // Ping_EX Back.
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

    // 等待連接成功或超時
    unsigned long startTime = millis();
    while (millis() - startTime < 10000) {  // 5 秒超時
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
      vTaskDelay(pdMS_TO_TICKS(100));  // n + 1000, Fail: 1000,500,300    OK:100,200
    }

    Serial.println("[狀態] 連接失敗，嘗試下一個伺服器...");
    webSocketClient.disconnect();  // 斷開當前連接
    updateSystemState(STATE_WEBSOCKET_CONNECTING, "連接失敗，嘗試下一個伺服器...");
  }
  Serial.println("[錯誤] 所有伺服器連接失敗！");
  updateSystemState(STATE_WIFI_CONNECTED, "所有伺服器連接失敗！");
}

// WebSocket 事件處理
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("WebSocket Disconnected! (%lu)\n", (millis() - websocket_connect_time) / 1000);
      updateSystemState(STATE_ERROR, "WebSocket Disconnected");
      if ((millis() - websocket_connect_time) >= MAX_WEBS_RTY_TIME) {
        Serial.printf("\n斷線重連!\n");
        websocket_connect_time = millis();
        currentNetwork = (currentNetwork + 1) % numNetworks;  // 先試下一組AP
        webSocketClient.disconnect();
        WiFi.disconnect(true);
      }
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected!");
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
      // webSocketClient.sendTXT("pong");
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
    webSocketClient.sendTXT(message);
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

// 打印任務狀態
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

    // 打印任務信息
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
    // 如果百分比大於等於 1，則打印該行並增加計數
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


// 檢查系統狀態
void check_system(unsigned long lastCheckTime, unsigned long currentMillis) {
  calculateCPULoad(lastCheckTime, currentMillis);
  checkMemory();
  Serial.printf("InterruptCount:%lu, scanDisplayCount:%lu \n", InterruptCount, scanDisplayCount);
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
void handleRoot() {
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
  Serial.println("handleRoot");
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
  String response1 = "      ID: " + savedData1;
  server.send(200, "text/plain; charset=UTF-8", response);
  Serial.println(response1);
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
  buffer[head] = value;
  head = (head + 1) % BUFFER_SIZE;
  if (head == tail) {
    tail = (tail + 1) % BUFFER_SIZE;  // Buffer 已滿，覆寫舊資料
    Serial.println("Function A: Buffer 已滿，覆寫舊資料");
  }
}

// 從緩衝區彈出資料
bool buffer_pop(int& value) {
  if (head == tail) {
    return false;  // Buffer 為空
  }
  // Serial.printf("buffer_pop(%d)\n", value);
  value = buffer[tail];
  tail = (tail + 1) % BUFFER_SIZE;
  return true;
}

void sendBufferedData() {
  // 只有在WiFi和WebSocket都連接時才嘗試發送數據
  if (WiFi.status() == WL_CONNECTED && webSocketClient.isConnected() && !waitingResponse) {
    int value;
    if (retryMode) {
      value = retryValue;
      sendWebSocketMessage(value);
      retryMode = false;  // 防止卡在重試模式
    } else if (buffer_pop(value)) {
      // vTaskDelay(pdMS_TO_TICKS(500));  // 或使用 delay
      sendWebSocketMessage(value);
      vTaskDelay(pdMS_TO_TICKS(500));  // 或使用 delay
    }
  }
  checkResponse();
}

// 發送 WebSocket 消息
void sendWebSocketMessage(int value) {
  String message = "";
  if (!new_connect) {
    message = String(Caller_Number) + "," + String(value);
  } else {
    new_connect = false;
    char bssid[18];
    sprintf(bssid, "%02X:%02X:%02X:%02X:%02X:%02X", WiFi.BSSID()[0], WiFi.BSSID()[1], WiFi.BSSID()[2], WiFi.BSSID()[3], WiFi.BSSID()[4], WiFi.BSSID()[5]);
    message = String(Caller_Number) + "," + String(value) + ",INFO: 'SSID:" + String(WiFi.SSID()) + " ; RSSI:" + String(WiFi.RSSI()) + "dBm" + " ; BSSID:" + String(bssid) + " ; Ver:" + String(Version) + "'";
    // updateSystemState(STATE_TRANS);
    vTaskDelay(pdMS_TO_TICKS(200));  // 或使用 delay
    // bool success = webSocketClient.sendTXT(message);
    // vTaskDelay(pdMS_TO_TICKS(200));  // 或使用 delay
    // if (success) {
    //   updateSystemState(STATE_WEBSOCKET_CONNECTED);
    //   Serial.print("傳送：");
    //   Serial.println(message);
    // } else {
    //   updateSystemState(STATE_WEBSOCKET_CONNECTING);
    //   Serial.printf("傳送(%s)失敗，WebSocket 可能未連接", message.c_str());
    // }
    // return;
  }
  updateSystemState(STATE_TRANS);
  bool success = webSocketClient.sendTXT(message);

  if (success) {
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
    sendTime = millis();
    waitingResponse = true;
    retryMode = false;
    Serial.print("傳送：");
    Serial.println(message);
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
  if (waitingResponse) {
    if (millis() - sendTime >= retryTimeout * 1000) {
      waitingResponse = false;
      retryMode = true;
      retryValue = buffer[(tail == 0) ? BUFFER_SIZE - 1 : tail - 1];
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
      client_send(nowStrDemo);

      onMessage_time = currentMillis;  // 重置 onMessage 計時器
    }
    lastUpdateTime = currentMillis;
    nextUpdateInterval = random(MIN_INTERVAL, MAX_INTERVAL + 1);
  }
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






// ================================================================



// #include <ArduinoWebsockets.h>
// #include <Arduino.h>
// #include <WiFi.h>

#define LED_a 17
#define LED_b 5
#define LED_c 18
#define LED_d 19
#define LED_e 21
#define LED_f 22
#define LED_g 23

#define LED_1e 16
#define LED_2e 4
#define LED_3e 15  //0 LOW(x)

#define GLED 32
#define RLED 33


#define BLED 2
#define LLH 500
// const char ssid[]= "TEST";
// const char pwd[]= "TEST";
// const char ssid[] = "CMB00000";
// const char pwd[] = "88888888";
// const char websockets_server_host[] = "0.0.0.0";  // //Enter server adress
// const uint16_t websockets_server_port = 8000;     // Enter server port
unsigned long delayStart = 0;  // the time the delay started
unsigned long ma_500ms_counter = 0;
unsigned long ma_100ms_counter = 0;
byte led_light_en = 0;
byte reCnt_en = 0;

// using namespace websockets;
// WebsocketsClient client;

unsigned long ma_reboot_counter = 0;
unsigned long ma_counter = 0;
unsigned long ma_l1 = 20;
unsigned long sendCt = 0;

// int fe[3] = { 0 };
// int n1 = -1, n2 = -1, n3 = -1;
int cn1 = -1, cn2 = -1, cn3 = -1;
// int pn1 = -2, pn2 = -2, pn3 = -2;

volatile bool newDigitEvent = false;

// hw_timer_t* timer0;
// String preStr = "";
// String nowStr = "";
// String sendStr = "";
// int matchCt = 0;
int numCk = 0;

int Le[3] = { 0 };
int Le_ok[3] = { 0 };
byte le_i = 0;
byte le_s = 0;

int i_count = 0;

void IRAM_ATTR isr_handler() {
  delayMicroseconds(500);
  
  int a1 = digitalRead(LED_1e);
  int a2 = digitalRead(LED_2e);
  int a3 = digitalRead(LED_3e);

  Le[0] = 0;
  Le[1] = 0;
  Le[2] = 0;

  if (a1 == 1 && a2 == 0 && a3 == 0)
    Le[0] = 1;
  else if (a2 == 1 && a1 == 0 && a3 == 0)
    Le[1] = 1;
  else if (a3 == 1 && a2 == 0 && a1 == 0)
    Le[2] = 1;
  i_count++;
  if (i_count >= 100) {
    Serial.printf("I_");
    i_count = 0;
  }
}

// void onEventsCallback(WebsocketsEvent event, String data) {
//     if(event == WebsocketsEvent::ConnectionOpened) {
//         Serial.println("Connnection Opened");
//         reCnt_en=0;
//     }
//     else if(event == WebsocketsEvent::ConnectionClosed) {
//       Serial.println("Connnection Closed");
//       reCnt_en=1;
//     }

// }

void setup_1() {
  pinMode(RLED, OUTPUT);
  pinMode(GLED, OUTPUT);

  pinMode(BLED, OUTPUT);
  pinMode(LED_a, INPUT);
  pinMode(LED_b, INPUT);
  pinMode(LED_c, INPUT);
  pinMode(LED_d, INPUT);
  pinMode(LED_e, INPUT);
  pinMode(LED_f, INPUT);
  pinMode(LED_g, INPUT);
  pinMode(LED_1e, INPUT);
  pinMode(LED_2e, INPUT);
  pinMode(LED_3e, INPUT);
  digitalWrite(BLED, LOW);
  digitalWrite(RLED, HIGH);
  digitalWrite(GLED, HIGH);

  attachInterrupt(digitalPinToInterrupt(LED_1e), isr_handler, RISING);
  attachInterrupt(digitalPinToInterrupt(LED_2e), isr_handler, RISING);
  attachInterrupt(digitalPinToInterrupt(LED_3e), isr_handler, RISING);

  //   //
  //   Serial.begin(115200);
  //   Serial.print("\nOK\n");
  //   // Connect to wifi
  //  WiFi.mode(WIFI_STA); //設置WiFi模式
  //  WiFi.begin(ssid, pwd);
  //  Serial.print("WiFi connecting");
  //  //當WiFi連線時會回傳WL_CONNECTED，因此跳出迴圈時代表已成功連線
  //  while(WiFi.status()!=WL_CONNECTED){
  //    Serial.print(".");
  //    delay(500);
  //    ma_reboot_counter++;
  //    if (ma_reboot_counter>20)
  //    {
  //      Serial.println("wifi_reboot");
  //      ESP.restart();
  //    }
  //  }
  //  Serial.print("\nIP address: ");
  //  Serial.println(WiFi.localIP());
  //  Serial.println("WiFi status:");
  //  Serial.println("Connected to Wifi, Connecting to server.");

  //   // try to connect to Websockets server
  //  bool connected = client.connect(websockets_server_host, websockets_server_port, "");
  //  if(connected) {
  //      Serial.println("Server Connected!");
  //      reCnt_en=0;
  //  } else {
  //      Serial.println("Server Not Connected!");
  //      reCnt_en=1;
  //  }

  //  // run callback when messages are received
  //  client.onMessage([&](WebsocketsMessage message){
  //      Serial.print(message.data()+" ");
  //  });

  //  client.onEvent(onEventsCallback);
}

// void serverReconnect() {
//   if (reCnt_en == 1) {
//     if (ma_500ms_counter > 250) {
//       ma_500ms_counter = 0;
//       client.connect(websockets_server_host, websockets_server_port, "/");

//       if (led_light_en == 0) {
//         digitalWrite(BLED, HIGH);
//         led_light_en = 1;
//       } else {
//         digitalWrite(BLED, LOW);
//         led_light_en = 0;
//       }
//     }
//   }
// }

int numberConverter() {
  int aa = digitalRead(LED_a);
  int bb = digitalRead(LED_b);
  int cc = digitalRead(LED_c);
  int dd = digitalRead(LED_d);
  int ee = digitalRead(LED_e);
  int ff = digitalRead(LED_f);
  int gg = digitalRead(LED_g);

  if (aa == 0 && bb == 0 && cc == 0 && dd == 0 && ee == 0 && ff == 0 && gg == 1) return 0;
  else if (aa == 1 && bb == 0 && cc == 0 && dd == 1 && ee == 1 && ff == 1 && gg == 1) return 1;
  else if (aa == 0 && bb == 0 && cc == 1 && dd == 0 && ee == 0 && ff == 1 && gg == 0) return 2;
  else if (aa == 0 && bb == 0 && cc == 0 && dd == 0 && ee == 1 && ff == 1 && gg == 0) return 3;
  else if (aa == 1 && bb == 0 && cc == 0 && dd == 1 && ee == 1 && ff == 0 && gg == 0) return 4;
  else if (aa == 0 && bb == 1 && cc == 0 && dd == 0 && ee == 1 && ff == 0 && gg == 0) return 5;
  else if (aa == 0 && bb == 1 && cc == 0 && dd == 0 && ee == 0 && ff == 0 && gg == 0) return 6;
  else if (aa == 0 && bb == 0 && cc == 0 && dd == 1 && ee == 1 && ff == 1 && gg == 1) return 7;
  else if (aa == 0 && bb == 0 && cc == 0 && dd == 0 && ee == 0 && ff == 0 && gg == 0) return 8;
  else if (aa == 0 && bb == 0 && cc == 0 && dd == 0 && ee == 1 && ff == 0 && gg == 0) return 9;
  else return -1;

  // if      (aa==1 && bb==1 && cc==1 && dd==1 && ee==1 && ff==1 && gg==0)        return 0;
  // else if (aa==0 && bb==1 && cc==1 && dd==0 && ee==0 && ff==0 && gg==0)        return 1;
  // else if (aa==1 && bb==1 && cc==0 && dd==1 && ee==1 && ff==0 && gg==1)        return 2;
  // else if (aa==1 && bb==1 && cc==1 && dd==1 && ee==0 && ff==0 && gg==1)        return 3;
  // else if (aa==0 && bb==1 && cc==1 && dd==0 && ee==0 && ff==1 && gg==1)        return 4;
  // else if (aa==1 && bb==0 && cc==1 && dd==1 && ee==0 && ff==1 && gg==1)        return 5;
  // else if (aa==1 && bb==0 && cc==1 && dd==1 && ee==1 && ff==1 && gg==1)        return 6;
  // else if (aa==1 && bb==1 && cc==1 && dd==0 && ee==0 && ff==0 && gg==0)        return 7;
  // else if (aa==1 && bb==1 && cc==1 && dd==1 && ee==1 && ff==1 && gg==1)        return 8;
  // else if (aa==1 && bb==1 && cc==1 && dd==1 && ee==0 && ff==1 && gg==1)        return 9;
  // else                                                                         return -1;
}

void numberGetter2() {
  Serial.printf("G_");
  switch (le_s) {
    case 0:
      if (Le[0] == 1) {
        le_s = 10;
        le_i = 0;
      } else if (Le[1] == 1) {
        le_s = 20;
        le_i = 0;
      } else if (Le[2] == 1) {
        le_s = 30;
        le_i = 0;
      }
      break;
    case 10:
      if (le_i > 1) {
        Le_ok[0] = numberConverter();
        le_s = 0;
        Le[0] = 0;
        Le[1] = 0;
        Le[2] = 0;
        numCk++;
      }
      break;
    case 20:
      if (le_i > 1) {
        Le_ok[1] = numberConverter();
        le_s = 0;
        Le[0] = 0;
        Le[1] = 0;
        Le[2] = 0;
        numCk++;
      }
      break;
    case 30:
      if (le_i > 1) {
        Le_ok[2] = numberConverter();
        le_s = 0;
        Le[0] = 0;
        Le[1] = 0;
        Le[2] = 0;
        numCk++;
      }
      break;
  }
}

void numberSend2() {
  Serial.printf("S_");

  if (numCk >= 3) {
    numCk = 0;
    n1 = Le_ok[0];
    n2 = Le_ok[1];
    n3 = Le_ok[2];

    if (n1 >= 0 && n2 >= 0 && n3 >= 0) {
      nowStr = String(n1) + String(n2) + String(n3);
      if (nowStr == preStr) {
        matchCt++;
      } else matchCt = 1;

      preStr = nowStr;

      if (matchCt >= 3) {
        if (pn1 != n1 || pn2 != n2 || pn3 != n3) {
          pn1 = n1;
          pn2 = n2;
          pn3 = n3;
          Serial.println("send: " + nowStr + ",");

          // if(nowStr!=sendStr && client.available()){
          // client.send(nowStr+ ",");
          sendStr = nowStr;
          // }
          matchCt = 0;
        }
      }
      n1 = n2 = n3 = -1;  //reset n
    }
  }
}




void ma_1ms_timer() {
  if ((millis() - delayStart) >= 1) {
    delayStart = millis();
    ma_500ms_counter++;
    ma_100ms_counter++;
    le_i++;
  }
}




// void ma_led_500ms() {
//   serverReconnect();

//   if (ma_500ms_counter > LLH) {
//     ma_500ms_counter = 0;
//     if (led_light_en == 0) {
//       digitalWrite(BLED, HIGH);
//       digitalWrite(RLED, LOW);
//       digitalWrite(GLED, HIGH);
//       led_light_en = 1;
//     } else {
//       digitalWrite(BLED, LOW);
//       digitalWrite(RLED, HIGH);
//       digitalWrite(GLED, LOW);
//       led_light_en = 0;
//     }
//     //Serial.printf("%d %d %d \n",Le_ok[0],Le_ok[1],Le_ok[2]);

//     if (WiFi.status() != WL_CONNECTED) {
//       Serial.println("wifi GG");
//       Serial.println("reboot");
//       ESP.restart();
//     }

//     // let the websockets client check for incoming messages
//     if (client.available()) {
//       client.poll();
//       //  sendCt++;
//       //  client.send(String(sendCt));
//     }
//   }
// }

// void loop()
// {
//   ma_1ms_timer();
//   ma_led_500ms();
//   numberGetter2();
//   numberSend2();
// }
