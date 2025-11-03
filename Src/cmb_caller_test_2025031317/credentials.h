// credentials.h
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

struct WiFiNetwork {
  const char* ssid;
  const char* password;
  bool isValid;        // 表示該 AP 是否被認為有效
  int signalStrength;  // 保存掃描到的訊號強度 (RSSI)
};

// 定義 Local_Test，當你想切換Server時，改變這裡
// #define LOCAL_TEST  // 使用 Local Server，註解掉這行就會使用遠端Server

#ifdef LOCAL_TEST
WiFiNetwork wifiNetworks[] = {
  { "CMBxxxxx", "88888888", true, 0 },
  { "CMB00000", "88888888", true, 0 },  // ***** 必須 local network! *****
  { "CMBz6666", "88888888", true, 0 },
  { "xxxxxxxx", "xxxxxxx", false, 0 }
};
#else
WiFiNetwork wifiNetworks[] = {
  { "CMBzxxxx", "88888888", true, 0 },
  { "CMB00000", "88888888", true, 0 },
  { "CMBz8888", "88888888", true, 0 },
  { "CMBz6666", "88888888", true, 0 },
  { "xxxxxxxx", "xxxxxxx", false, 0 }
};
#endif


// WiFiNetwork wifiNetworks[] = {
//   { "CMBxxxxx", "88888888", true, 0 },
//   { "CMBz888x", "88888888", true, 0 } // !!!@@@
// };


#endif