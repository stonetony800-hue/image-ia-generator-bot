import os
import logging
from io import BytesIO

import requests
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURATION
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
IMAGE_API_URL = os.getenv("IMAGE_API_URL")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Flask app for Render
app = Flask(__name__)


@app.route("/")
def home():
    return "AI Image Generator Bot is running!"


# =========================
# TELEGRAM COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Welcome to the AI Image Generator Bot!\n\n"
        "Send me an image description and I will generate it for you.\n\n"
        "Example:\n"
        "A futuristic city at night, cinematic lighting"
    )


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text

    await update.message.reply_text(
        "🎨 Generating your image...\nPlease wait."
    )

    try:
        # Request image from your image generation API
        response = requests.post(
            IMAGE_API_URL,
            json={
                "prompt": prompt
            },
            timeout=120
        )

        response.raise_for_status()

        # If API returns the actual image
        image = BytesIO(response.content)

        await update.message.reply_photo(
            photo=image,
            caption=f"🎨 Generated from:\n{prompt}"
        )

    except Exception as e:
        logging.error(f"Image generation error: {e}")

        await update.message.reply_text(
            "❌ Sorry, I couldn't generate the image.\n"
            "Please try again."
        )


# =========================
# START BOT
# =========================

def main():
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            generate_image
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
