import os
import json
import base64
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

from openai import OpenAI


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)


def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"

    encoded = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def send_message(chat_id, text):
    telegram_request(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


def send_photo(chat_id, image_bytes):
    boundary = "----TelegramBoundary"

    parts = []

    parts.append(
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{chat_id}\r\n"
    )

    parts.append(
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="caption"\r\n\r\n'
        "✨ Your AI-generated image\r\n"
    )

    header = "".join(parts).encode("utf-8")

    file_header = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="photo"; filename="image.png"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8")

    ending = f"\r\n--{boundary}--\r\n".encode("utf-8")

    body = header + file_header + image_bytes + ending

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def create_image(prompt):
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
    )

    image_base64 = result.data[0].b64_json

    if not image_base64:
        raise Exception("OpenAI did not return image data.")

    return base64.b64decode(image_base64)


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        self.wfile.write(
            b"AI Image Generator Telegram Bot is running!"
        )

    def do_POST(self):

        try:
            length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(length)

            update = json.loads(
                body.decode("utf-8")
            )

            message = update.get("message")

            if not message:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            chat_id = message["chat"]["id"]

            text = message.get("text", "").strip()

            if not text:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            if text == "/start":

                send_message(
                    chat_id,
                    "👋 Welcome to the AI Image Generator!\n\n"
                    "Send me a description of the image you want.\n\n"
                    "Example:\n"
                    "A futuristic city at night, cinematic lighting"
                )

            else:

                send_message(
                    chat_id,
                    "🎨 Creating your image... Please wait."
                )

                try:

                    image = create_image(text)

                    send_photo(
                        chat_id,
                        image
                    )

                except Exception as error:

                    print("IMAGE ERROR:", repr(error))

                    send_message(
                        chat_id,
                        "❌ Image generation failed.\n\n"
                        f"Error: {str(error)[:800]}"
                    )

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as error:

            print("WEBHOOK ERROR:", repr(error))

            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error")
