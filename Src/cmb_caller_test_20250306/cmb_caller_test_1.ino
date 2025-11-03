
#include <ArduinoWebsockets.h>
#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoOTA.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_freertos_hooks.h"
#include "sdkconfig.h"

#include <WebServer.h>
#include <Preferences.h>
#include <ESPping.h>

#include "credentials.h"

String Version = "2025030618";

extern void vTaskGetRunTimeStats(char* pcWriteBuffer);

// bool local_test = false;
// 網路相關定義
#ifndef LOCAL_TEST
const char* websockets_server_host = "35.187.148.66";  // VM
const uint16_t websockets_server_port = 8765;          // VM
#else
const char* websockets_server_host = "192.168.1.10";  // Windows Local
const uint16_t websockets_server_port = 38000;        // Windows Local
#endif

String Caller_Number = "00000";  //

// LED 定義
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

#define LED_RED 33
#define LED_GREEN 32
// #define LED_BLUE 2

const int numNetworks = sizeof(wifiNetworks) / sizeof(wifiNetworks[0]);

// 計時器和網路相關
const long WIFI_TIMEOUT = 7000;          // WiFi 連接超時時間 (原10000毫秒)
const long WS_TIMEOUT = 5000;            // WebSocket 連接超時時間 (5000)
const long STATE_UPDATE_INTERVAL = 500;  // 狀態更新間隔 (500)
const long PING_INTERVAL = 30000;        // Ping 間隔 (30000)
// const long PONG_INTERVAL = 10000;        // Pong 間隔 (10000)
const long ON_MESSAGE_TIMEOUT = 10000;    // onMessage 超時時間 (10 秒)
const long printInterval = (10 * 60000);  // 設定列印系統訊息時間間隔為10分鐘 (600000ms) !!!@@@
const long CHECK_DISPLAY_INTERVAL = 100;  // Interrupt 有效取樣間隔 (100ms)
const long SCAN_NUM = 3;                  // Interrupt 取樣次數 (3 or 6)
const long CHECK_NUMBER_INTERVAL = 100;   // 數值變動取樣間隔 (100ms)
// 系統變數
unsigned long lastPING = 0;
unsigned long delayStart = 0;
int currentNetwork = 0;
volatile unsigned long onMessage_time = 0;  // 宣告 onMessage_time 為全域變數
// unsigned long lastPrintTime = millis() - printInterval;  // 儲存上次印出系統訊息的時間
unsigned long lastPrintTime = millis();  // 儲存上次印出系統訊息的時間
unsigned long lastCheckNumber = 0;
volatile unsigned long InterruptCount = 0;
volatile unsigned long scanDisplayCount = 0;
volatile unsigned long currentMillis = millis();
volatile unsigned long lastScanDisplayTime = 0;
volatile int scanCallCount = 0;
// Caller 相關定義
const char Caller_Prefix[] = "CMB";
char Caller_SSID[sizeof(Caller_Prefix) + sizeof(Caller_Number) - 1];
// 變數用於儲存 CPU 負載量
volatile uint32_t idleCount[portNUM_PROCESSORS] = { 0 };
volatile uint32_t idleCountLast[portNUM_PROCESSORS] = { 0 };


// 數字顯示相關
int fe[3] = { 0 };
volatile int n1 = -1, n2 = -1, n3 = -1;
int pn1 = -2, pn2 = -2, pn3 = -2;
volatile bool has_interrupted = false;
hw_timer_t* timer0;
String preStr = "1";
String nowStr = "1";
String nowStrDemo = "1";
String sendStr = "000";
int matchCt = 0;

using namespace websockets;
WebsocketsClient client;


// DEMO
const int BUTTON_PIN = 0;                  // IO0 按鈕
const int LED_PIN = 32;                    // LED 腳位
const long CHECK_IO0_INTERVAL = 100;       // 按鈕檢測間隔 (100ms)
const long MULTI_CLICK_INTERVAL = 500;     // 連續按壓有效時間
const int CLICK_COUNT_TARGET = 2;          // 目標按壓次數
const unsigned long MIN_INTERVAL = 30000;  // 最小更新間隔 (30sec)
const unsigned long MAX_INTERVAL = 90000;  // 最大更新間隔 (90sec)
const int MIN_CHANGE = -1;                 // 最小變化值
const int MAX_CHANGE = 2;                  // 最大變化值
const int MIN_VALUE = 1;                   // 最小允許值
const int MAX_VALUE = 999;                 // 最大允許值

// 狀態變數
// bool ledState = true;    // LED 狀態
bool demoState = false;  // Demo 模式狀態
int clickCount = 0;      // 按鈕計數
// int Caller_num;          // 呼叫號碼

// 時間追蹤
unsigned long lastCheckIO0 = 0;     // 上次按鈕檢查時間
unsigned long lastButtonPress = 0;  // 上次按鈕按下時間
unsigned long lastUpdateTime = 0;   // 上次更新時間
unsigned long nextUpdateInterval;   // 下次更新間隔
bool lastButtonState = HIGH;        // 上次按鈕狀態


// 系統狀態枚舉
enum SystemState {
  STATE_INIT,
  STATE_WIFI_CONNECTING,
  STATE_WIFI_CONNECTED,
  STATE_WEBSOCKET_CONNECTING,
  STATE_WEBSOCKET_CONNECTED,
  STATE_ERROR,
  STATE_DEMO,
  STATE_TRANS,
  STATE_COUNT
};

