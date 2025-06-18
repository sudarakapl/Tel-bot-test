import time
from telegram.error import NetworkError
from bot import create_bot

if __name__ == "__main__":
    while True:
        try:
            bot = create_bot()
            print("✅ Task bot is starting…")
            # This will block until you Ctrl‑C or an unrecoverable error occurs
            bot.run_polling()
            # If run_polling ever returns normally, break out of the loop
            break
        except NetworkError as e:
            print("🌐 NetworkError (Bad Gateway) encountered: %s", e)
            print("⏳ Sleeping 5s before restarting polling…")
            time.sleep(5)
        except Exception:
            print("💥 Unhandled exception, exiting")
            break
