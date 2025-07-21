import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from open_webui.models.users import Users
from open_webui.models.billing import UserCredits
from open_webui.telegram_bot import send_telegram_message

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_subscription_reminders():
    log.info("Running subscription reminder check...")
    now = datetime.now()
    three_days_from_now = now + timedelta(days=3)
    one_day_from_now = now + timedelta(days=1)

    # Get all users with credits
    users_with_credits = UserCredits.get_all_user_credits()

    for user_credits in users_with_credits:
        if user_credits.current_period_end:
            # Convert timestamp to datetime
            period_end_date = datetime.fromtimestamp(user_credits.current_period_end)

            user = Users.get_user_by_id(user_credits.user_id)
            if not user or not user.telegram_chat_id:
                continue

            days_left = (period_end_date - now).days

            if days_left == 3 or days_left == 1:
                try:
                    message = f"Your subscription is expiring in {days_left} day(s). Please renew to continue enjoying our services."
                    await send_telegram_message(user.telegram_chat_id, message)
                    log.info(f"Sent subscription reminder to user {user.id} ({user.email})")
                except Exception as e:
                    log.error(f"Failed to send subscription reminder to user {user.id}: {e}")


def schedule_tasks():
    # Schedule the subscription reminder to run once a day
    scheduler.add_job(check_subscription_reminders, 'interval', days=1)
    scheduler.start()
    log.info("Scheduled tasks started.")