// LED 控制結構
struct LedState {
  bool isOn;                 // LED 當前狀態
  bool isBlinking;           // 是否閃爍
  unsigned long onTime;      // 亮持續時間 (ms)
  unsigned long offTime;     // 滅持續時間 (ms)
  unsigned long lastToggle;  // 最後切換時間
};

// 系統狀態結構
struct Status {
  SystemState state;
  unsigned long lastStateChange;
  String lastError;
  int wifiAttempts;
  int websocketAttempts;
  String currentSSID;
} status;

// LED 配置
struct LedConfig {
  LedState red;
  LedState green;
} ledConfigs[STATE_COUNT];

// unsigned long currentMillis = 0;
TimerHandle_t redTimer;
TimerHandle_t greenTimer;

// IP 地址列表
int xxx = 0;
IPAddress ipList[] = {
  // IPAddress(xxx, xxx, xxx, 148),
  // IPAddress(xxx, xxx, xxx, 138),
  IPAddress(xxx, xxx, xxx, 128),
  IPAddress(xxx, xxx, xxx, 118),
  IPAddress(xxx, xxx, xxx, 108)
};
const int IP_COUNT = sizeof(ipList) / sizeof(ipList[0]);

// IPAddress ipList1[] = {
//   // IPAddress(xxx, xxx, xxx, 198),
//   // IPAddress(xxx, xxx, xxx, 188),
//   IPAddress(xxx, xxx, xxx, 178),
//   IPAddress(xxx, xxx, xxx, 168),
//   IPAddress(xxx, xxx, xxx, 158)
// };
// const int IP_COUNT1 = sizeof(ipList1) / sizeof(ipList1[0]);

// IPAddress ipList2[] = {
//   IPAddress(xxx, xxx, xxx, 248),
//   IPAddress(xxx, xxx, xxx, 238),
//   IPAddress(xxx, xxx, xxx, 228),
//   IPAddress(xxx, xxx, xxx, 218),
//   IPAddress(xxx, xxx, xxx, 208)
// };
// const int IP_COUNT2 = sizeof(ipList2) / sizeof(ipList2[0]);

int currentIpIndex = 0;
int loopCount;         // 用於存儲循環次數
IPAddress* ipListPtr;  // 用於指向選擇的 IP 列表
bool useDhcp = false;  // 標記是否使用了 DHCP

IPAddress apIP;
IPAddress LocalIP;
IPAddress gateway;
IPAddress subnet;
IPAddress dns;

// WebServer instance
WebServer server(80);
Preferences preferences;

String savedData1 = "";
String savedData2 = "";
String savedData3 = "";
volatile bool NullId = false;

// 記錄開機時間和失效時間
unsigned long startTime = 0;            // 記錄開機時間
const unsigned long expireMinutes = 5;  // 設定失效時間（單位：分鐘）
unsigned long expireTime = expireMinutes * 60 * 1000;

// 轉換 IP 為字串
String ipToString(IPAddress ip) {
  // return String(ip[0]) + "." + String(ip[1]) + "." + String(ip[2]) + "." + String(ip[3]);
  return ip.toString().c_str();
}

const int RETRY_COUNT = 1;
bool Maint_mode = true;

bool isIPAvailable(IPAddress ip) {
  bool available = true;
  // Serial.printf("isIPAvailable( %s )\n", ip.toString().c_str());
  // 方法1: TCP連接測試
  // WiFiClient client;
  // client.setTimeout(TIMEOUT_MS);

  // if (client.connect(ip, 80)) {
  //   available = false;  // 如果能建立連接，表示IP在使用中
  //   client.stop();
  //   // Serial.printf("TCP測試: IP %s 已被使用\n", ip.toString().c_str());
  //   return available;
  // }

  // 方法2: 使用Ping測試
  int successCount = 0;

  for (int i = 0; i < RETRY_COUNT; i++) {
    if (Ping.ping(ip, 1)) {  // 發送1個ping包
      successCount++;
      // Serial.printf("Ping測試(%s) %d: 成功\n", ip.toString().c_str(), i + 1);
    } else {
      // Serial.printf("Ping測試(%s) %d: 失敗\n", ip.toString().c_str(), i + 1);
    }
    delay(100);  // 短暫延遲避免過度頻繁
  }

  // 如果超過一半的ping成功，認為IP在使用中
  if (successCount > RETRY_COUNT / 2) {
    available = false;
  }

  // Serial.printf("IP %s 最終狀態: %s (成功次數: %d/%d)\n",
  //               ip.toString().c_str(),
  //               available ? "可用" : "已被使用",
  //               successCount,
  //               RETRY_COUNT);

  return available;
}

void updateSystemState(SystemState newState, const String& error = "");

// WiFi 連接函數
// bool connecTtoWiFi(const char* ssid, const char* pwd) {
//   updateSystemState(STATE_WIFI_CONNECTING);
//   Serial.printf("Connecting to WiFi: %s\n", ssid);

//   status.currentSSID = ssid;
//   WiFi.begin(ssid, pwd);

