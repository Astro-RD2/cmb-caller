# cmb-caller
This project is a hardware/software system for project CallMeBack.

_Copyright by Astro Corp._

## Before delivery caller module
- Burn program and configure unique caller ID into flash of caller module.
```
[Windows PC]
+------------------------+      +----------------+
|Caller flash burning    |----->|Caller module   |
|                        | USB  |                |
|cmb-caller-burner       |      |(invalid/empty) |
+------------------------+      +----------------+

[Windows PC]
+------------------------+      +---------------+
|Caller ID generator     |----->|Caller module  |
|                        | USB  |               |
|cmb-caller-id-generator |      |cmb-caller     |
+------------------------+      +---------------+
```
- Add the new caller ID into CallMeBack database and bind it with a specific vendor in management console (web UI).
```
[PC/Browser]         [Cloud / Service]
+-------------+      +----------------+
|Browser      |----->| Management web |
|             |      |                |
|             |      |                |
+-------------+      +----------------+
```

## Set up caller module on site
- Use the "Setting App" run on mobile phone to configure the WIFI parameters, e.g. SSID/Password, and something into caller module.
```
[Vendor spot]                                          [Cloud / GCP]
======================================                 ==============
                                                       [Cloud / Service]
+---------------+                                      +---------------------+ 
|Caller module  |           +----------+               |Service              |    API of
|               |-- Wifi -->| Wifi AP  |-- Internet -->|                     |--> CallMeBack sys
|cmb-caller     |           +----------+               |cmb-caller-frontend  |
+---------------+                                      +---------------------+
    ^
    |
    |WiFi direct (Setting SSID) or
    |Bluetooth
    |
+------------------------+
|Setting App (on Phone)  |
|                        |
|cmb-caller-setting-app  |
+------------------------+
```

## Announcements
- Official website: https://www.callmeback.com.tw
- Line official: "叫叫我" @callmeback https://line.me/R/ti/p/@787vjeld
- Line official customer service: "叫叫我(官方客服)" https://line.me/R/ti/p/@502njbyc
- Github: https://github.com/Astro-RD2/cmb-caller
- Project CallMeBack Github: https://github.com/callmeback-org/callmeback

## Third Party

## Software Platform
1. Most programs are coded in C and Python.
2. GCP technologies/services used - Cloud Run, Cloud Storage, Firebase
3. Containers are run in form of Cloud Run on Google Cloud Platform.

## How to set up local environment
```
$ git clone https://github.com/Astro-RD2/cmb-caller.git
$ cd pre-callmeback
```

2025/1/6 Created by Chance Hsu
