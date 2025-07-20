import logging
import time
from telegram import Bot, Update
from telegram.ext import CommandHandler, Application, CallbackContext
from telegram.error import TelegramError

from open_webui.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENABLED,
)
from open_webui.models.users import Users

log = logging.getLogger(__name__)

app = None
bot = None

if TELEGRAM_ENABLED and TELEGRAM_BOT_TOKEN:
    app = Application.builder().token(str(TELEGRAM_BOT_TOKEN)).build()
    bot = app.bot


async def start(update: Update, context: CallbackContext):
    log.info(f"Received /start command from chat_id: {update.message.chat_id}")
    
    try:
        if update.message.text and len(update.message.text.split()) > 1:
            token = update.message.text.split()[1]
            log.info(f"Attempting to link user with token: {token}")

            user = Users.get_user_by_telegram_onboarding_token(token)

            if user:
                log.info(f"Found user {user.id} for token.")
                if user.telegram_onboarding_token_expires_at > int(time.time()):
                    log.info("Token is valid. Updating user's telegram_chat_id.")
                    Users.update_user_by_id(
                        user.id,
                        {
                            "telegram_chat_id": str(update.message.chat_id),
                            "telegram_onboarding_token": None,
                            "telegram_onboarding_token_expires_at": None,
                        },
                    )
                    await update.message.reply_text(
                        "Your Telegram account has been successfully linked to your Open WebUI account."
                    )
                    log.info(f"Successfully linked chat_id {update.message.chat_id} to user {user.id}")
                else:
                    log.warning(f"Onboarding token has expired for user {user.id}.")
                    await update.message.reply_text("The onboarding token has expired.")
            else:
                log.warning(f"No user found for token: {token}")
                await update.message.reply_text("Invalid onboarding token.")
        else:
            log.info("Received /start command without a token.")
            await update.message.reply_text(
                "Welcome to the Open WebUI bot! Please use the link provided in your user profile to connect your account."
            )
    except Exception as e:
        log.error(f"Error in /start command handler: {e}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again later.")


async def send_telegram_message(chat_id: str, message: str):
    if not bot:
        log.debug("Telegram bot is not enabled or configured.")
        return

    try:
        await bot.send_message(chat_id=chat_id, text=message)
        log.info(f"Telegram message sent to {chat_id}")
    except TelegramError as e:
        log.error(f"Failed to send Telegram message to {chat_id}: {e}")


async def notify_admins(message: str):
    if not bot:
        log.debug("Telegram bot is not enabled or configured.")
        return

    try:
        admins = Users.get_admin_users()
        if not admins:
            log.warning("Could not find any admin users to notify.")
            return

        notified_admins = []
        for admin in admins:
            if admin.telegram_chat_id:
                await send_telegram_message(admin.telegram_chat_id, message)
                notified_admins.append(admin.email)
            else:
                log.warning(f"Admin user {admin.email} does not have a Telegram chat ID configured.")
        
        if notified_admins:
            log.info(f"Notified admins: {', '.join(notified_admins)}")
        else:
            log.warning("No admin users with a configured Telegram chat ID were found.")

    except Exception as e:
        log.error(f"An error occurred while notifying admins: {e}", exc_info=True)



if app:
    app.add_handler(CommandHandler("start", start))
