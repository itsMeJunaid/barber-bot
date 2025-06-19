# =========================
# File: reminder.py
# Purpose: Schedule future reminders using TeleBot
# =========================

from apscheduler.schedulers.background import BackgroundScheduler
from config import TELEGRAM_BOT_TOKEN
import telebot
import os
import logging
from datetime import datetime

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Bot Initialization ===
API_TOKEN = TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("🚨 TELEGRAM_BOT_TOKEN is not set in config.py or environment variables.")

bot = telebot.TeleBot(API_TOKEN)

# === Scheduler Setup ===
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder(user_id, message, run_date):
    """
    Schedule a reminder message to be sent to a Telegram user at a specific time.
    
    :param user_id: Telegram user chat ID
    :param message: Message to be sent
    :param run_date: Datetime object (when to send)
    """
    try:
        scheduler.add_job(
            lambda: send_safe_message(user_id, message),
            trigger='date',
            run_date=run_date
        )
        logger.info(f"⏰ Reminder scheduled for user {user_id} at {run_date} - Message: {message}")
    except Exception as e:
        logger.error(f"❌ Failed to schedule reminder: {e}")

def send_safe_message(user_id, message):
    """
    Send message to user with error handling
    """
    try:
        bot.send_message(chat_id=user_id, text=message)
        logger.info(f"✅ Reminder sent to {user_id} at {datetime.now()}")
    except Exception as e:
        logger.error(f"❌ Error sending message to {user_id}: {e}")
