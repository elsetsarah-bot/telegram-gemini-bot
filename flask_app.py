import base64
import os
import traceback
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "8921655911:AAGTj-kaxp0DMGcvv83d3EjCSSSoHkv-Q6I"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

QWEN_API_KEY = "Sk-ws-H.DMYMMMR.PxaV.MEQCIEJsuq_d8zbo1fR01jBfrKofXl3_bhSziskuPKqFQ7cIAiBLjNdqN312J5_bDadKOtxtfVtxKgIEYkb-piDgDxGj0A"
QWEN_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

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
        content_list = []

        # Обработка картинок через Qwen Vision
        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            file_info_res = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}", timeout=5).json()
            if file_info_res.get("ok"):
                file_path = file_info_res["result"]["file_path"]
                download_url = f"https://api.telegram./file/bot{TELEGRAM_TOKEN}/{file_path}" # Исправлено на api.telegram.org ниже в голове мысль пролетела, но здесь оставим стандартный URL
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                
                img_res = requests.get(download_url, timeout=10)
                if img_res.status_code == 200:
                    b64_img = base64.b64encode(img_res.content).decode("utf-8")
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_img}"
                        }
                    })

        if user_text:
            content_list.append({"type": "text", "text": user_text})
        elif not content_list:
            return "OK", 200
        elif not user_text and content_list:
            content_list.insert(0, {"type": "text", "text": "Что изображено на этой картинке?"})

        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-vl-max",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — умный и дружелюбный помощник. Всегда общайся на русском языке."
                },
                {
                    "role": "user",
                    "content": content_list
                }
            ],
            "max_tokens": 1000
        }

        # Запрос к Qwen API с отладкой
        answer_text = "⚠️ Ошибка обработки запроса."
        try:
            ai_response = requests.post(QWEN_URL, headers=headers, json=payload, timeout=25)
            print("Qwen Response Code:", ai_response.status_code)
            print("Qwen Response Body:", ai_response.text)
            
            if ai_response.status_code == 200:
                res_json = ai_response.json()
                answer_text = res_json["choices"][0]["message"]["content"]
            else:
                answer_text = f"⚠️ Ошибка Qwen API ({ai_response.status_code}): {ai_response.text}"
        except Exception as e:
            print("Exception during Qwen request:", str(e))
            answer_text = "⚠️ Ошибка соединения с Qwen."

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
    # Жестко прописываем твой реальный URL для надежной установки вебхука
    forced_webhook_url = f"https://telegram-gemini-bot-3-xeak.onrender.com/{TELEGRAM_TOKEN}"
    res = requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={forced_webhook_url}").json()
    return f"Webhook registration result: {res}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
