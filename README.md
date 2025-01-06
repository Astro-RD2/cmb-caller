# cmb-caller
This project is a hardware/software system for project CallMeBack https://github.com/KillbugChance/callmeback

_Copyright by Astro Corp._

## Before delivery caller module
- Burn program and configure unique caller ID into flash of caller module.
```
+--------------------+      +---------------+
|Caller ID generator |----->| Caller module |
|                    |      |               |
|                    |      | cmb-caller    |
+--------------------+      +---------------+
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
- Use the Setting App run on mobile phone to configure the WIFI parameters, e.g. SSID/Password), and something.
```
[Vendor]                                             [Cloud / GCP]
+---------------+                                    +--------------+ 
| Caller module |          +----------+              | Service      |    API of
|               |-- Wifi --| Wifi AP  |-- Internet --|              |--- CallMeBack
| cmb-caller    |          +----------+              | cmb-frontend |
+---------------+                                    +--------------+ 
    |
    |Wifi or Bluetooth
    |
 +--------------------+
 | Setting App        |
 |                    |
 | cmb-caller-setting |
 +--------------------+
```

## Announcements
- Official website: https://www.callmeback.com.tw
- Line: "叫叫我" @callmeback https://line.me/R/ti/p/@787vjeld
- Line customer service: "叫叫我(官方客服)" https://line.me/R/ti/p/@502njbyc
- Parent Github repository: https://github.com/ghjando/callmeback

## Third Party
- MainPi 免排: 為叫號機系統商, 公司為奇城科技.  https://www.mainpi.com
- 盈德科技

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
