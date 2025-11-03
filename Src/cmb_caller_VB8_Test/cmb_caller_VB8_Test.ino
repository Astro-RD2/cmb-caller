#define VERSION "VB8_20251016_Test"

// 引入必要的函式庫
#include <WebSocketsClient.h>  // 用於 WebSocket 通訊
#include <Arduino.h>           // Arduino 核心函式庫
#include <WiFi.h>              // ESP32 WiFi 功能
#include <ArduinoOTA.h>        // OTA 更新功能
#include "sdkconfig.h"         // ESP32 SDK 配置
#include <WebServer.h>         // Web 伺服器功能
#include <Preferences.h>       // 用於存儲偏好設定
#include <ArduinoJson.h>       // 用於 JSON 解析和產生

// 引入自定義的憑證檔案
#include "credentials.h"
#include "ma_Functions.h"

// 程式版本資訊
#ifndef LOCAL_TEST
String Version = VERSION;
#else
String Version = String(VERSION) + " Local Test!";
#endif

// 呼叫號碼（用於識別設備）
String Caller_Number = "00000";

#define LED_RED 33    // 紅色 LED
#define LED_GREEN 32  // 綠色 LED
#define LED_BLUE 2    // 藍色 LED

// 計時器和網路相關設定
const long WIFI_TIMEOUT = 7000;          // WiFi 連接超時時間（7 秒）
const long STATE_UPDATE_INTERVAL = 500;  // 狀態更新間隔（500 毫秒）
const long PING_INTERVAL = 30000;        // Ping 間隔（30 秒）
const long CHECK_NUMBER_INTERVAL = 50;   // 數值變動取樣間隔（50 毫秒）

// 系統變數
unsigned long lastPING = 0;
volatile unsigned long onMessage_time = 0;
unsigned long lastPrintTime = millis();
unsigned long lastCheckNumber = 0;
volatile unsigned long currentMillis = millis();

// 呼叫號碼相關定義
const char Caller_Prefix[] = "CMB";
char Caller_SSID[sizeof(Caller_Prefix) + sizeof(Caller_Number) - 1];

String nowStr = "0";
String nowStrDemo = "0";
String sendStr = "000";
String lastSendStr = sendStr;
bool bypassLast = false;

// WebSocket 客戶端
WebSocketsClient webSocketClient;

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
  STATE_AP_STA,
  STATE_AP_STA_C,
  STATE_NUMBER_ERROR,
  STATE_RESTORE,
  STATE_COUNT
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

// LED 控制結構
struct LedState {
  bool isOn;
  bool isBlinking;
  unsigned long onTime;
  unsigned long offTime;
  unsigned long lastToggle;
};

// LED 配置
struct LedConfig {
  LedState red;
  LedState green;
} ledConfigs[STATE_COUNT];

// FreeRTOS 計時器
TimerHandle_t redTimer;
TimerHandle_t greenTimer;

// 存儲的資料
String savedData1 = "";
String savedData2 = "";
String savedData3 = "";
volatile bool NullId = false;

// 開機時間與失效時間
unsigned long startTime = 0;
const unsigned long expireMinutes = 10;
unsigned long expireTime = expireMinutes * 60 * 1000;

// 資料緩衝區設定
#define NUM_BUFFER_SIZE 60
int num_buffer[NUM_BUFFER_SIZE];
int num_head = 0;
int num_tail = 0;

// 其他變數
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 10;
bool waitingResponse = false;
int retryValue;
bool retryMode = false;
const int retryTimeout = 5;

bool Maint_mode = true;

String ssid;
String password;
bool new_connect = false;
int ping_EX_no_reply_count = 0;
int sendPing_fail = 0;

unsigned long websocket_connect_time = millis();

int AP_mode = 0;

#define STATUS_INTERVAL 500
static unsigned long lastCheck = 0;
bool WebSocket_init = false;

//======================================================================
// 函數原型宣告
void updateSystemState(SystemState newState, const String& error = "");
void GetSendCallerNumber(unsigned long currentMillis);
void initLedConfigs();
void updateLEDState();
void blinkLED(TimerHandle_t xTimer);
void setupOTA();
void setupWebSocket();
void handleRoot();
void handleStore();
void handleRetrieve();
void onMessageCallback(const String& message);

