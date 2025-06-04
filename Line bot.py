from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# 你的 LINE 機器人金鑰
CHANNEL_ACCESS_TOKEN = 'ofjYBMQ0NxxzZ6yyvRtGRkdPpIhvIBCh1Jt9bhTosTS38qdcAxfffdU+oTRVQnTzJ/u0F3VWgWSKF/zLNHOSnIQyGgDuUJVOoduAVQRTTSlpAs/8yU+lyaf6mj2sFKlclD38ObZxPatk/MdR1j7j3gdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'e4306d91aba6cce87b00a5dcb50ce13e'

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def get_schedule_from_sheet(date_str):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    json_path = '/etc/secrets/optimum-credentials.json'  # Render Secret File 預設路徑
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key('15PEJqNlnVfePT7RyyxvtXGLu7QMjJz_A5V5eAKzkn_g').sheet1
    data = sheet.get_all_records()

    for row in data:
        if str(row['日期']) == date_str:
            return row['班表內容']
    return "查無排班資料"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()

    if msg.startswith("班表"):
        parts = msg.split(" ")
        if len(parts) == 2:
            date_query = parts[1]
        else:
            date_query = datetime.now().strftime("%Y-%m-%d")

        result = get_schedule_from_sheet(date_query)
        reply = f"{date_query} 的排班：\n{result}"
    else:
        reply = "查無此指令，可輸入：班表 或 班表 2025-06-04"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# Render 運行設定
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
