import os
import traceback
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "8921655911:AAGTj-kaxp0DMGcvv83d3EjCSSSoHkv-Q6I"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Твой ключ Groq
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(silent=True)
        print("Received Telegram data:", data)
        if not data or "message" not in data:
            return "OK", 200

        message = data["message"]
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return "OK", 200

        user_text = message.get("caption") or message.get("text", "")
        if not user_text:
            if "photo" in message:
                user_text = "Что изображено на этой картинке?"
            else:
                return "OK", 200

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — умный и дружелюбный помощник. Всегда общайся на русском языке."
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            "max_tokens": 1000
        }

        # Запрос к Groq API
        answer_text = "⚠️ Ошибка обработки запроса."
        try:
            ai_response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            print("Groq Response Code:", ai_response.status_code)
            print("Groq Response Body:", ai_response.text)
            
            if ai_response.status_code == 200:
                res_json = ai_response.json()
                answer_text = res_json["choices"][0]["message"]["content"]
            else:
                answer_text = f"⚠️ Ошибка Groq API ({ai_response.status_code}): {ai_response.text}"
        except Exception as e:
            print("Exception during Groq request:", str(e))
            answer_text = "⚠️ Ошибка соединения с Groq."

        # Отправка ответа в Telegram
        send_url = f"{TELEGRAM_API_URL}/sendMessage"
        send_res = requests.post(send_url, json={"chat_id": chat_id, "text": answer_text}, timeout=5)
        print("Telegram Send Response:", send_res.text)

    except Exception as e:
        print("CRITICAL WEBHOOK ERROR:")
        traceback.print_exc()

    return "OK", 200

@app.route('/')
def index():
    forced_webhook_url = f"https://telegram-gemini-bot-3-xeak.onrender.com/{TELEGRAM_TOKEN}"
    res = requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={forced_webhook_url}").json()
    return f"Webhook registration result: {res}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