void checkMemory();
void Ping_EX();
void client_send(const String& message);
void buffer_push(int value);
bool buffer_pop(int& value);
void sendBufferedData();
void sendWebSocketMessage(int value);
void checkResponse();
void add_profile(const char* ssid, const char* password);
void WiFi_reconnect();

void change_AP_mode();
void process_change_AP_mode(int code);
void parseUpdateMessage(const String& msg);
void num_LED_dis(const String& message);
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length);
void check_auth();
bool VB8_Recv();
void VB8_Send(unsigned long num);

//=========================================================================

#define MAX_NETWORKS 15
#define MAX_USER_NETWORKS 10

// 合併後的網路清單
WiFiNetwork wifiNetworks[MAX_NETWORKS];
uint8_t networkCount = 0;

// 用戶新增網路
Preferences preferences;
WebServer server(80);

struct ScannedNetwork {
  String ssid;
  String bssid;
  int8_t rssi;
  int channel;
  String encryption;
};
std::vector<ScannedNetwork> scannedNetworks;

const unsigned long SCAN_INTERVAL = 60 * 60 * 1000;
const unsigned long SCAN_MIN_INTERVAL = 30000;

unsigned long lastScanTime = millis() - SCAN_INTERVAL;
unsigned long lastScanTimeRun = millis() - SCAN_MIN_INTERVAL;

const int MIN_ACCEPTABLE_RSSI = -85;
const int MIN_SAVE_RSSI = MIN_ACCEPTABLE_RSSI - 0;

const unsigned long CONNECT_RETRY_DELAY = 1000;

unsigned long lastConnectAttempt = millis() - CONNECT_RETRY_DELAY - 1000;

bool isScanning = false;
unsigned long scanStartTime = 0;

unsigned long lastDisconnectTime = 0;
const unsigned long RECONNECT_DELAY = 1000;

bool demoState = false;  // Demo 模式狀態
unsigned long sendTime;  // 發送時間記錄
unsigned int cldNum = 1;  // CLD當前編號(0-999)



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

  uint8_t userCount = 0;
  for (int i = 0; i < networkCount; i++) {
    if (wifiNetworks[i].isUserAdded) userCount++;
  }

  preferences.putUChar("count", userCount);

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

void addNetwork(const char* ssid, const char* password) {
  Serial.printf("addNetwork:%s,%s\n", ssid, password);
  for (uint8_t i = 0; i < networkCount; i++) {
    if (strcmp(wifiNetworks[i].ssid, ssid) == 0) {
      Serial.printf("addNetwork 用戶已存在:%s\n", ssid);
      strncpy(wifiNetworks[i].password, password, 63);
      wifiNetworks[i].password[63] = 0;
      wifiNetworks[i].isUserAdded = true;
      if (wifiNetworks[i].isUserAdded) {
        WiFiNetwork temp = wifiNetworks[i];
        for (uint8_t j = i; j > 0; j--) {
          wifiNetworks[j] = wifiNetworks[j - 1];
        }
        wifiNetworks[0] = temp;
      }
      return;
    }
  }

  if (networkCount < MAX_NETWORKS) {
    Serial.printf("addNetwork 添加新用戶:%s\n", ssid);
    for (uint8_t i = networkCount; i > 0; i--) {
      wifiNetworks[i] = wifiNetworks[i - 1];
    }

    strncpy(wifiNetworks[0].ssid, ssid, 31);
    wifiNetworks[0].ssid[31] = 0;
    strncpy(wifiNetworks[0].password, password, 63);
    wifiNetworks[0].password[63] = 0;
    wifiNetworks[0].enabled = true;
    wifiNetworks[0].rssi = 0;
    wifiNetworks[0].isUserAdded = true;
    networkCount++;
  }
}

void deleteNetwork(uint8_t idx) {
  uint8_t userNetworkIndex = 0;
  uint8_t foundIndex = 255;

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
    for (uint8_t i = foundIndex; i < networkCount - 1; i++) {
      wifiNetworks[i] = wifiNetworks[i + 1];
    }
    networkCount--;
    saveNetworks();
  }
}

