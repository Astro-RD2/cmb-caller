char Caller_Number[] = "z0001";
// char Caller_Number[] = "z0002";

#include <ArduinoWebsockets.h>
#include <Arduino.h>
#include <WiFi.h>
#include "credentials.h"

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
#define RLED 33
#define BLED 2

#define LLH 500

// 系統狀態枚舉
enum SystemState {
  STATE_INIT,
  STATE_WIFI_CONNECTING,
  STATE_WIFI_CONNECTED,
  STATE_WEBSOCKET_CONNECTING,
  STATE_WEBSOCKET_CONNECTED,
  STATE_ERROR
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

const int numNetworks = sizeof(wifiNetworks) / sizeof(wifiNetworks[0]);

// 網路相關定義
const char* websockets_server_host = "35.187.148.66";
const uint16_t websockets_server_port = 8765;

// 計時器和網路相關
const long WIFI_TIMEOUT = 7000;          // WiFi 連接超時時間 (10000)
const long WS_TIMEOUT = 5000;            // WebSocket 連接超時時間 (5000)
const long STATE_UPDATE_INTERVAL = 500;  // 狀態更新間隔 (500)
const long HEARTBEAT_INTERVAL = 30000;   // 心跳間隔 (3000)

// Caller 相關定義
const char Caller_Prefix[] = "CMB";
char Caller_SSID[sizeof(Caller_Prefix) + sizeof(Caller_Number) - 1];

// 系統變數
unsigned long lastHeartbeat = 0;
unsigned long delayStart = 0;
unsigned long ma_500ms_counter = 0;
byte led_light_en = 0;
int currentNetwork = 0;

// 數字顯示相關
int fe[3] = { 0 };
int n1 = -1, n2 = -1, n3 = -1;
int pn1 = -2, pn2 = -2, pn3 = -2;
volatile bool has_interrupted = false;
hw_timer_t* timer0;
String preStr = "";
String nowStr = "";
String sendStr = "";
int matchCt = 0;

using namespace websockets;
WebsocketsClient client;

// 更新系統狀態
void updateSystemState(SystemState newState, const String& error = "") {
  status.state = newState;
  status.lastStateChange = millis();
  if (error.length() > 0) {
    status.lastError = error;
    Serial.println("\nError: " + error);
  }

  // 更新 LED 狀態
  switch (newState) {
    case STATE_INIT:
      digitalWrite(RLED, HIGH);  // 紅燈亮
      digitalWrite(BLED, LOW);   // 綠燈滅
      break;
    case STATE_WIFI_CONNECTING:
      digitalWrite(RLED, !digitalRead(RLED));  // 快速閃爍
      digitalWrite(BLED, !digitalRead(BLED));  // 快速閃爍
      break;
    case STATE_WIFI_CONNECTED:
      digitalWrite(RLED, LOW);   // 紅燈滅
      digitalWrite(BLED, HIGH);  // 綠燈亮
      break;
    case STATE_WEBSOCKET_CONNECTING:
      digitalWrite(RLED, !digitalRead(RLED));  // 慢速閃爍
      digitalWrite(BLED, !digitalRead(BLED));  // 慢速閃爍
      break;
    case STATE_WEBSOCKET_CONNECTED:
      digitalWrite(RLED, LOW);   // 紅燈滅
      digitalWrite(BLED, HIGH);  // 綠燈亮
      break;
    case STATE_ERROR: // 不變動LED，以免影響其它狀態顯示.
      // digitalWrite(RLED, HIGH);  // 紅燈亮 
      // digitalWrite(BLED, LOW);   // 綠燈滅
      break;
  }
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

// WiFi 連接函數
bool connectToWiFi(const char* ssid, const char* pwd) {
  updateSystemState(STATE_WIFI_CONNECTING);
  status.currentSSID = ssid;

  WiFi.begin(ssid, pwd);
  Serial.printf("Connecting to WiFi: %s\n", ssid);

  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startTime > WIFI_TIMEOUT) {
      updateSystemState(STATE_ERROR, "WiFi connection timeout");
      status.wifiAttempts++;
      return false;
    }
    Serial.printf(".");
    delay(100);  // LED
    updateSystemState(STATE_WIFI_CONNECTING);
  }
  Serial.printf("\nConnected to WiFi. SSID: %s, IP: %s\n", ssid, WiFi.localIP().toString().c_str());
  updateSystemState(STATE_WIFI_CONNECTED);
  status.wifiAttempts = 0;
  return true;
}

