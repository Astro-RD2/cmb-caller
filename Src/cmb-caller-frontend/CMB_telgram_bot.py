# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 10:31:22 2025

@author: RoyChing
"""
import requests

# === 設定 ===
# TOKEN = "123456789:ABCdefGhIjkLmNoPQRstuVWxyz12345678"  # 你的Bot Token
TOKEN = '7953139290:AAEFzEJpPK2DaUnUZEg6gOOMIYFdef9DZ84'
# CHAT_ID = "987654321"  # 你的Chat ID
CHAT_ID = '6597541679'
MESSAGE = "你好，這是從 Python 發送的訊息！"

# === 發送訊息 ===
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": MESSAGE
}

response = requests.post(url, data=payload)

# === 顯示結果 ===
if response.status_code == 200:
    print("✅ 訊息發送成功！")
else:
    print("❌ 發送失敗:", response.text)