// ====== 合併預設網路 ======
void mergeDefaultNetworks() {
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
  delay(500);
}

void disableAP() {
  Serial.print("AP 關閉!\n");
  WiFi.softAPdisconnect(true);
  updateSystemState(STATE_RESTORE);
}

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
  if (WiFi.getMode() == WIFI_OFF) {
    Serial.printf(" 0_強制 AP 切換到 %i 模式!\n", AP_mode);
    change_AP_mode();
  }

  if (!isScanning && (millis() - lastScanTime) >= SCAN_INTERVAL) {
    Serial.println("\n啟動背景 Wi-Fi 掃描...");

    for (int retry = 0; retry < 3; retry++) {
      if (millis() - lastScanTimeRun <= SCAN_MIN_INTERVAL) {
        int delay = (SCAN_MIN_INTERVAL - (millis() - lastScanTimeRun));
        Serial.printf("設定延後 %dms WiFi 掃描!!\n", delay);
        lastScanTime = millis() - SCAN_INTERVAL + delay;
        return;
      }
      int scanResult = WiFi.scanNetworks(true, false, false, 100);
      if (scanResult == WIFI_SCAN_RUNNING) {
        isScanning = true;
        scanStartTime = millis();
        Serial.printf("掃描啟動成功 (嘗試 %d)\n", retry + 1);
        lastScanTime = millis();
        lastScanTimeRun = lastScanTime;
        break;
      } else {
        Serial.printf("掃描啟動失敗，錯誤碼: %d (嘗試 %d)\n", scanResult, retry + 1);
        if (retry < 2) {
          WiFi.scanDelete();
          delay(500 * (retry + 1));
          delay(500);
        } else {
          isScanning = false;
        }
      }
    }
  }

  if (isScanning) {
    int scanStatus = WiFi.scanComplete();

    if (scanStatus == WIFI_SCAN_RUNNING) {
      if (millis() - scanStartTime > 10000) {
        Serial.println("掃描超時，取消本次掃描");
        WiFi.scanDelete();
        isScanning = false;
      }
      return;
    }

    if (scanStatus < 0) {
      Serial.printf("掃描失敗，錯誤碼: %d\n", scanStatus);
      isScanning = false;
      return;
    }

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
                    network.encryption);

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
    WiFi.scanDelete();
    Serial.printf("當前已儲存的有效網路數量: %d\n", scannedNetworks.size());
    isScanning = false;
  }
}