// WebSocket 連接函數
bool connectToWebSocket() {
  updateSystemState(STATE_WEBSOCKET_CONNECTING);

  bool connected = client.connect(websockets_server_host, websockets_server_port, "/");
  if (connected) {
    Serial.println("Connected to WebSocket server");
    updateSystemState(STATE_WEBSOCKET_CONNECTED);
    status.websocketAttempts = 0;
    return true;
  }

  updateSystemState(STATE_ERROR, "WebSocket connection failed");
  status.websocketAttempts++;
  return false;
}

// 中斷處理函數
void IRAM_ATTR handleInterrupt() {
  has_interrupted = true;
  const int enablePins[3] = { LED_1e, LED_2e, LED_3e };
  int* numbers[3] = { &n1, &n2, &n3 };

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
    if (nowStr == preStr) {
      matchCt++;
    } else {
      matchCt = 1;
    }

    preStr = nowStr;

    if (matchCt >= 3) {
      if (pn1 != n1 || pn2 != n2 || pn3 != n3) {
        pn1 = n1;
        pn2 = n2;
        pn3 = n3;

        if (nowStr != sendStr && client.available()) {
          String message = String(Caller_Number) + "," + nowStr;
          Serial.println("Send: " + message);
          client.send(message);
          sendStr = nowStr;
        }
        matchCt = 0;
      }
    }
    n1 = n2 = n3 = -1;
  }
  has_interrupted = false;
}

// 檢查連接狀態
void checkConnections() {
  // 檢查 WiFi 連接
  Serial.print("_");
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi.status() != WL_CONNECTED");
    if (status.state != STATE_WIFI_CONNECTING) {
      Serial.println("status.state != STATE_WIFI_CONNECTING");
      bool result = connectToWiFi(wifiNetworks[currentNetwork].ssid, wifiNetworks[currentNetwork].password);
      if (!result)  // 如果連線成功，如斷線先繼續試此一 SSID.
        currentNetwork = (currentNetwork + 1) % numNetworks;
    }
    return;
  }

  // 檢查 WebSocket 連接
  if (!client.available()) {
    if (status.state != STATE_WEBSOCKET_CONNECTING) {
      connectToWebSocket();
      delay(500);
    }
    return;
  }

  // 發送心跳
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    client.send("ping");
    lastHeartbeat = millis();
  }

  client.poll();
}

// 初始化函數
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n\n----------------------------------\n");
  updateSystemState(STATE_INIT);

  // 初始化 Caller_SSID
  strcpy(Caller_SSID, Caller_Prefix);
  strcat(Caller_SSID, Caller_Number);
  wifiNetworks[0].ssid = Caller_SSID;
  wifiNetworks[0].password = "88888888";

  // IO 初始化
  pinMode(RLED, OUTPUT);
  pinMode(BLED, OUTPUT);
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
  bool result = false;
  for (int i = 0; i < numNetworks; i++) {
    delay(500);
    currentNetwork = i;
    result = connectToWiFi(wifiNetworks[i].ssid, wifiNetworks[i].password);
    if (result) {
      break;
    }
  }
  if (result == false)
    currentNetwork = 0;

  // WebSocket 消息處理
  client.onMessage([](WebsocketsMessage message) {
    Serial.println("Received: " + message.data());
  });
  Serial.println("Setup finish!");
}

// 主循環
void loop() {
  static unsigned long lastCheck = 0;
  unsigned long currentMillis = millis();

  // 定期檢查連接狀態
  if (currentMillis - lastCheck >= STATE_UPDATE_INTERVAL) {
    lastCheck = currentMillis;
    checkConnections();
  }

  // 處理 Caller 數字發送
  sendCallerNumber();

  // 檢查重置按鈕
  if (digitalRead(0) == 0) {
    Serial.println("IO0 button pressed");
  }
}