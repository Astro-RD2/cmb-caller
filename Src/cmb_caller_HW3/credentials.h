// #define LOCAL_TEST

// credentials.h
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

struct WiFiNetwork {
  char ssid[32];
  char password[64];
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

WiFiNetwork defaultNetworks[] = {
  { "CMBzxxxx"    , "88888888", true, 0 , false },
  // { "DrayTek_M"    , "1qasde32", true, 0 , false },
  { "CMB00000", "88888888", true, 0 , false }
  // { "CMBz8888", "88888888", true, 0 , false }
  // { "CMBz6666", "88888888", true, 0 , false }
};


// 定義多個 WebSocket 伺服器
WebSocketServerConfig servers[] = {
  // { "cmb-caller-frontend-410240967190.asia-east1.run.app", 443, true }  // WSS Live
  { "cmb-caller-frontend-306511771181.asia-east1.run.app", 443, true }  // WSS Trila
  // { "192.168.1.10", 38000, false }                    // WS, LOCAL PC
};

// ========================================================================================================

#else  // not LOCAL_TEST

WiFiNetwork defaultNetworks[] = {
  { "CMBzxxxx", "88888888", true, 0, false },
  { "CMB00000", "88888888", true, 0, false },
  { "CMBz8888", "88888888", true, 0, false },
  { "CMBz6666", "88888888", true, 0, false }
};

// 定義多個 WebSocket 伺服器
WebSocketServerConfig servers[] = {
  { "cmb-caller-frontend-410240967190.asia-east1.run.app", 443, true }  // WSS Live
};

#endif

// WiFi 網路列表
const int defaultNetworkCount = sizeof(defaultNetworks) / sizeof(defaultNetworks[0]);  // IP器數量
// WebSocket 伺服器列表
const int SERVER_COUNT = sizeof(servers) / sizeof(servers[0]);  // WebSocket Server 數量
const char auth_password[] PROGMEM = "liM3yMfrMIAWHmFVvGQ1RA3BmdCTx2/hHdFbzv7ulcQ=";  // ASTRO_cmb-caller

#endif

