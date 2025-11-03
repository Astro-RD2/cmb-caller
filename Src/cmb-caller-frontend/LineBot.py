# 2025/09/01 OK


from linebot.v3.messaging import MessagingApi, ApiClient, Configuration
from linebot.v3.messaging.models import PushMessageRequest, TextMessage
from datetime import datetime

class LineNotifier:
    def __init__(self):
        # LINE BOT Token
        self.channel_access_token = "vcClHW6zeF2V/nBoWQtDR7XiSOl98/uqK0s615RbKXHkGeRS3l2TTAZVQr3DjIE+l3yzEHydaekwMRapABOGcvrX7BX7mJsV4XKKRdO/x2nPGKz4f9conu09LbPQQFylNn/VvZONdEwmNEvaiDxo2QdB04t89/1O/w1cDnyilFU="

        # 使用 Configuration 初始化 MessagingApi
        configuration = Configuration(access_token=self.channel_access_token)
        
        # 使用正確的API客戶端初始化
        api_client = ApiClient(configuration)
        self.messaging_api = MessagingApi(api_client)

        # 事件設定檔
        self.settings = {
            "event_1": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"}
                ],
                "template": "📢 第 {count} 次通知\n🕒 時間：{time}\n📋 狀態：{status}\n👤 收件人：{name}"
            },
            "event_2": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"}
                ],
                "template": "🔔 通知 {count} 次\n🕒 {time}\n📊 狀態：{status}\n👥 給：{name}"
            }
        }

    def send_event_message(self, event_key, count, status):
        event = self.settings.get(event_key)
        if not event:
            print(f"❌ 找不到事件設定：{event_key}")
            return False

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = event["template"]
        recipients = event["recipients"]

        result = False
        for user in recipients:
            try:
                message_text = template.format(
                    count=count,
                    time=current_time,
                    status=status,
                    name=user["name"]
                )

                # 修正API調用方式
                push_message_request = PushMessageRequest(
                    to=user["id"],
                    messages=[TextMessage(text=message_text)]
                )
                
                # 正確調用API方法
                response = self.messaging_api.push_message(push_message_request)
                print(f"✅ 已發送給 {user['name']}, 回應: {response}")
                result = True
            except Exception as e:
                print(f"❌ 發送給 {user['name']} 失敗: {str(e)}")
        return result

# ✅ 使用範例
if __name__ == "__main__":
    notifier = LineNotifier()
    send_result = notifier.send_event_message("event_1", count=1, status="系統正常")
    print(f"1 success {send_result}")
    send_result = notifier.send_event_message("event_2", count=2, status="資料同步中")
    print(f"2 success {send_result}")




'''

from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime
class LineNotifier:
    def __init__(self):
        # LINE BOT Token
        self.channel_access_token = "vcClHW6zeF2V/nBoWQtDR7XiSOl98/uqK0s615RbKXHkGeRS3l2TTAZVQr3DjIE+l3yzEHydaekwMRapABOGcvrX7BX7mJsV4XKKRdO/x2nPGKz4f9conu09LbPQQFylNn/VvZONdEwmNEvaiDxo2QdB04t89/1O/w1cDnyilFU="
        self.line_bot_api = LineBotApi(self.channel_access_token)

        # 事件設定檔
        self.settings = {
            "event_1": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"},
                    # {"id": "U95547b7b9b1226f08563825c7f8db533", "name": "Jando"}
                ],
                "template": "📢 第 {count} 次通知\n🕒 時間：{time}\n📋 狀態：{status}\n👤 收件人：{name}"
            },
            "event_2": {
                "recipients": [
                    {"id": "U0bbec15cbf5eadf5d39e9a9182c6a47e", "name": "Roy"},
                    # {"id": "U95547b7b9b1226f08563825c7f8db533", "name": "Jando"},
                    # {"id": "Ubfd6afe6fc674dd60bb7712e3a0681b5", "name": "Alvin"},
                    # {"id": "U925476ebe228a22175cfcc499cec617e", "name": "Sam"},
                    # {"id": "Ud9dfd12cfadcfa768c33c51a9c07b2d2", "name": "李大涵 "},
                    # {"id": "U90ed94e344db6b2014cc1b3f29adbfe3", "name": "客服"}
                ],
                "template": "🔔 通知 {count} 次\n🕒 {time}\n📊 狀態：{status}\n👥 給：{name}"
            }
        }

    def send_event_message(self, event_key, count, status):
        event = self.settings.get(event_key)
        if not event:
            print(f"❌ 找不到事件設定：{event_key}")
            return

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = event["template"]
        recipients = event["recipients"]
        
        result = False
        for user in recipients:
            try:
                message_text = template.format(
                    count=count,
                    time=current_time,
                    status=status,
                    name=user["name"]
                )
                self.line_bot_api.push_message(user["id"], TextSendMessage(text=message_text))
                print(f"✅ 已發送給 {user['name']}")
                result = True
            except Exception as e:
                print(f"❌ 發送給 {user['name']} 失敗: {e}")
        return result

# ✅ 使用範例
notifier = LineNotifier()
send_result = notifier.send_event_message("event_1", count=1, status="系統正常")
print(f"1 success {send_result}")
send_result = notifier.send_event_message("event_2", count=2, status="資料同步中")
print(f"2 success {send_result}")

'''

