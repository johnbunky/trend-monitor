import os, httpx
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LENGTH = 4000

async def send_message(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = TELEGRAM_API.format(token=token)
    chunks = _split(text)
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown", "disable_web_page_preview": True}
            r = await client.post(url, json=payload)
            if r.status_code != 200:
                payload["parse_mode"] = ""
                await client.post(url, json=payload)

def _split(text):
    if len(text) <= MAX_LENGTH:
        return [text]
    chunks = []
    while text:
        if len(text) <= MAX_LENGTH:
            chunks.append(text); break
        split_at = text.rfind("\n", 0, MAX_LENGTH)
        if split_at == -1: split_at = MAX_LENGTH
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