bool isAcceptableSignal(const String& ssid) {
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

#define LED_PIN 2

void attemptWiFiConnect() {
  const uint8_t MAX_ATTEMPTS = 1;
  static unsigned long lastStatusTime = 0;
  if (WiFi.status() != WL_CONNECTED && millis() - lastConnectAttempt >= CONNECT_RETRY_DELAY) {
    updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
    if (isScanning) {
      if (millis() - lastStatusTime >= STATUS_INTERVAL) {
        lastStatusTime = millis();
        Serial.print(" sc");
      }
      return;
    }
    Serial.printf("\n連線 Wi-Fi...\n");

    for (uint8_t attemptCount = 1; attemptCount <= MAX_ATTEMPTS; attemptCount++) {
      Serial.printf("[嘗試 %d/%d] 連線 Wi-Fi...\n", attemptCount, MAX_ATTEMPTS);
      for (uint8_t i = 0; i < networkCount; i++) {
        if (!wifiNetworks[i].enabled) continue;

        String currentSSID = String(wifiNetworks[i].ssid);
        if (isAcceptableSignal(currentSSID)) {
          Serial.printf("測試網路 #%d: %s\n", i + 1, currentSSID.c_str());
          updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
          Serial.printf("WiFi.begin: %s\n", wifiNetworks[i].ssid);
          WiFi.begin(wifiNetworks[i].ssid, wifiNetworks[i].password);
          password = wifiNetworks[i].password;
          unsigned long startAttempt = millis();
          unsigned long lastBlink = 0;
          const unsigned long blinkInterval = 500;

          while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < WIFI_TIMEOUT) {
            unsigned long now = millis();
            if (now - lastBlink >= blinkInterval) {
              lastBlink = now;
              Serial.print(".");
            }
            server.handleClient();
            GetSendCallerNumber(now);
          }

          if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("\n\n========================================\n");
            Serial.printf("(%s,%s,%s,%s)連線成功！\n", Caller_Number, wifiNetworks[i].ssid, WiFi.localIP().toString().c_str(), password);
            Serial.printf("========================================\n\n");
            digitalWrite(LED_PIN, HIGH);
            lastConnectAttempt = millis();
            return;
          } else {
            digitalWrite(LED_PIN, LOW);
            Serial.println("\n連線失敗");
            WiFi.disconnect(true);
          }
        }
      }
      if (WiFi.status() == WL_CONNECTED) {
      } else {
        digitalWrite(LED_PIN, LOW);
        Serial.println("\n全部連線失敗!!!");
        delay(1000);
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

// 數字讀取發送函數
void GetSendCallerNumber(unsigned long currentMillis) {
  if (currentMillis - lastCheckNumber < CHECK_NUMBER_INTERVAL)
    return;
  bool get_num = VB8_Recv();

  if (get_num) {
    client_send(nowStr);
    lastSendStr = sendStr;
    sendStr = nowStr;
    nowStrDemo = nowStr;
    onMessage_time = currentMillis;
    process_change_AP_mode(sendStr.toInt());
  }
}

// 初始化 LED 設定
void initLedConfigs() {
  // STATE_INIT, 0
  ledConfigs[STATE_INIT].red = { true, false, 0, 0, 0 };
  ledConfigs[STATE_INIT].green = { false, false, 0, 0, 0 };

  // STATE_WIFI_CONNECTING, 1
  ledConfigs[STATE_WIFI_CONNECTING].red = { false, true, 100, 100, 0 };
  ledConfigs[STATE_WIFI_CONNECTING].green = { false, false, 0, 0, 0 };

  // STATE_WIFI_CONNECTED, 2
  ledConfigs[STATE_WIFI_CONNECTED].red = { true, false, 0, 0, 0 };
  ledConfigs[STATE_WIFI_CONNECTED].green = { false, false, 0, 0, 0 };

  // STATE_WEBSOCKET_CONNECTING, 3
  ledConfigs[STATE_WEBSOCKET_CONNECTING].red = { true, true, 750, 750, 0 };
  ledConfigs[STATE_WEBSOCKET_CONNECTING].green = { false, true, 750, 750, 0 };

  // STATE_WEBSOCKET_CONNECTED, 4
  ledConfigs[STATE_WEBSOCKET_CONNECTED].red = { false, false, 0, 0, 0 };
  ledConfigs[STATE_WEBSOCKET_CONNECTED].green = { true, false, 0, 0, 0 };

  // STATE_ERROR, 5
  ledConfigs[STATE_ERROR].red = { false, false, 0, 0, 0 };
  ledConfigs[STATE_ERROR].green = { false, false, 0, 0, 0 };

  // STATE_DEMO, 6
  ledConfigs[STATE_DEMO].red = { false, false, 0, 0, 0 };
  ledConfigs[STATE_DEMO].green = { true, true, 1900, 100, 0 };

  // STATE_TRANS, 7
  ledConfigs[STATE_TRANS].red = { true, true, 100, 10000, 0 };
  ledConfigs[STATE_TRANS].green = { true, false, 0, 0, 0 };

  // STATE_AP_STA,8
  ledConfigs[STATE_AP_STA].red = { true, true, 100, 400, 0 };
  ledConfigs[STATE_AP_STA].green = { false, true, 500, 500, 0 };

  // STATE_AP_STA_C,9
  ledConfigs[STATE_AP_STA_C].red = { false, false, 0, 0, 0 };
  ledConfigs[STATE_AP_STA_C].green = { true, true, 500, 500, 0 };

  // STATE_NUMBER_ERROR,10
  ledConfigs[STATE_NUMBER_ERROR].red = { true, false, 0, 0, 0 };
  ledConfigs[STATE_NUMBER_ERROR].green = { false, false, 0, 0, 0 };
}

// LED 先亮後滅
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

  vTimerSetTimerID(redTimer, redState);
  vTimerSetTimerID(greenTimer, greenState);

  currentMillis = millis();
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
    }
  }

  if (newState == previousDisState)
    return;
  previousDisState = newState;

  Serial.printf(" _S%d ", newState);
  if (error.length() > 0) {
    status.lastError = error;
    Serial.println(error);
  }
  if (newState == STATE_ERROR) {
    return;
  }

  if (newState != STATE_AP_STA && newState != STATE_AP_STA_C && newState != STATE_DEMO) {
    if (newState == STATE_RESTORE) {
      newState = previousState;
      Serial.printf(" __S%d ", newState);
    } else {
      previousState = newState;
    }
  }
  status.lastStateChange = currentMillis;
  status.state = newState;
  updateLEDState();
}

