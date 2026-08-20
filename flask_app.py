import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Твои данные
TELEGRAM_TOKEN = "8921655911:AAGTj-kaxp0DMGcvv83d3EjCSSSoHkv-Q6I"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
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
        if not user_text:
            return "OK", 200

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": "Ты — умный и дружелюбный помощник. Всегда общайся на русском языке."},
                {"role": "user", "content": user_text}
            ]
        }

        # Запрос к Groq API
        try:
            ai_response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            if ai_response.status_code == 200:
                res_json = ai_response.json()
                answer_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "Пустой ответ от нейросети.")
            else:
                answer_text = f"⚠️ Ошибка API Groq: {ai_response.text}"
        except Exception:
            answer_text = "⚠️ Ошибка соединения с Groq AI."

        # Отправка ответа в Telegram
        send_url = f"{TELEGRAM_API_URL}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": answer_text}, timeout=5)

    except Exception:
        pass

    return "OK", 200

@app.route('/')
def index():
    render_url = request.host_url.rstrip('/')
    webhook_url = f"{render_url}/{TELEGRAM_TOKEN}"
    requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    return "Bot is running perfectly on Groq AI!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
