import os
import logging
import re
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from docx import Document

logging.basicConfig(level=logging.INFO)

ESCAPE_CHARS = r'."!?)([]%:;\-'
def escape_punct(text: str) -> str:
    return re.sub(f'([{re.escape(ESCAPE_CHARS)}])', r'\\\1', text)

def format_run(run):
    original_text = run.text
    if not original_text.strip():
        return escape_punct(original_text)
    lead = original_text[:len(original_text)-len(original_text.lstrip())]
    trail = original_text[len(original_text.rstrip()):]
    core = original_text.strip()
    core = escape_punct(core)
    try:
        strike = bool(run.font.strike)
    except:
        strike = False
    if run.underline and run.italic:
        styled = f"__{core}__"
    else:
        styled = core
        if run.bold: styled = f"*{styled}*"
        if run.italic: styled = f"_{styled}_"
        if run.underline: styled = f"__{styled}__"
        if strike: styled = f"~{styled}~"
    return lead + styled + trail

def process_document(docx_bytes):
    doc = Document(docx_bytes)
    return "\n".join(
        "".join(format_run(r) for r in para.runs)
        for para in doc.paragraphs
    )

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Присылай .docx — верну в Markdown ✨")

async def handle_docx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.docx'):
        await update.message.reply_text("Нужен файл .docx")
        return
    file = await doc.get_file()
    data = await file.download_as_bytearray()
    result = process_document(BytesIO(data))
    out = BytesIO(result.encode('utf-8'))
    out.seek(0)
    await update.message.reply_document(
        document=InputFile(out, filename='formatted.txt'),
        caption="✔ Вот твой Markdown"
    )

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.FileExtension("docx"), handle_docx))
    app.run_polling()  # Можно поменять на run_webhook(...) при необходимости

if __name__ == "__main__":
    main()