// LED 閃動函數
void blinkLED(TimerHandle_t xTimer) {
  unsigned long currentMillis = millis();
  LedState* ledState = (LedState*)pvTimerGetTimerID(xTimer);

  int selectedLED = (ledState == &ledConfigs[status.state].red ? LED_RED : LED_GREEN);
  if (ledState->isBlinking) {
    if (ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->onTime)) {
      ledState->isOn = false;
      ledState->lastToggle = currentMillis;
      digitalWrite(selectedLED, HIGH);
      if (selectedLED == LED_RED)
        digitalWrite(LED_BLUE, HIGH);
    } else if (!ledState->isOn && (currentMillis - ledState->lastToggle >= ledState->offTime)) {
      ledState->isOn = true;
      ledState->lastToggle = currentMillis;
      digitalWrite(selectedLED, LOW);
      if (selectedLED == LED_RED)
        digitalWrite(LED_BLUE, LOW);
    }
  } else {
    int status = (ledState->isOn ? LOW : HIGH);
    digitalWrite(selectedLED, status);
    if (selectedLED == LED_RED)
      digitalWrite(LED_BLUE, status);
  }
}

void onMessageCallback(const String& message) {
  onMessage_time = 0;
  if (message == "pong") {
    Serial.print("B");
    return;
  }
  updateSystemState(STATE_WEBSOCKET_CONNECTED);
  Serial.println("接收: " + message);
  if (message.startsWith("OK,")) {
    waitingResponse = false;
  }
  parseUpdateMessage(message);
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



// void parseUpdateMessage(const String& msg) {
//   StaticJsonDocument<200> doc;
//   DeserializationError error = deserializeJson(doc, msg);

//   if (!error) {
//     if (doc.containsKey("action")) {
//       String action = doc["action"].as<String>();
//       if (action.startsWith("wifi_")) {
//         return;
//       }
//     }
//   }

//   String parts[4];
//   int count = 0;
//   int start = 0;
//   while (count < 4 && start < msg.length()) {
//     int end = msg.indexOf(',', start);
//     if (end == -1) end = msg.length();
//     parts[count++] = msg.substring(start, end);
//     start = end + 1;
//   }
//   if (count == 4 && (parts[3] == "update" || parts[3] == "get")) {
//     Serial.printf("Websocket 已連線時間:%lu\n", millis() - websocket_connect_time);
//     bypassLast = false;
//     if (((millis() - websocket_connect_time) >= 1000) || (parts[2] != sendStr && parts[2] != lastSendStr)) {
//       if ((millis() - websocket_connect_time) < 1000) {
//         bypassLast = true;
//         Serial.printf("bypassLast = true\n");
//       }
//       Serial.printf("%s   資料變動:%s, old sendStr:%s,%s \n", parts[3], parts[2], lastSendStr, sendStr);
//       num_LED_dis(parts[2]);
//     } else {
//       Serial.printf("%s 資料未變動:%s, old sendStr:%s,%s \n", parts[3], parts[2], lastSendStr, sendStr);
//     }
//   }
// }

bool webSocketClient_sendTXT(String& message) {
  Serial.print("[WebSocket 發送] ");
  Serial.println(message);
  webSocketClient.sendTXT(message);
  return true;
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
  WiFi.disconnect(false, false);
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
      webSocketClient.beginSSL(host, port, "/");
    } else {
      webSocketClient.begin(host, port, "/");
    }

    webSocketClient.onEvent(webSocketEvent);
    webSocketClient.setReconnectInterval(1);

    unsigned long startTime = millis();
    while (millis() - startTime < 10000) {
      if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\nWiFi 已斷線！跳出 setupWebSocket!!!");
        return;
      }
      webSocketClient.loop();
      if (webSocketClient.isConnected()) {
        Serial.printf("[狀態] 連接成功！(%s:%d/)\n", host, port);
        updateSystemState(STATE_WEBSOCKET_CONNECTED, "WebSocket 已連接！");
        return;
      }
      vTaskDelay(pdMS_TO_TICKS(100));
    }

    Serial.println("[狀態] 連接失敗,斷開當前連接,嘗試下一個伺服器...");
    webSocketClient.disconnect();
    updateSystemState(STATE_WEBSOCKET_CONNECTING, "連接失敗，嘗試下一個伺服器...");
  }
  Serial.println("[錯誤] 所有伺服器連接失敗！");
  updateSystemState(STATE_WEBSOCKET_CONNECTING, "所有伺服器連接失敗！");
}

