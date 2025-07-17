import logging, os, re
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from docx import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
ESCAPE_CHARS = r'.\"!?)(\[\]%:;\-'

def escape_punct(text: str) -> str:
    return re.sub(f'([{re.escape(ESCAPE_CHARS)}])', r'\\\1', text)

def format_run(run):
    txt = run.text
    if not txt.strip():
        return escape_punct(txt)
    leading = txt[:len(txt) - len(txt.lstrip())]
    trailing = txt[len(txt.rstrip()):]
    core = txt.strip()
    core = escape_punct(core)
    try:
        strike = run.font.strike
    except:
        strike = False

    if run.underline and run.italic:
        core = f"__{core}__"
    else:
        if run.bold:
            core = f"*{core}*"
        if run.italic:
            core = f"_{core}_"
        if run.underline:
            core = f"__{core}__"
        if strike:
            core = f"~{core}~"

    return f"{leading}{core}{trailing}"

def process_document(doc_bytes):
    doc = Document(doc_bytes)
    lines = []
    for p in doc.paragraphs:
        lines.append(''.join(format_run(r) for r in p.runs))
    return "\n".join(lines)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Присылай .docx — я верну Markdown!")

async def handle_docx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc_file = update.message.document
    if not doc_file.file_name.endswith('.docx'):
        return await update.message.reply_text("Только .docx, пожалуйста.")
    f = await doc_file.get_file()
    data = await f.download_as_bytearray()
    md = process_document(BytesIO(data))
    out = BytesIO(md.encode('utf-8'))
    out.name = 'formatted.txt'
    await update.message.reply_document(InputFile(out), caption="Готово ✅")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    APP_URL = os.getenv("APP_URL")
    if not TOKEN or not APP_URL:
        raise RuntimeError("Нужны BOT_TOKEN и APP_URL в env vars")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.FileExtension("docx"), handle_docx))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_path="/webhook",
        webhook_url=f"{APP_URL}/webhook"
    )

if __name__ == "__main__":
    main()
