import os
from dotenv import load_dotenv

from bot.telegram_bot import StudentAnalyticsBot
from llm.groq_client import GroqClient


def main() -> None:
    load_dotenv()

    api_key = os.getenv("API_KEY", "").strip()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_raw = os.getenv("ADMIN_ID", "").strip()

    if not api_key:
        raise RuntimeError("Set API_KEY in .env file")
    if not bot_token:
        raise RuntimeError("Set BOT_TOKEN in .env file")
    if not admin_id_raw:
        raise RuntimeError("Set ADMIN_ID in .env file")

    admin_id = int(admin_id_raw)
    llm = GroqClient(api_key=api_key)
    bot = StudentAnalyticsBot(token=bot_token, llm=llm, admin_id=admin_id)
    bot.run()


if __name__ == "__main__":
    main()