unsigned long disconnected_time = millis();

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      disconnected_time = millis();
      Serial.printf("\nWebSocket Disconnected! (WStype_DISCONNECTED) (%lu Sec)\n", (millis() - websocket_connect_time) / 1000);
      updateSystemState(STATE_ERROR, "STATE_ERROR WebSocket Disconnected!");
      break;
    case WStype_CONNECTED:
      Serial.printf("\nWebSocket Connected!(%lu ms)\n", millis() - disconnected_time);
      websocket_connect_time = millis();
      new_connect = true;
      updateSystemState(STATE_WEBSOCKET_CONNECTED);
      break;
    case WStype_TEXT:
      onMessageCallback(String((char*)payload));
      break;
    case WStype_PING:
      Serial.print("I");
      Serial.print("o");
      break;
    case WStype_PONG:
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
      Serial.printf("\n已超過%d次 sendPing 失敗!, reconnecting...\n", sendPing_fail);
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
    webSocketClient_sendTXT(message);
    Serial.print("E");
    lastPING = currentMillis;
    onMessage_time = lastPING;
  }
}

// **首頁**
void cmb_handleRoot() {
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
  server.send(200, "text/plain; charset=UTF-8", response);
}

void IRAM_ATTR client_send(const String& message) {
  buffer_push(message.toInt());
}

// 將資料推入緩衝區
void IRAM_ATTR buffer_push(int value) {
  num_buffer[num_head] = value;
  num_head = (num_head + 1) % NUM_BUFFER_SIZE;
  if (num_head == num_tail) {
    num_tail = (num_tail + 1) % NUM_BUFFER_SIZE;
    Serial.println("Buffer 已滿，覆寫舊資料");
  }
}

// 從緩衝區彈出資料
bool buffer_pop(int& value) {
  if (num_head == num_tail) {
    return false;
  }
  value = num_buffer[num_tail];
  num_tail = (num_tail + 1) % NUM_BUFFER_SIZE;
  return true;
}

int buffer_size() {
  if (num_head >= num_tail) {
    return num_head - num_tail;
  } else {
    return NUM_BUFFER_SIZE - num_tail + num_head;
  }
}

