// 定義 Local_Test，當你想切換Server時，改變這裡
#define LOCAL_TEST  // 使用 Local Server，註解掉這行就會使用遠端Server

// credentials.h
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

// struct WiFiNetwork {
//   const char* ssid;
//   const char* password;
//   bool isValid;        // 表示該 AP 是否被認為有效
//   int signalStrength;  // 保存掃描到的訊號強度 (RSSI)
// };

struct WiFiNetwork {
  // char ssid[32];
  // char password[64];
  const char* ssid;
  const char* password;
  bool enabled;
  int8_t rssi;
  bool isUserAdded;  // 標記是否為用戶新增的網路
};

struct WebSocketServerConfig {
  const char* host;  // 伺服器網址
  uint16_t port;     // 端口
  bool useSSL;       // 是否使用 SSL (WSS)
};

#ifdef LOCAL_TEST
// WiFiNetwork defaultNetworks[] = {
//   { "CMBxxxxx", "88888888", true, 0 },
//   { "CMB00000", "88888888", true, 0 },  // ***** 必須 local network! *****
//   { "CMBz6666", "88888888", true, 0 },
//   { "xxxxxxxx", "xxxxxxx", false, 0 }
// };

WiFiNetwork defaultNetworks[] = {
  { "CMBzxxxx", "88888888", true, 0, false },
  { "CMB00000", "88888888", true, 0, false },  // ***** 必須 local network! *****
  { "CMBz6666", "88888888", true, 0, false }   // ***** 必須 local network! *****
  // { "xxxxxxxx", "88888888", true, 0, false }
};
// 定義多個 WebSocket 伺服器
WebSocketServerConfig servers[] = {
  // { "192.168.1.10", 38000, false }                    // WS, LOCAL
  { "cmb-caller-frontend-306511771181.asia-east1.run.app", 443, true }  // WSS Trila
  // { "cmb-caller-frontend-410240967190.asia-east1.run.app", 443, true }  // WSS Live
  // { "cmb-front-end.callmeback.com.tw", 8765, false }                    // WS, VM DNS 轉址
};

#else  // not LOCAL_TEST

// WiFiNetwork defaultNetworks[] = {
//   { "CMBzxxxx", "88888888", true, 0 },
//   { "CMB00000", "88888888", true, 0 },
//   { "CMBz6666", "88888888", true, 0 },
//   { "CMBz8888", "88888888", true, 0 },
//   { "xxxxxxxx", "xxxxxxx", false, 0 }
// };

WiFiNetwork defaultNetworks[] = {
  { "CMBzxxxx", "88888888", true, 0, false },
  { "CMB00000", "88888888", true, 0, false },
  { "CMBz6666", "88888888", true, 0, false },
  { "CMBz8888", "88888888", true, 0, false }
};

// 定義多個 WebSocket 伺服器
WebSocketServerConfig servers[] = {
  { "cmb-caller-frontend-410240967190.asia-east1.run.app", 443, true }  // WSS Live
  // { "cmb-caller-frontend-306511771181.asia-east1.run.app", 443, true }  // WSS Trila
  // { "cmb-front-end.callmeback.com.tw", 8765, false }                    // WS, VM DNS 轉址
  // { "192.168.1.10", 38000, false }                    // WS, LOCAL
  // { "backup-websocket-server.com", 8080, false }                         // 備用 WS
};

#endif

// WiFi 網路列表
const int defaultNetworkCount = sizeof(defaultNetworks) / sizeof(defaultNetworks[0]);  // IP器數量

// WebSocket 伺服器列表
const int SERVER_COUNT = sizeof(servers) / sizeof(servers[0]);  // WebSocket Server 數量

// # ASTRO_cmb-caller
String caller_password = "liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ=";

#endif