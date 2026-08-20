import os
import time
import base64
import requests
import threading
from flask import Flask, request

app = Flask(__name__)

TOKEN = "8921655911:AAGTj-kaxp0DMGcvv83d3EjCSSSoHkv-Q6I"
GEMINI_API_KEY = "AQ.Ab8RN6IjLdwEbO9sE00WJxZt9Awuk7gqeMNuzkfHFY833YqDSw"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

chat_histories = {}
user_personas = {}
user_last_message_time = {}

BASE_SYSTEM_INSTRUCTION = "Всегда общайся на русском языке, если пользователь явно не попросит общаться на другом языке."

PERSONAS = {
    "🧠 Психолог": "Ты профессиональный, эмпатичный и поддерживающий психолог. Общайся мягко, выслушивай пользователя и задавай наводящие вопросы.",
    "🩺 Доктор": "Ты квалифицированный врач. Отвечай профессионально и заботливо, напоминая об очной консультации при симптомах.",
    "📚 Учитель": "Ты мудрый и терпеливый учитель. Объясняй сложные темы простым языком."
}

class TypingIndicator:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                requests.post(f"{TELEGRAM_API_URL}/sendChatAction", json={"chat_id": self.chat_id, "action": "typing"}, timeout=5)
            except:
                pass
            self.stop_event.wait(4)

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=2)

def send_main_menu(chat_id, text):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": text,
            "reply_markup": {
                "keyboard": [
                    [{"text": "👤 Выбрать персонажа"}, {"text": "🗑 Сбросить историю"}]
                ],
                "resize_keyboard": True,
                "is_persistent": True
            }
        }
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def send_persona_menu(chat_id, text):
    try:
        current_persona = user_personas.get(chat_id)
        p_text = "✅ 🧠 Психолог" if current_persona == "🧠 Психолог" else "🧠 Психолог"
        d_text = "✅ 🩺 Доктор" if current_persona == "🩺 Доктор" else "🩺 Доктор"
        t_text = "✅ 📚 Учитель" if current_persona == "📚 Учитель" else "📚 Учитель"
        n_text = "✅ 👤 Обычный режим" if current_persona is None else "👤 Обычный режим"

        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": text,
            "reply_markup": {
                "keyboard": [
                    [{"text": p_text}, {"text": d_text}],
                    [{"text": t_text}, {"text": n_text}]
                ],
                "resize_keyboard": True,
                "is_persistent": True
            }
        }
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def get_image_base64(file_id):
    try:
        file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
        res = requests.get(file_info_url, timeout=5).json()
        if res.get("ok"):
            file_path = res["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            img_data = requests.get(file_url, timeout=10).content
            return base64.b64encode(img_data).decode("utf-8")
    except:
        pass
    return None

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = request.get_json(silent=True)
        if not update or "message" not in update:
            return "OK", 200
            
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return "OK", 200
            
        text = message.get("text", "")

        if text == "/start":
            chat_histories[chat_id] = []
            user_personas[chat_id] = None
            send_main_menu(chat_id, "Привет! Бот на связи и работает идеально 🚀")
            return "OK", 200

        if text == "🗑 Сбросить историю":
            chat_histories[chat_id] = []
            send_main_menu(chat_id, "🔄 История очищена.")
            return "OK", 200
            
        if text == "👤 Выбрать персонажа":
            send_persona_menu(chat_id, "Выберите персонажа:")
            return "OK", 200
            
        cleaned_text = text.replace("✅ ", "")
        if cleaned_text in PERSONAS:
            user_personas[chat_id] = cleaned_text
            chat_histories[chat_id] = []
            send_main_menu(chat_id, f"✅ Выбран персонаж: {cleaned_text}")
            return "OK", 200
            
        if cleaned_text == "👤 Обычный режим":
            user_personas[chat_id] = None
            chat_histories[chat_id] = []
            send_main_menu(chat_id, "🔄 Обычный режим.")
            return "OK", 200

        now = time.time()
        last_time = user_last_message_time.get(chat_id, 0)
        elapsed = now - last_time
        
        if elapsed < 3.0:
            remaining = round(3.0 - elapsed, 1)
            send_main_menu(chat_id, f"⏳ Погодите, еще {remaining} сек.")
            return "OK", 200
            
        user_last_message_time[chat_id] = now

        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
            
        current_parts = []
        b64_img = None
        
        if "photo" in message:
            file_id = message["photo"][-1]["file_id"]
            caption = message.get("caption", "")
            b64_img = get_image_base64(file_id)
            current_parts.append({"text": caption if caption else "Опиши эту картинку"})
        elif text:
            current_parts.append({"text": text})
        else:
            send_main_menu(chat_id, "Отправьте текст или картинку.")
            return "OK", 200

        if b64_img:
            current_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})

        chat_histories[chat_id].append({"role": "user", "parts": current_parts})
        if len(chat_histories[chat_id]) > 10:
            chat_histories[chat_id] = chat_histories[chat_id][-10:]

        instruction_text = BASE_SYSTEM_INSTRUCTION
        persona = user_personas.get(chat_id)
        if persona and persona in PERSONAS:
            instruction_text += " " + PERSONAS[persona]

        payload = {
            "contents": chat_histories[chat_id],
            "system_instruction": {"parts": [{"text": instruction_text}]}
        }
        
        typing_ind = TypingIndicator(chat_id)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GEMINI_API_KEY}"
            }
            response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=25)
            res_json = response.json()
            
            if "candidates" in res_json and len(res_json["candidates"]) > 0:
                ai_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                chat_histories[chat_id].append({"role": "model", "parts": [{"text": ai_text}]})
                
                typing_ind.stop()
                send_main_menu(chat_id, ai_text)
            elif "error" in res_json:
                typing_ind.stop()
                if len(chat_histories[chat_id]) > 0:
                    chat_histories[chat_id].pop()
                err_msg = res_json['error'].get('message', '')
                send_main_menu(chat_id, f"⚠️ API Error: {err_msg}")
            else:
                typing_ind.stop()
                if len(chat_histories[chat_id]) > 0:
                    chat_histories[chat_id].pop()
                send_main_menu(chat_id, "⚠️ Ошибка ответа ИИ.")
        except Exception as inner_e:
            typing_ind.stop()
            if len(chat_histories[chat_id]) > 0:
                chat_histories[chat_id].pop()
            send_main_menu(chat_id, "⚠️ Ошибка соединения с ИИ.")

    except Exception as e:
        pass

    return "OK", 200

@app.route('/')
def index():
    render_url = request.host_url.rstrip('/')
    webhook_url = f"{render_url}/{TOKEN}"
    requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    return "Bot is running on Render perfectly!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