//   unsigned long ConnectStartTime = millis();
//   while (WiFi.status() != WL_CONNECTED) {
//     if (millis() - ConnectStartTime > WIFI_TIMEOUT) {
//       updateSystemState(STATE_ERROR, "WiFi connection timeout");
//       status.wifiAttempts++;
//       return false;
//     }
//     updateSystemState(STATE_WIFI_CONNECTING);
//     delay(100);  // LED 閃動
//   }
//   Serial.printf("\nConnected to WiFi. SSID: %s, IP: %s\n", ssid, WiFi.localIP().toString().c_str());
//   updateSystemState(STATE_WIFI_CONNECTED);
//   status.wifiAttempts = 0;
//   return true;
// }


// const char* ssid;
// const char* password;
String ssid;
String password;

bool connectToWiFi_new(const char* ssid_in, const char* password_in) {
  ssid = ssid_in;
  password = password_in;

  // 先使用 DHCP 連接 Wi-Fi 以獲取 AP 的 LAN IP 地址
  updateSystemState(STATE_WIFI_CONNECTING);
  Serial.printf("Connecting to WiFi: %s\n", ssid.c_str());
  WiFi.begin(ssid.c_str(), password.c_str());

  // int attempts = 0;
  // connecTtoWiFi
  // while (WiFi.status() != WL_CONNECTED && attempts < 20) {
  //   //
  //   delay(500);
  //   Serial.print(".");
  //   attempts++;
  // }
  unsigned long ConnectStartTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - ConnectStartTime > WIFI_TIMEOUT) {
      updateSystemState(STATE_ERROR, "WiFi connection_0 timeout");
      status.wifiAttempts++;
      return false;
    }
    Serial.print(".");
    // updateSystemState(STATE_WIFI_CONNECTING);
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
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
    // for (int i = 0; i < IP_COUNT1; i++) {
    //   ipList1[i] = IPAddress(apIP[0], apIP[1], apIP[2], ipList1[i][3]);
    // }
    // for (int i = 0; i < IP_COUNT2; i++) {
    //   ipList2[i] = IPAddress(apIP[0], apIP[1], apIP[2], ipList2[i][3]);
    // }

    loopCount = IP_COUNT;
    ipListPtr = ipList;  // 指向 ipList
    Serial.printf("剩餘堆積記憶體: %d\n", ESP.getFreeHeap());
    // 根據條件選擇循環範圍和 IP 列表
    Serial.printf("NullId 地址: %p, 值: %i\n", &NullId, NullId);
    if (NullId == true) {
      Serial.printf("NullId 地址: %p, 值: %i\n", &NullId, NullId);
      if (NullId != true) {
        Serial.printf("NullId 地址: %p, 值: %i\n", &NullId, NullId);
        Serial.printf("IP 無須更換(%s)!\n", LocalIP.toString().c_str());
        return true;
      }
      Serial.printf("使用自訂IP.\n");
      for (currentIpIndex = 0; currentIpIndex < loopCount; currentIpIndex++) {
        IPAddress newlocalIP = ipListPtr[currentIpIndex];
        // if ((Maint_mode == false) || (LocalIP == newlocalIP)) {
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
        WiFi.disconnect(false);
        // delay(1000);  // 等待 1 秒，確保 WiFi 完全斷開
        while (WiFi.status() != WL_DISCONNECTED) {
          delay(100);  // 以較短間隔反覆檢查，以達到最佳反應
        }
        delay(100);  // 以較短間隔反覆檢查，以達到最佳反應

        updateSystemState(STATE_WIFI_CONNECTING);

        // 配置靜態 IP
        gateway = apIP;
        subnet = IPAddress(255, 255, 255, 0);
        if (!WiFi.config(newlocalIP, gateway, subnet, dns)) {
          Serial.println("STA Failed to configure");
          return false;  // 返回錯誤
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
        // attempts = 0;
        // while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        //   delay(500);
        //   Serial.print(".");
        //   attempts++;
        // }

        ConnectStartTime = millis();
        while (WiFi.status() != WL_CONNECTED) {
          if (millis() - ConnectStartTime > WIFI_TIMEOUT) {
            updateSystemState(STATE_ERROR, "WiFi connection_1 timeout");
            status.wifiAttempts++;
            return false;
          }
          Serial.print(".");
          // updateSystemState(STATE_WIFI_CONNECTING);
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


void scanDisplayDigits();

void IRAM_ATTR handleInterrupt() {
  // currentMillis = millis();
  InterruptCount += 1;

  // 檢查是否超過100ms
  if (currentMillis - lastScanDisplayTime >= CHECK_DISPLAY_INTERVAL) {
    lastScanDisplayTime = currentMillis;
    scanCallCount = 0;  // 重置計數器
  }

  // 只在計數器小於3時呼叫scanDisplayDigits
  if (scanCallCount < SCAN_NUM) {
    has_interrupted = true;
    scanCallCount++;
    scanDisplayDigits();  // 數字掃描
  }
}

// IDLE 迴圈函數
bool vApplicationIdleHook(void) {
  idleCount[xPortGetCoreID()]++;
  return true;
}

/*
struct LedState {
  bool isOn;                 // LED 當前狀態
  bool isBlinking;           // 是否閃爍
  unsigned long onTime;      // 亮持續時間 (ms)
  unsigned long offTime;     // 滅持續時間 (ms)
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

  // STATE_WEBSOCKET_CONNECTING, 3
  ledConfigs[STATE_WEBSOCKET_CONNECTING].red = { true, true, 500, 500, 0 };     // 紅燈慢速閃爍
  ledConfigs[STATE_WEBSOCKET_CONNECTING].green = { false, true, 500, 500, 0 };  // 綠燈慢速閃爍

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
  Serial.printf("S%i ", newState);
  if (error.length() > 0) {
    status.lastError = error;
    Serial.println("\nError: " + error);
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
      // Serial.printf("LED(%i)滅! ", LED);
    } else if (!ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->offTime)) {
      ledState->isOn = true;
      ledState->lastToggle = currentMillis;
      digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, LOW);  // LED亮
      // Serial.printf("LED(%i)亮! ", LED);
    }
  } else {  // 不閃爍時用
    // digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, ledState->isOn ? HIGH:LOW );
    int status = (ledState->isOn ? LOW : HIGH);
    digitalWrite(LED, status);
    // Serial.printf("LED(%i)切換%i! ", LED, status);
  }
}


// void blinkLED_new(TimerHandle_t xTimer) {
//   currentMillis = millis();
//   LedState* ledState = (LedState*)pvTimerGetTimerID(xTimer);

//   if (ledState->isBlinking) {
//     if (ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->onTime)) {
//       ledState->isOn = false;
//       ledState->lastToggle = currentMillis;
//       digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, HIGH);  // LED滅
//       // 交替閃爍
//       if (ledState == &ledConfigs[status.state].red) {
//         digitalWrite(LED_GREEN, LOW);  // 綠燈亮
//       } else {
//         digitalWrite(LED_RED, LOW);  // 紅燈亮
//       }
//     } else if (!ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->offTime)) {
//       ledState->isOn = true;
//       ledState->lastToggle = currentMillis;
//       digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, LOW);  // LED亮
//       // 交替閃爍
//       if (ledState == &ledConfigs[status.state].red) {
//         digitalWrite(LED_GREEN, HIGH);  // 綠燈滅
//       } else {
//         digitalWrite(LED_RED, HIGH);  // 紅燈滅
//       }
//     }
//   } else {
//     digitalWrite(ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN, ledState->isOn ? LOW : HIGH);  // LED亮滅相反
//   }
// }


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

// 初始化函數
void setup() {
  Serial.begin(115200);
  // 記錄開機時間
  startTime = millis();

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

  handleRetrieve();
  if (savedData1 == "") {
    savedData1 = "z0000";
    savedData2 = "88888888";
    Serial.printf("設置原始機碼(%s)\n", savedData1);
    preferences.begin("storage", false);
    preferences.putString("saved_data1", savedData1);
    preferences.end();
    handleRetrieve();
  }
  if (savedData1 == "z0000") {
    Serial.printf("機碼為原始值(%s)\n", savedData1);
    NullId = true;
  }
  Caller_Number = savedData1;
  Serial.printf("cmb_caller Ver:%s, Caller Number %s.\n", Version.c_str(), Caller_Number);

  // 初始化 Caller_SSID
  strcpy(Caller_SSID, Caller_Prefix);
  // strcat(Caller_SSID, Caller_Number);
  strcat(Caller_SSID, Caller_Number.c_str());
  wifiNetworks[0].ssid = Caller_SSID;
  wifiNetworks[0].password = "88888888";

#ifdef LOCAL_TEST
  Serial.println("\n ***** 本地測試模式!!! *****\n");
  // wifiNetworks[0].ssid = "";
  // wifiNetworks[0].password = "";
  // wifiNetworks[2].ssid = "";
  // wifiNetworks[2].password = "";
#endif

  // IO 初始化
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  // 初始化 LED 配置
  initLedConfigs();
  // 創建 FreeRTOS 計時器
  redTimer = xTimerCreate("RedLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].red, blinkLED);
  greenTimer = xTimerCreate("GreenLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].green, blinkLED);
  // 啟動計時器
  xTimerStart(redTimer, 0);
  xTimerStart(greenTimer, 0);

  updateSystemState(STATE_INIT);

  const int inputs[] = { LED_a, LED_b, LED_c, LED_d, LED_e, LED_f, LED_g,
                         LED_1e, LED_2e, LED_3e, 0 };
  for (int pin : inputs) {
    pinMode(pin, INPUT);
  }

  // Timer 初始化
  timer0 = timerBegin(1000000);         // 1MHZ
  timerAlarm(timer0, 500000, true, 0);  // 500ms
  timerAttachInterrupt(timer0, &handleInterrupt);

  // 設置外部中斷
  attachInterrupt(digitalPinToInterrupt(LED_1e), handleInterrupt, RISING);
  attachInterrupt(digitalPinToInterrupt(LED_2e), handleInterrupt, RISING);
  attachInterrupt(digitalPinToInterrupt(LED_3e), handleInterrupt, RISING);

  // 網路初始化
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // 禁用 Wi-Fi 休眠
  bool result = false;

  bool boot = true;
  Serial.printf("savedData1.startsWith:%i\n", savedData1.startsWith("z"));
  while (!result) {
    scanAndValidateNetworks();
    for (int i = 0; i < numNetworks; i++) {  // 從 wifiNetworks 取得 ssid & password
      delay(500);

      if (boot && (savedData1.startsWith("z"))) {
        Serial.printf("先連測試網路\n");
        boot = false;
        continue;
      }
      currentNetwork = i;

      if (!wifiNetworks[i].isValid) {
        Serial.printf("wifiNetworks %i pass!\n", i);
        continue;
      }
      result = connectToWiFi_new(wifiNetworks[i].ssid, wifiNetworks[i].password);
      if (result) {
        break;
      }
    }
    if (!result) {
      Serial.printf("\nwifi 無法連線，重新嘗試...\n");
      delay(2000);
    }
  }

  Serial.printf("\n成功連接到 WiFi 網路: %s\n", wifiNetworks[currentNetwork].ssid);

  // 設定 IDLE HOOK 函數
  esp_register_freertos_idle_hook_for_cpu(vApplicationIdleHook, 0);
  esp_register_freertos_idle_hook_for_cpu(vApplicationIdleHook, 1);

  setupOTA();

  // WebSocket Event 處理
  client.onEvent(onEventsCallback);

  // WebSocket 消息處理
  client.onMessage(onMessageCallback);

  // 設定 HTTP 端點
  server.on("/cmb", HTTP_GET, handleRoot);
  server.on("/cmb_store", HTTP_POST, handleStore);
  server.on("/cmb_retrieve", HTTP_GET, handleRetrieve);
  server.on("/cmb_status", HTTP_GET, handleStatus);

  // 啟動 Web Server
  server.begin();

  Serial.println("Setup finish!");
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


// WebSocket 連接函數
bool connectToWebSocket() {
  updateSystemState(STATE_WEBSOCKET_CONNECTING);
  Serial.printf("Connecting to WebSocket server (attempt %i)\n", status.websocketAttempts);

  const int maxAttempts = 5;    // 最大重試次數
  const int retryDelay = 5000;  // 重試延遲時間 (毫秒)
  const int timeout = 10000;    // 連接超時時間 (毫秒)

  for (int attempt = 0; attempt < maxAttempts; attempt++) {
    unsigned long startTime = millis();
    bool connected = false;

    while (millis() - startTime < timeout) {
      connected = client.connect(websockets_server_host, websockets_server_port, "/");
      if (connected) {
        break;
      }
      delay(100);  // 短暫延遲以避免過多嘗試
    }

    if (connected) {
      Serial.println("Connected to WebSocket server");
      updateSystemState(STATE_WEBSOCKET_CONNECTED);
      if (demoState) {
        updateSystemState(STATE_DEMO);
      }
      status.websocketAttempts = 0;
      return true;
    } else {
      Serial.println("WebSocket connection attempt failed");
      updateSystemState(STATE_ERROR, "WebSocket connection failed!");
      status.websocketAttempts++;
      delay(retryDelay);  // 等待一段時間後重試
    }
  }

  Serial.println("Max WebSocket connection attempts reached");
  return false;
}
// bool connectToWebSocket() {
//   updateSystemState(STATE_WEBSOCKET_CONNECTING);
//   Serial.printf("Connecting to WebSocket server(%i)\n", status.websocketAttempts);

//   // !!!@@@
//   bool connected = client.connect(websockets_server_host, websockets_server_port, "/");
//   if (connected) {
//     Serial.println("Connected to WebSocket server");
//     updateSystemState(STATE_WEBSOCKET_CONNECTED);
//     if (demoState) {
//       updateSystemState(STATE_DEMO);
//     }
//     status.websocketAttempts = 0;
//     return true;
//   }
//   updateSystemState(STATE_ERROR, "WebSocket connection failed!");
//   status.websocketAttempts++;
//   return false;
// }

void scanDisplayDigits() {
  const int enablePins[3] = { LED_1e, LED_2e, LED_3e };
  volatile int* numbers[3] = { &n1, &n2, &n3 };

  scanDisplayCount += 1;
  for (int i = 0; i < 3; ++i) {
    int state = digitalRead(enablePins[i]);
    if (state == 1 && fe[i] == 0) {
      fe[i] = 1;
      *numbers[i] = convertToNumber();
    }
    fe[i] = state;
  }
}

// 數字發送函數
void sendCallerNumber() {
  if (!has_interrupted) return;

  if (n1 >= 0 && n2 >= 0 && n3 >= 0) {
    nowStr = String(n1) + String(n2) + String(n3);
    matchCt = (nowStr == preStr) ? matchCt + 1 : 1;
    preStr = nowStr;

    if (matchCt >= 3 && (pn1 != n1 || pn2 != n2 || pn3 != n3)) {
      // Serial.println("*");
      pn1 = n1;
      pn2 = n2;
      pn3 = n3;
      if (nowStr != sendStr && client.available()) {
        updateSystemState(STATE_TRANS);
        String message = String(Caller_Number) + "," + nowStr;
        Serial.println("\nSend: " + message);
        client.send(message);
        sendStr = nowStr;
        nowStrDemo = nowStr;
        onMessage_time = currentMillis;  // 重置 onMessage 計時器
        // vTaskDelay(pdMS_TO_TICKS(50));   // LED 閃動. !!!@@@
        // updateSystemState(STATE_WEBSOCKET_CONNECTED);
      }
      matchCt = 0;
    }
    n1 = n2 = n3 = -1;
  }
  has_interrupted = false;
}

// 檢查連接狀態
void checkConnections() {
  client.poll();  // !!!@@
  // 檢查 WiFi 連接
  if (WiFi.status() != WL_CONNECTED) {
    // Serial.println("WiFi.status() != WL_CONNECTED");
    if (status.state != STATE_WIFI_CONNECTING) {
      // scanAndValidateNetworks();
      Serial.println("status.state != STATE_WIFI_CONNECTING");
      Serial.printf("WiFi.status=%i, status.state=%i\n", WiFi.status(), status.state);
      bool result = false;
      if (wifiNetworks[currentNetwork].isValid)
        // result = connectToWiFi(wifiNetworks[currentNetwork].ssid, wifiNetworks[currentNetwork].password);
        result = connectToWiFi_new(wifiNetworks[currentNetwork].ssid, wifiNetworks[currentNetwork].password);
      if (!result) {                    // 如果連線未成功則試下一組，如斷線先試現在的SSID.
        updateSystemState(STATE_INIT);  // 比需改變為不是 STATE_WIFI_CONNECTING
        Serial.printf("wifiNetworks %s Fail! ,WiFi.status=%i, status.state=%i\n", wifiNetworks[currentNetwork].ssid, WiFi.status(), status.state);
        currentNetwork = (currentNetwork + 1) % numNetworks;
        vTaskDelay(pdMS_TO_TICKS(1000));  // 或使用 delay
      }
    }
    return;
  }

  // 檢查 WebSocket 連接
  if (!client.available()) {
    if (status.state != STATE_WEBSOCKET_CONNECTING) {
      Serial.println("\nconnectToWebSocket");
      connectToWebSocket();
    } else {
      // 如果已經在連接中，但超過一定時間未連接成功，重新嘗試連接
      if (currentMillis - status.lastStateChange > WS_TIMEOUT) {
        Serial.println("WebSocket connection timeout, retrying...");
        client.close();
        updateSystemState(STATE_WEBSOCKET_CONNECTING);
        connectToWebSocket();
      }
    }
    return;
  }
  // client.poll();  // !!!@@
}

// void webSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
void onEventsCallback(WebsocketsEvent event, String data) {
  // Serial.println("");
  if (event == WebsocketsEvent::ConnectionOpened) {
    Serial.println("Event:Connection Opened");
  } else if (event == WebsocketsEvent::ConnectionClosed) {
    Serial.println("\nEvent:Connection Closed");
  } else if (event == WebsocketsEvent::GotPing) {
    Serial.print("I");
    client.pong();
    Serial.print("o ");
  } else if (event == WebsocketsEvent::GotPong) {
    // Serial.println("\nEvent:Got a Pong!");
    Serial.print("O");
  }
}

void onMessageCallback(WebsocketsMessage message) {
  // Serial.println("onMessage");
  onMessage_time = 0;
  if (message.data() != "pong") {
    // updateSystemState(STATE_WEBSOCKET_CONNECTED);
    if (demoState) {
      updateSystemState(STATE_DEMO);
    } else {
      updateSystemState(STATE_WEBSOCKET_CONNECTED);
    }
    Serial.println("Received: " + message.data());
  } else Serial.print("B ");  // Ping_EX Back.
}

// 在全域變數區域加入
#define MINIMUM_HEAP 20000  // 設定最小堆積記憶體門檻值（依需求調整）

// 記憶體檢查函數
void checkMemory() {
  uint32_t freeHeap = ESP.getFreeHeap();
  Serial.printf("Free Heap: %u bytes\n", freeHeap);
  if (freeHeap < MINIMUM_HEAP) {
    updateSystemState(STATE_ERROR, "Low memory warning");
  }
}

// 發送 Ping_EX
void Ping_EX() {
  if (client.ping()) {
    // Serial.println("Ping sent successfully");
    Serial.print("i");
  } else {
    Serial.println("Ping failed!!!");
  }
  String message = "";
  if (!demoState)
    message = String(Caller_Number) + "," + "ping" + "," + sendStr;
  else
    message = String(Caller_Number) + "," + "ping" + "," + nowStrDemo;
  if (client.available()) {
    client.send(message);
    lastPING = currentMillis;
    onMessage_time = lastPING;  // 重置 onMessage 計時器
  }
}

// 定義任務狀態數組的最大大小
#define MAX_TASKS 20

// 全局變量，用於存儲上一次的任務運行時間
TaskStatus_t previousTaskStatus[MAX_TASKS];
UBaseType_t previousTaskCount = 0;

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



portMUX_TYPE statsMutex = portMUX_INITIALIZER_UNLOCKED;

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
  // vTaskClearRunTimeStats();  // !!!@@@
  // vTaskResetRunTimeStats();   // !!!@@@
  // resetRuntimeStats();  // !!!@@@
  // resetRunTimeCounter();  // !!!@@@
}

// void resetRunTimeCounter() {
//   // 重置任務運行時間計數器
//   TaskStatus_t* pxTaskStatusArray;
//   volatile UBaseType_t uxArraySize, x;
//   unsigned long ulTotalRunTime;

//   // 獲取任務數量
//   uxArraySize = uxTaskGetNumberOfTasks();

//   // 分配內存來存儲任務狀態
//   pxTaskStatusArray = (TaskStatus_t*)pvPortMalloc(uxArraySize * sizeof(TaskStatus_t));

//   if (pxTaskStatusArray != NULL) {
//     // 獲取任務狀態
//     uxArraySize = uxTaskGetSystemState(pxTaskStatusArray, uxArraySize, &ulTotalRunTime);

//     // 重置每個任務的運行時間
//     for (x = 0; x < uxArraySize; x++) {
//       pxTaskStatusArray[x].ulRunTimeCounter = 0;
//     }
//   }
//   // 釋放內存
//   vPortFree(pxTaskStatusArray);
//   Serial.println("🔄 重置任務運行時間計數器");
// }

void check_system(unsigned long lastCheckTime, unsigned long currentMillis) {
  // Serial.println("--- CPU Usage (RunTimeStats) ---");
  // showCPULoad();
  // Serial.println("\n=== System Load Monitor ===");
  // GetRunTimeStats();
  // Serial.println("\n--- Task Load (SystemState) ---");
  // showTaskLoad();
  // Serial.println("===========================\n");
  // printRunningTasks(Serial);
  calculateCPULoad(lastCheckTime, currentMillis);
  // printTaskStats();
  checkMemory();
  // Serial.printf("InterruptCount:%lu, scanDisplayCount:%lu \n", InterruptCount, scanDisplayCount);
}

int idleRate[2] = { configTICK_RATE_HZ, configTICK_RATE_HZ };

void calculateCPULoad(unsigned long lastCheckTime, unsigned long currentMillis) {
  float minute = ((currentMillis - lastCheckTime) / 1000.0);
  for (int i = 0; i < portNUM_PROCESSORS; i++) {
    uint32_t idleDiff = idleCount[i] - idleCountLast[i];
    if (idleDiff > int(idleRate[i] * minute)) {
      idleRate[i] = ((float)idleDiff / minute) + 1;
    }
    // int idleRate = configTICK_RATE_HZ * ((currentMillis - lastCheckTime) / 1000);
    float load = (1.0f - (float)idleDiff / (float)(idleRate[i] * minute));
    // 確保負載量不為負數且不超過 100%
    // if (load < 0) load = 0;
    // if (load > 100) load = 100;
    Serial.printf("idleCount - idleCountLast:%lu, idleRate:%lu\n", idleCount[i] - idleCountLast[i], idleRate[i]);
    Serial.printf("Core %d Load: %.2f%%\n", i, load);
    idleCountLast[i] = idleCount[i];
  }
}


unsigned long lastScanTime = millis();     // 記錄最後一次掃描網路的時間
const unsigned long scanInterval = 60000;  // 掃描網路的時間間隔（毫秒）

// 主循環
void loop() {
  static unsigned long lastCheck = 0;
  currentMillis = millis();

  if (Maint_mode && ((currentMillis - startTime) > expireTime)) {
    Maint_mode = false;
    Serial.printf("\nMaint_mode(%d) off!\n", Maint_mode);
    if (NullId) {
      Serial.printf("\n重新取得IP!\n");
      // WiFi.disconnect(true);
      WiFi.disconnect();
    }
  }

  server.handleClient();
  ArduinoOTA.handle();

  // 定期檢查連接狀態
  if (currentMillis - lastCheck >= STATE_UPDATE_INTERVAL) {
    lastCheck = currentMillis;
    checkConnections();
  }

  // 處理 Caller 數字發送
  if (currentMillis - lastCheckNumber >= CHECK_NUMBER_INTERVAL) {
    lastCheckNumber = currentMillis;
    sendCallerNumber();
  }

  // 發送 ping
  if (currentMillis - lastPING >= PING_INTERVAL) {
    lastPING = currentMillis;
    Ping_EX();
  }

  // 檢查 onMessage 超時
  if ((onMessage_time != 0) && (currentMillis - onMessage_time >= ON_MESSAGE_TIMEOUT)) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("onMessage timeout, reconnecting WebSocket...");
      client.close();
      updateSystemState(STATE_WEBSOCKET_CONNECTING);
      connectToWebSocket();
      onMessage_time = currentMillis;  // 重置計時器
    }
  }

  // 按鈕處理
  handleButton(currentMillis);

  // Demo 模式處理
  if (demoState) {
    handleDemoMode(currentMillis);
  }

  if (currentMillis - lastPrintTime >= printInterval) {
    //lastPrintTime = currentMillis;  // 更新上次印出訊息的時間
    Serial.println();  // 印出換行
    check_system(lastPrintTime, currentMillis);
    lastPrintTime = currentMillis;  // 更新上次印出訊息的時間
  }

  if ((WiFi.status() != WL_CONNECTED) && (currentMillis - lastScanTime >= scanInterval)) {
    // 執行掃描和驗證網路的函數
    lastScanTime = currentMillis;  // 更新最後一次掃描的時間
    scanAndValidateNetworks();
  }

  // if (currentMillis % 10 == 0)  // 10ms 執行一次
  vTaskDelay(pdMS_TO_TICKS(1));
}

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

void handleDemoMode(unsigned long currentMillis) {
  if (currentMillis - lastUpdateTime >= nextUpdateInterval) {
    // 生成非零隨機變化值
    int change;
    do {
      // change = random(MIN_CHANGE, MAX_CHANGE + 1);
      change = 1;
    } while (change == 0);
    // Serial.printf("Change: %d\n", change);

    int nowStrNum = nowStrDemo.toInt();
    // Serial.printf("Old value: %d\n", nowStrNum);
    nowStrNum += change;

    // // 處理循環邏輯
    // if (nowStrNum > MAX_VALUE) {
    //   nowStrNum = MIN_VALUE + (nowStrNum - MAX_VALUE - 1);
    // } else if (nowStrNum < MIN_VALUE) {
    //   nowStrNum = MAX_VALUE - (MIN_VALUE - nowStrNum - 1);
    // }

    nowStrNum = ((nowStrNum - MIN_VALUE) % (MAX_VALUE - MIN_VALUE + 1)) + MIN_VALUE;

    if (client.available()) {
      nowStrDemo = String(nowStrNum);
      String message = String(Caller_Number) + "," + nowStrDemo;
      Serial.println("\nDemo Send: " + message);
      // updateSystemState(STATE_DEMO);
      updateSystemState(STATE_TRANS);
      client.send(message);
      onMessage_time = currentMillis;  // 重置 onMessage 計時器
    }
    lastUpdateTime = currentMillis;
    nextUpdateInterval = random(MIN_INTERVAL, MAX_INTERVAL + 1);
    // Serial.printf("nextUpdateInterval:%lu\n", nextUpdateInterval);
  }
}

void toggleDemoMode() {
  demoState = !demoState;
  // ledState = !ledState;
  Serial.printf("Demo mode: %s\n", demoState ? "ON" : "OFF");
  if (demoState) {
    // 設定初始值
    randomSeed(millis());
    lastUpdateTime = millis();
    nextUpdateInterval = random(MIN_INTERVAL, MAX_INTERVAL + 1);
    // Serial.printf("nextUpdateInterval:%lu\n", nextUpdateInterval);
    updateSystemState(STATE_DEMO);
  } else {
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
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
    // Serial.println("資料 1 已存儲: " + data1);
  }

  if (server.hasArg("data2")) {
    String data2 = server.arg("data2");
    preferences.putString("saved_data2", data2);
    response += "資料 2 已存儲: " + data2 + "\n";
    // Serial.println("資料 2 已存儲: " + data2);
  }

  if (server.hasArg("data3")) {
    String data3 = server.arg("data3");
    preferences.putString("saved_data3", data3);
    response += "資料 3 已存儲: " + data3 + "\n";
    // Serial.println("資料 3 已存儲: " + data3);
  }

  preferences.end();

  if (response == "") {
    server.send(400, "text/plain; charset=UTF-8", "錯誤: 缺少 data 參數");
    Serial.println("錯誤: 缺少 data 參數");
  } else {
    server.send(200, "text/plain; charset=UTF-8", response);
  }
  // handleRetrieve();   // 更新資料
  //重新啟動
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


const int SIGNAL_THRESHOLD = -90;  // 例如: 低於 -80 dBm 視為無效

void scanAndValidateNetworks() {
  Serial.println("PASS 掃描 WiFi 網路...");
  // Serial.println("開始掃描 WiFi 網路...");

  // // // 確保 WiFi 已斷開並處於空閒狀態
  // // WiFi.disconnect();
  // // while (WiFi.status() != WL_DISCONNECTED) {
  // //   delay(100);
  // // }
  // // delay(1000);  // 確保 WiFi 完全斷開

  // // 執行網路掃描，獲取掃描到的網路數量
  // int networksFound = WiFi.scanNetworks();
  // if (networksFound == -1) {
  //   Serial.println("WiFi 掃描失敗！");
  //   return;
  // } else if (networksFound == -2) {
  //   Serial.println("WiFi 掃描未完成或模組未準備好！");
  //   return;
  // }
  // Serial.printf("掃描結果: 找到 %d 個網路\n", networksFound);

  // /* 重置原有清單中的資料，一次掃描後將狀態與訊號強度重設 */
  // for (int i = 0; i < numNetworks; i++) {
  //   wifiNetworks[i].isValid = false;
  //   wifiNetworks[i].signalStrength = 0;
  // }

  // /* 遍歷每個掃描到的網路 */
  // for (int j = 0; j < networksFound; j++) {
  //   String scannedSSID = WiFi.SSID(j);
  //   int currentRSSI = WiFi.RSSI(j);

  //   // 輸出掃描到的網路名稱與訊號強度
  //   Serial.printf("掃描網路: %s | RSSI: %d dBm\n", scannedSSID.c_str(), currentRSSI);

  //   // 將掃描到的資料與預設清單中的 AP 進行比對
  //   for (int i = 0; i < numNetworks; i++) {
  //     // 使用字串比對確認是否為同一個 SSID
  //     if (scannedSSID.equals(wifiNetworks[i].ssid)) {
  //       wifiNetworks[i].signalStrength = currentRSSI;
  //       // 若訊號強度超過閾值則標記為有效，否則標記為無效
  //       wifiNetworks[i].isValid = (currentRSSI > SIGNAL_THRESHOLD);
  //     }
  //   }
  // }

  // // 顯示更新後的 AP 狀態
  // Serial.println("\n最終 WiFi AP 狀態:");
  // for (int i = 0; i < numNetworks; i++) {
  //   Serial.printf("SSID: %s, 狀態: %s, RSSI: %d dBm\n",
  //                 wifiNetworks[i].ssid,
  //                 wifiNetworks[i].isValid ? "有效" : "無效",
  //                 wifiNetworks[i].signalStrength);
  // }
}
