// credentials.h
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

struct WiFiNetwork {
    const char* ssid;
    const char* password;
};

WiFiNetwork wifiNetworks[] = {
    { "", "" },
    { "R_A9", "88888888" },
    { "CMB66666", "88888888" }
};

#endif