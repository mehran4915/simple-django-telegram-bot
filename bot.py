import os
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from bot.models import UserData
from asgiref.sync import sync_to_async

load_dotenv()
TOKEN = os.getenv("TOKEN")

# States for ConversationHandler
ASK_USERNAME, ASK_FIRSTNAME, ASK_LASTNAME = range(3)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        user = await sync_to_async(UserData.objects.get)(id=user_id)
        await update.message.reply_text(f"Welcome back, {user.first_name}!")
    except UserData.DoesNotExist:
        await update.message.reply_text("You are not registered. What's your username?")
        return ASK_USERNAME

# Ask for username
async def ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("What's your first name?")
    return ASK_FIRSTNAME

# Ask for first name
async def ask_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("What's your last name?")
    return ASK_LASTNAME

# Final step: save user
async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    user_id = update.effective_user.id

    # Save to DB
    user = UserData(
        id=user_id,
        username=context.user_data["username"],
        first_name=context.user_data["first_name"],
        last_name=context.user_data["last_name"]
    )
    await sync_to_async(user.save)()
    await update.message.reply_text(f"Thank you {user.first_name}, you are now registered!")
    return ConversationHandler.END

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END

# Main app setup
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_username)],
            ASK_FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_firstname)],
            ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
