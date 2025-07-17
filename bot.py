from telegram.ext import ApplicationBuilder

app = ApplicationBuilder().token("...").build()
app.run_polling()  # или run_webhook
