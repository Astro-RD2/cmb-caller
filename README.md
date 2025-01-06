# cmb-caller
This project is a hardware/software system for project CallMeBack https://github.com/KillbugChance/callmeback

_Copyright by Astro Corp._

## Manufacturer
Burn program and set caller ID into flash of caller module.
```
+--------------------+      +---------------+
|Caller ID generator |----->| Caller module |
|                    |      |               |
|                    |      | cmb-caller    |
+--------------------+      +---------------+
```

## Operation
  - Configure call ID and vendor ID in managemetn console (web).
  - Set up the caller module in the street.
    - Use the Setting App run on mobile phone to configure the Caller App the WIFI parameters (SSID/Password).
```
+---------------+          +----------+              +--------------+ 
| Caller module |          | Wifi AP  |              | Service      |    API of
|               |-- Wifi --|          |-- Internet --|              |--- CallMeBack
| cmb-caller    |          |          |              | cmb-frontend |
+---------------+          +----------+              +--------------+ 
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

## Third Party
- MainPi 免排: 為叫號機系統商, 公司為奇城科技.  https://www.mainpi.com
- 盈德科技

## Software Platform
1. Most programs are coded in C and Python.
   Others are coded in Python or Bash and are usually in form of scripts or standalone applications.
2. GCP technologies/modules used - Cloud Run, Cloud Storage, Firebase
3. Containers are run in form of Cloud Run on Google Cloud Platform.

## How to set up local environment
```
$ git clone https://github.com/Astro-RD2/cmb-caller.git
$ cd pre-callmeback
```

2025/1/6 Created by Chance Hsu
