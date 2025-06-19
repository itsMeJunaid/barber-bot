# =========================
# File: config.py
# Purpose: Configuration settings for Elite Barber Shop Bot
# =========================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === Telegram Bot Configuration ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# === Gemini AI Configuration ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_MODEL = "gemini-1.5-flash"

# === Database Configuration ===
BOOKING_DB_PATH = "bookings.json"
USER_DB_PATH = "users.json"

# === Google Sheets Configuration ===
# Put your Google Sheets credentials file in the project folder
GOOGLE_SHEETS_CREDENTIALS = "credentials.json"  # Path to your Google credentials JSON file
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "YOUR_SPREADSHEET_ID_HERE")

# === Business Configuration ===
BUSINESS_NAME = "Elite Barber Shop"
BUSINESS_HOURS = {
    "monday": {"open": "09:00", "close": "18:00"},
    "tuesday": {"open": "09:00", "close": "18:00"},
    "wednesday": {"open": "09:00", "close": "18:00"},
    "thursday": {"open": "09:00", "close": "18:00"},
    "friday": {"open": "09:00", "close": "18:00"},
    "saturday": {"open": "09:00", "close": "17:00"},
    "sunday": {"closed": True}
}

# === Service Configuration ===
SERVICES = {
    "Classic Haircut": {"price": 25, "duration": 30},
    "Fade Cut": {"price": 30, "duration": 45},
    "Beard Trim": {"price": 15, "duration": 20},
    "Mustache Trim": {"price": 10, "duration": 15},
    "Hot Towel Shave": {"price": 35, "duration": 40},
    "Hair Wash & Style": {"price": 40, "duration": 45},
    "Eyebrow Trim": {"price": 12, "duration": 15},
    "Hair Treatment": {"price": 50, "duration": 60},
    "Full Service Package": {"price": 65, "duration": 90}
}

# === Time Slot Configuration ===
TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM",
    "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
    "05:00 PM", "05:30 PM"
]

# === Reminder Configuration ===
REMINDER_ADVANCE_HOURS = 1  # Send reminder 1 hour before appointment
REMINDER_ENABLED = True

# === Webhook Configuration ===
# Use environment variables for webhook configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8080))

# === Admin Configuration ===
ADMIN_USER_IDS = [
    # Add admin Telegram user IDs here
    # 123456789,  # Replace with actual admin user ID
]

# === Logging Configuration ===
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# === Rate Limiting ===
MAX_BOOKINGS_PER_USER_PER_DAY = 3
MAX_MESSAGES_PER_MINUTE = 20

# === Validation Rules ===
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50
ADVANCE_BOOKING_DAYS = 30  # How many days in advance can users book

# === Backup Configuration ===
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 30

# === Messages Configuration ===
WELCOME_MESSAGE = """
👋 Welcome to Elite Barber Shop AI!

🔹 Available Commands:
• Type "book" - Book an appointment
• Type "cancel" - Cancel your appointment  
• Type "view" - View available slots
• Type "my bookings" - See your appointments
• Ask any questions about our services!

How can I help you today?
"""

ERROR_MESSAGES = {
    "booking_failed": "❌ Booking failed. Please try again or contact support.",
    "invalid_time": "❌ Invalid time format. Please use format like '2:30 PM'",
    "invalid_date": "❌ Invalid date format. Please use DD-MM-YYYY or type 'today'/'tomorrow'",
    "slot_taken": "❌ That time slot is already taken. Please choose another time.",
    "past_date": "❌ Cannot book appointments in the past.",
    "no_slots": "❌ No available slots for this date.",
    "rate_limit": "❌ Too many requests. Please wait a moment.",
    "system_error": "❌ System error occurred. Please try again later."
}

SUCCESS_MESSAGES = {
    "booking_confirmed": "✅ Your appointment has been confirmed!",
    "booking_cancelled": "✅ Your appointment has been cancelled.",
    "reminder_set": "🔔 Reminder set for 1 hour before your appointment."
}

# === Environment Validation ===
def validate_config():
    """Validate that all required configuration is present"""
    required_vars = [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("GEMINI_API_KEY", GEMINI_API_KEY),
    ]
    
    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value or var_value.startswith("YOUR_"):
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
    
    return True

# === Simple Configuration Instructions ===
SETUP_INSTRUCTIONS = """
To set up your bot:

1. Create a .env file with your API keys:
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   GEMINI_API_KEY=your_gemini_key_here
   SPREADSHEET_ID=your_spreadsheet_id_here
   WEBHOOK_URL=your_webhook_url_here

2. For Google Sheets (optional):
   - Follow the Google Sheets setup guide
   - Place credentials.json in project folder

3. Install dependencies: pip install -r requirements.txt

4. Run: python main.py
"""