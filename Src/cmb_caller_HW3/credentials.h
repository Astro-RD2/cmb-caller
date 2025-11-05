// 定義 Local_Test，當你想切換Server時，改變這裡
// #define LOCAL_TEST  // 使用 Local Server，註解掉這行就會使用遠端Server
// 直接使用鍵盤訊號訊號
// #define USE_KEYBOARD_SIGNAL


// credentials.h
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

// 定義 Local_Test，當你想切換Server時，改變這裡
// #define LOCAL_TEST  // 使用 Local Server，註解掉這行就會使用遠端Server

struct WiFiNetwork {
  const char* ssid;
  const char* password;
  bool isValid;        // 表示該 AP 是否被認為有效
  int signalStrength;  // 保存掃描到的訊號強度 (RSSI)
};

WiFiNetwork wifiNetworks[] = {
  { "CMBzxxxx", "88888888", true, 0 },
  { "CMB00000", "88888888", true, 0 },
  { "CMBz8888", "88888888", true, 0 },
  { "CMBz6666", "88888888", true, 0 }
};

// WiFi 網路列表
const int numNetworks = sizeof(wifiNetworks) / sizeof(wifiNetworks[0]);   // IP器數量

struct WebSocketServerConfig {
  const char* host;  // 伺服器網址
  uint16_t port;     // 端口
  bool useSSL;       // 是否使用 SSL (WSS)
};
// 定義多個 WebSocket 伺服器
WebSocketServerConfig servers[] = {
  { "cmb-caller-frontend-410240967190.asia-east1.run.app", 443, true }  // WSS Live
  // { "cmb-caller-frontend-306511771181.asia-east1.run.app", 443, true }  // WSS Trila
  // { "cmb-front-end.callmeback.com.tw", 8765, false }                    // WS
  // { "backup-websocket-server.com", 8080, false }                         // 備用 WS
};
const int SERVER_COUNT = sizeof(servers) / sizeof(servers[0]);  // WebSocket Server 數量


#endif