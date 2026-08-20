@app.route('/')
def index():
    webhook_url = f"https://твое-имя-на-рендере.onrender.com/{TOKEN}" # потом заменим на реальный URL
    requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    return "Bot is running on Render!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