unsigned long bufferSendTime = millis();
void sendBufferedData() {
  static bool buffer_use = false;
  if (WiFi.status() == WL_CONNECTED && webSocketClient.isConnected() && !waitingResponse) {
    int value;
    if (retryMode) {
      value = retryValue;
      sendWebSocketMessage(value);
      bufferSendTime = millis();
      retryMode = false;
    } else if (((millis() - bufferSendTime) > 500) && buffer_pop(value)) {
      sendWebSocketMessage(value);
      bufferSendTime = millis();
      if (buffer_size() > 0) {
        buffer_use = true;
      }
      if (buffer_use == true && buffer_size() == 0) {
        buffer_use = false;
        String message = String(Caller_Number) + ",get";
        updateSystemState(STATE_TRANS);
        Serial.println("查詢最新叫號號碼!");
        webSocketClient_sendTXT(message);
        vTaskDelay(pdMS_TO_TICKS(200));
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

    String caller_password = FPSTR(auth_password);
    message = String(Caller_Number) + ",auth," + caller_password;
    updateSystemState(STATE_TRANS);
    webSocketClient_sendTXT(message);
    vTaskDelay(pdMS_TO_TICKS(200));

    sprintf(bssid, "%02X:%02X:%02X:%02X:%02X:%02X", WiFi.BSSID()[0], WiFi.BSSID()[1], WiFi.BSSID()[2], WiFi.BSSID()[3], WiFi.BSSID()[4], WiFi.BSSID()[5]);
    message = String(Caller_Number) + ",info," + "'SSID:" + String(WiFi.SSID()) + " ; RSSI:" + String(WiFi.RSSI()) + "dBm" + " ; BSSID:" + String(bssid) + " ; IP:" + String(WiFi.localIP().toString()) + " ; APIP:" + String(WiFi.softAPIP().toString()) + " ; Ver:" + String(Version) + "'";
    updateSystemState(STATE_TRANS);
    webSocketClient_sendTXT(message);
    vTaskDelay(pdMS_TO_TICKS(200));

    message = String(Caller_Number) + ",get";
    updateSystemState(STATE_TRANS);
    Serial.println("查詢最新叫號號碼!");
    webSocketClient_sendTXT(message);
    vTaskDelay(pdMS_TO_TICKS(200));
  }
}

// 發送 WebSocket 訊息
void sendWebSocketMessage(int value) {
  String message = "";
  check_auth();
  message = String(Caller_Number) + ",send," + String(value);
  updateSystemState(STATE_TRANS);
  bool success = webSocketClient_sendTXT(message);

  if (success) {
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
    sendTime = millis();
    waitingResponse = true;
    retryMode = false;
    Serial.printf(" 傳送：%s ", message.c_str());
  } else {
    updateSystemState(STATE_WEBSOCKET_CONNECTING);
    retryValue = value;
    retryMode = true;
    waitingResponse = false;
    Serial.println("傳送失敗，立即嘗試重新連接 WebSocket");
    webSocketClient.disconnect();
    vTaskDelay(pdMS_TO_TICKS(500));
    setupWebSocket();
  }
}

// 檢查回應
void checkResponse() {
  if (waitingResponse) {
    if (millis() - sendTime >= retryTimeout * 2000) {
      waitingResponse = false;
      retryMode = true;
      retryValue = num_buffer[(num_tail == 0) ? NUM_BUFFER_SIZE - 1 : num_tail - 1];
      Serial.println("回應超時，啟動重試機制");

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
    static int timeoutCount = 0;
    timeoutCount = 0;
  }
}

void num_LED_dis(const String& message) {
  nowStr = message;
  nowStrDemo = nowStr;
  if (bypassLast) {
    lastSendStr = "000";
    bypassLast = false;
  } else {
    lastSendStr = sendStr;
  }
  sendStr = message;
  VB8_Send(message.toInt());
}

// WiFi 模式切換
const int CODE1_PART1 = 159;
const int CODE1_PART2 = 357;
const int CODE2_PART1 = 357;
const int CODE2_PART2 = 159;

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

void change_AP_mode() {
  if (AP_mode_now == AP_mode) {
    return;
  }
  Serial.printf("切換 AP 到模式 %i\n", AP_mode);
  AP_mode_now = AP_mode;
  if (ESP.getFreeHeap() < 20000) {
    Serial.println("警告: 記憶體不足，延遲切換");
    delay(1000);
    if (ESP.getFreeHeap() < 15000) {
      Serial.println("記憶體嚴重不足，重啟系統");
      ESP.restart();
      return;
    }
  }
  if (AP_mode == 1) {
    setupAP();
  } else {
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
      if (millis() - stateEnterTime > 30000) {
        currentState = IDLE;
        Serial.println("Timeout waiting for second code");
        break;
      }

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
        currentState = IDLE;
        Serial.println("Invalid code combination");
      }
      break;

    case ACTIVE_MODE:
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

void VB8_Send(unsigned long num) {
  if (num < 1000) {
    bool ok = ma_set_data(int(num));
    cldNum = num;
  }
}

unsigned long last_VB8_KB_read = millis();

bool VB8_Recv() {
  bool result = false;

  if ((millis() - last_VB8_KB_read) >= 100) {
    Serial.print("VB8_Recv 間隔時間過大?");
    Serial.println((millis() - last_VB8_KB_read));
  }
  last_VB8_KB_read = millis();

  int b = ma_get_data();

  if (b >= 0) {
    String ss = "[MSG_VB8] VB8 rev data " + String(b);
    Serial.println(ss);
    nowStr = String(b);
    result = true;
  }
  return result;
}

// 初始化函數
void setup() {
  Serial.begin(115200);
  startTime = millis();

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

  strcpy(Caller_SSID, Caller_Prefix);
  strcat(Caller_SSID, Caller_Number.c_str());
  strncpy(defaultNetworks[0].ssid, Caller_SSID, sizeof(defaultNetworks[0].ssid) - 1);
  defaultNetworks[0].ssid[sizeof(defaultNetworks[0].ssid) - 1] = '\0';
  strncpy(defaultNetworks[0].password, "88888888", sizeof(defaultNetworks[0].password) - 1);
  defaultNetworks[0].password[sizeof(defaultNetworks[0].password) - 1] = '\0';

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  initLedConfigs();

  redTimer = xTimerCreate("RedLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].red, blinkLED);
  greenTimer = xTimerCreate("GreenLEDTimer", pdMS_TO_TICKS(100), pdTRUE, &ledConfigs[STATE_INIT].green, blinkLED);
  xTimerStart(redTimer, 0);
  xTimerStart(greenTimer, 0);

  updateSystemState(STATE_INIT);

  Serial.printf("WiFi 設定到 %i 模式!\n", WIFI_AP_STA);
  WiFi.mode(WIFI_AP_STA);
  setupAP();

  delay(200);
  AP_mode = 0;

  WiFi.setSleep(false);

  loadNetworks();
  mergeDefaultNetworks();

  server.on("/cmb", HTTP_GET, cmb_handleRoot);
  server.on("/cmb_store", HTTP_POST, handleStore);
  server.on("/cmb_retrieve", HTTP_GET, handleRetrieve);
  server.begin();

  updateSystemState(AP_mode == 1 ? STATE_AP_STA : STATE_WIFI_CONNECTING);
  Serial.println("\nSetup finish!");
  Serial.println("----------------------------------\n\n");

  setup_x();
}

void loop_VB8() {
  static unsigned long lastStatusTime = 0;
  currentMillis = millis();

  scanWiFiInBackground();
  attemptWiFiConnect();

  if (WiFi.status() == WL_CONNECTED) {
    if (!WebSocket_init) {
      WebSocket_init = true;
      setupWebSocket();
    }
    webSocketClient.loop();
  }

  server.handleClient();

  GetSendCallerNumber(currentMillis);

  if (currentMillis - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentMillis;
    sendBufferedData();
  }

  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastStatusTime >= STATUS_INTERVAL) {
      lastStatusTime = millis();
      Serial.print(" D");
    }
    if (lastDisconnectTime == 0) {
      lastDisconnectTime = millis();
      digitalWrite(LED_PIN, LOW);
      Serial.printf("WiFi 連接中斷!(%d dBm)\n", WiFi.RSSI());
      WiFi.disconnect(false, false);
      int scan_delay = 0;
      Serial.printf("scannedNetworks.size()=%d\n", scannedNetworks.size());
      if (scannedNetworks.size() <= 0) {
      } else {
        scan_delay = 5000;
        Serial.printf("WiFi 連接中斷, 設定 %d 秒後 WiFi 掃描!", scan_delay / 1000);
        lastScanTime = millis() - SCAN_INTERVAL + scan_delay;
        lastScanTimeRun = lastScanTime - SCAN_MIN_INTERVAL;
      }
    } else if (millis() - lastDisconnectTime > RECONNECT_DELAY) {
      lastDisconnectTime = millis();
    }
  } else {
    if (millis() - lastStatusTime >= STATUS_INTERVAL) {
      lastStatusTime = millis();
      if (webSocketClient.isConnected()) {
        Serial.print(" C");
      } else {
        Serial.print(" Cd");
      }
    }
    lastDisconnectTime = 0;
    digitalWrite(LED_PIN, HIGH);
    check_auth();
  }
}

void loop() {
  delay(100);
}