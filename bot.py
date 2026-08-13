import os
import logging
import base64
from io import BytesIO

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Get secret keys from Render environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Welcome to the AI Image Generator Bot!\n\n"
        "Send me an image description and I will generate it.\n\n"
        "Example:\n"
        "A futuristic city at night, cinematic lighting"
    )


async def generate_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    prompt = update.message.text

    await update.message.reply_text(
        "🎨 Generating your image...\nPlease wait..."
    )

    try:
        response = await client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
        )

        # GPT Image returns the image as base64 data
        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        image = BytesIO(image_bytes)
        image.name = "generated_image.png"

        await update.message.reply_photo(
            photo=image,
            caption=f"🎨 Generated from:\n{prompt}"
        )

    except Exception as e:
        logging.error(f"Image generation error: {e}")

        await update.message.reply_text(
            "❌ Sorry, I couldn't generate the image.\n\n"
            "Please try again with another prompt."
        )


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

    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
