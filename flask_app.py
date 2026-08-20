import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Полные учетные данные
TOKEN = "8921655911:AAGTj-kaxp0DMGcvv83d3EjCSSSoHkv-Q6I"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

CLOUDFLARE_ACCOUNT_ID = "93999d5bc0b9338893c1c5c4336f8470"
CLOUDFLARE_AUTH_TOKEN = "cfat_QuOS5b4bJLnOlmGxQmeryEUDXXc8F7GhAlh0AWphfd95afad"
CLOUDFLARE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return "OK", 200

        message = data["message"]
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return "OK", 200

        user_text = message.get("caption") or message.get("text", "")

        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {}

        # Проверяем наличие фото
        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_info_res = requests.get(file_info_url, timeout=5).json()
            
            if file_info_res.get("ok"):
                file_path = file_info_res["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                
                img_res = requests.get(download_url, timeout=10)
                if img_res.status_code == 200:
                    image_array = list(bytes(img_res.content))
                    payload = {
                        "messages": [
                            {"role": "system", "content": "Ты — умный и дружелюбный помощник. Всегда общайся на русском языке."},
                            {"role": "user", "content": user_text if user_text else "Что изображено на этой картинке?"}
                        ],
                        "image": image_array
                    }

        # Если фото нет — обычный текст
        if not payload:
            if not user_text:
                return "OK", 200
            payload = {
                "messages": [
                    {"role": "system", "content": "Ты — умный и дружелюбный помощник. Всегда общайся на русском языке."},
                    {"role": "user", "content": user_text}
                ]
            }

        # Запрос к Cloudflare AI
        try:
            ai_response = requests.post(CLOUDFLARE_URL, headers=headers, json=payload, timeout=25)
            if ai_response.status_code == 200:
                res_json = ai_response.json()
                answer_text = res_json.get("result", {}).get("response", "Пустой ответ от нейросети.")
            else:
                answer_text = f"⚠️ Ошибка API Cloudflare: {ai_response.text}"
        except Exception:
            answer_text = "⚠️ Ошибка соединения с Cloudflare AI."

        # Отправка ответа в Телеграм
        send_url = f"{TELEGRAM_API_URL}/sendMessage"
        try:
            requests.post(send_url, json={"chat_id": chat_id, "text": answer_text}, timeout=5)
        except:
            pass

    except Exception:
        pass

    return "OK", 200

@app.route('/')
def index():
    render_url = request.host_url.rstrip('/')
    webhook_url = f"{render_url}/{TOKEN}"
    requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    return "Bot is running perfectly on Cloudflare AI!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
