import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
from io import BytesIO

app = Flask(__name__)

TELEGRAM_TOKEN = "8872470367:AAHllFF0b1c1KZgDkfY313q9bDPv0Vwf9lw"
GEMINI_API_KEY = "AQ.Ab8RN6KvC8bQmFuuy4tF2CCZJm-PI4ewNe0sL6WQ6YyKSPedbg"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def download_photo(file_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    response = requests.get(url).json()
    if not response.get("ok"):
        return None
    file_path = response["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    img_response = requests.get(file_url)
    return Image.open(BytesIO(img_response.content))

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user_text = msg.get("text", "")
        photo = None

        if "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            photo = download_photo(file_id)

        if user_text == "/start":
            send_message(chat_id, "Привет! Отправь фото с вопросом, и я проанализирую его.")

        elif photo and user_text:
            response = model.generate_content([user_text, photo])
            send_message(chat_id, response.text)

        elif photo:
            response = model.generate_content(["Опиши, что ты видишь на этом изображении", photo])
            send_message(chat_id, response.text)

        elif user_text:
            response = model.generate_content(user_text)
            send_message(chat_id, response.text)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
