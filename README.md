# cmb-caller
This project is a hardware/software sub-system for project CallMeBack.

_Copyright by Astro Corp._

## Key componenets and Terms
1. Caller (終端設備): 外觀包含一高亮度數字顯示器、以及一分離式鍵盤，安裝於商家現場。 商家能透過鍵盤輸入號碼並將其即時顯示於數字顯示器上。
2. Caller module (終端內嵌模組) 與 Caller ID: 內嵌於 **Caller** 內的單晶片模組 (考慮使用 ESP32)。主要功能是監視數字顯示器內容(數字)，然後將內容(數字)傳遞給中央。每個 **Caller module** 都有一唯一 ID.
3. Caller flash burning (程式燒錄): 燒錄程式碼至 **Caller module** 的 flash 內。
4. Caller ID generator (Caller ID 產生器): 產生/獲得一新 **Caller ID** 並儲存至 **Caller module** 的 flash 內。
5. Setting APP ("設定 App") or Browser (簡稱: "終端設備設定UI/Web" 或 "終端內嵌模組設定UI/Web"): 對特定 **Caller module** 進行相關設定。
6. Caller management web (Caller 後臺管理網頁): 執行於雲端, 提供 **Caller** 與 **Vendor** 連結管理 UI。此部分由 **CallMeBack系統** 提供。
7. 號碼接收 Service: 執行於雲端, 接受 **Caller module** 登入以及接收傳來的相關資訊. 資訊內容主要為目前號碼回報.
8. CallMeBack Caller API: 一組 API 供 "號碼接收 service" 呼叫, 用來將目前叫號機資訊(數字) 傳遞給 **CallMeBack系統**. 此 API 由 **CallMeBack系統** 提供。
9. Vendor 與 Vendor ID: 表示商家以及用來代表此商家的唯一 ID.

## Operation flows
1. 燒綠與設定 **Caller ID**: Burn program and configure unique **Caller ID** into flash of caller module.
2. 建立 **Caller** 與 **Vendor** 連結: Bind Caller with a specific Vendor in Caller management console (web UI).
3. Install **Caller** in Vendor spot: 於商家現場進行硬體相關安裝。
4. Setting **Caller module**: 透過執行與手機上的 **Setting App**，與 **Caller module** 連線並進行相關設定.
5. Monitor and Report: **Caller module** 持續監視數字顯示器號碼並即時回報給中央系統。

## Announcements
- Official website: https://www.callmeback.com.tw
- Line official: "叫叫我" @callmeback https://line.me/R/ti/p/@787vjeld
- Line official customer service: "叫叫我(官方客服)" https://line.me/R/ti/p/@502njbyc
- Github: 本專案 GibHub 網站 https://github.com/Astro-RD2/cmb-caller
- Mother project CallMeBack Github: 母專案 Github 網站. https://github.com/callmeback-org/callmeback

## Third Party

## Software Platform
1. Most programs are coded in C and Python.
2. GCP technologies/services used - Cloud Run, Cloud Storage.
3. Containers are run in form of Cloud Run on Google Cloud Platform.

## How to set up local environment
```
$ git clone https://github.com/Astro-RD2/cmb-caller.git
$ cd cmb-caller
```

2025/1/6 Created by Chance Hsu
