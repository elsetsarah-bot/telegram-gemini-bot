import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

TELEGRAM_TOKEN = "8872470367:AAHllFF0b1c1KZgDkfY313q9bDPv0Vwf9lw"
GEMINI_KEY = "AQ.Ab8RN6KvC8bQmFuuy4tF2CCZJm-PI4ewNe0sL6WQ6YyKSPedbg"

# Настройка Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text):
    """Отправка сообщения пользователю Telegram."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

def download_telegram_file(file_id):
    """Получение байтов фото из Telegram без использования Pillow."""
    file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
    res = requests.get(file_info_url).json()
    if not res.get("ok"):
        return None, None

    file_path = res["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    
    file_bytes = requests.get(file_url).content
    
    # Определение mime-типа по расширению
    mime_type = "image/jpeg"
    if file_path.endswith(".png"):
        mime_type = "image/png"
    elif file_path.endswith(".webp"):
        mime_type = "image/webp"
        
    return file_bytes, mime_type

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return jsonify({"status": "ok"}), 200

    message = update["message"]
    chat_id = message["chat"]["id"]

    # 1. Обработка команд /start и /help
    text = message.get("text", "")
    if text == "/start":
        send_message(chat_id, "Привет! Я бот на базе Google Gemini. Отправь мне любой текст или фото с вопросом.")
        return jsonify({"status": "ok"}), 200

    if text == "/help":
        send_message(chat_id, "Команды:\n/start — перезапуск бота\n/help — помощь\n\nВы можете отправить текст или картинку с подписью.")
        return jsonify({"status": "ok"}), 200

    try:
        # 2. Обработка фото
        if "photo" in message:
            # Берём фото наибольшего разрешения (последнее в списке)
            file_id = message["photo"][-1]["file_id"]
            caption = message.get("caption", "Что изображено на этом фото?")

            image_bytes, mime_type = download_telegram_file(file_id)
            if not image_bytes:
                send_message(chat_id, "Не удалось загрузить изображение.")
                return jsonify({"status": "ok"}), 200

            # Передаем байты напрямую в Gemini без Pillow
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }
            
            response = model.generate_content([caption, image_part])
            send_message(chat_id, response.text)

        # 3. Обработка обычного текста
        elif text:
            response = model.generate_content(text)
            send_message(chat_id, response.text)

    except Exception as e:
        send_message(chat_id, f"Произошла ошибка при обработке: {str(e)}")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
