import os
from datetime import datetime, timedelta
from flask import Flask, request
import telebot
from telebot import types

from gpt_module import ask_gpt
from booking import (
    add_booking, 
    check_availability, 
    get_available_slots, 
    get_bookings_for_date,
    cancel_booking,
    update_booking,
    get_user_bookings
)
from reminder import schedule_reminder
from config import TELEGRAM_BOT_TOKEN, SERVICES

# Ensure the token is loaded
API_TOKEN = TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN")

if not API_TOKEN:
    raise ValueError("🚨 TELEGRAM_BOT_TOKEN is not set in config.py or environment variables.")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Store user states for multi-step conversations
user_states = {}

@app.route(f"/{API_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# @app.route("/webhook", methods=['POST'])
# def webhook():
#     json_str = request.get_data().decode("UTF-8")
#     update = telebot.types.Update.de_json(json_str)
#     bot.process_new_updates([update])
#     return "!", 200

@app.route('/')
def index():
    return "Elite Barber Shop Bot is Running! ✂️", 200

# === Helper Functions ===

def create_main_menu():
    """Create the main menu keyboard"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Create buttons
    btn_book = types.KeyboardButton("📅 Book Appointment")
    btn_view = types.KeyboardButton("👀 View Available Slots")
    btn_my_bookings = types.KeyboardButton("📋 My Bookings")
    btn_services = types.KeyboardButton("✂️ Services & Pricing")
    btn_cancel = types.KeyboardButton("❌ Cancel Booking")
    btn_help = types.KeyboardButton("❓ Help")
    
    markup.add(btn_book, btn_view)
    markup.add(btn_my_bookings, btn_services)
    markup.add(btn_cancel, btn_help)
    
    return markup

def create_services_keyboard():
    """Create services selection keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for service, details in SERVICES.items():
        btn = types.InlineKeyboardButton(
            f"{service} - ${details['price']}", 
            callback_data=f"service_{service}"
        )
        markup.add(btn)
    
    return markup

def create_time_keyboard(available_slots):
    """Create time selection keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    for slot in available_slots:
        btn = types.InlineKeyboardButton(slot, callback_data=f"time_{slot}")
        markup.add(btn)
    
    return markup

def create_date_keyboard():
    """Create date selection keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Today and Tomorrow buttons
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    btn_today = types.InlineKeyboardButton(
        f"Today ({today.strftime('%d %b')})", 
        callback_data="date_today"
    )
    btn_tomorrow = types.InlineKeyboardButton(
        f"Tomorrow ({tomorrow.strftime('%d %b')})", 
        callback_data="date_tomorrow"
    )
    
    markup.add(btn_today, btn_tomorrow)
    
    # Next few days
    for i in range(2, 7):
        future_date = today + timedelta(days=i)
        if future_date.weekday() != 6:  # Skip Sundays
            btn = types.InlineKeyboardButton(
                future_date.strftime('%d %b (%a)'),
                callback_data=f"date_{future_date.strftime('%Y-%m-%d')}"
            )
            markup.add(btn)
    
    return markup

# === Bot Command Handlers ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = """
👋 Welcome to Elite Barber Shop AI!

🔹 I'm here to help you:
• Book appointments easily
• Check available time slots
• View our services and pricing
• Answer your grooming questions

Use the menu buttons below or type your questions!
    """
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_msg = """
🆘 Elite Barber Shop Bot Help

📋 Available Commands:
• 📅 Book Appointment - Start booking process
• 👀 View Available Slots - See open time slots
• 📋 My Bookings - View your appointments
• ✂️ Services & Pricing - Our service menu
• ❌ Cancel Booking - Cancel your appointment
• ❓ Help - Show this help

💡 You can also ask me questions about:
- Hair cutting styles and trends
- Grooming tips and advice
- Product recommendations
- Our services and pricing

🕒 Business Hours:
Monday-Friday: 9:00 AM - 6:00 PM
Saturday: 9:00 AM - 5:00 PM
Sunday: Closed
    """
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, help_msg, reply_markup=markup)

# === Message Handlers ===

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Handle menu button clicks
    if text == "📅 Book Appointment":
        start_booking_process(message)
    
    elif text == "👀 View Available Slots":
        show_available_slots(message)
    
    elif text == "📋 My Bookings":
        show_user_bookings(message)
    
    elif text == "✂️ Services & Pricing":
        show_services_menu(message)
    
    elif text == "❌ Cancel Booking":
        start_cancel_process(message)
    
    elif text == "❓ Help":
        send_help(message)
    
    # Handle booking process steps
    elif chat_id in user_states:
        handle_booking_steps(message)
    
    # Handle general queries with AI
    else:
        reply = ask_gpt(text)
        bot.send_message(chat_id, reply)

# === Callback Query Handler ===

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data

    try:
        # Handle date selection
        if data.startswith("date_"):
            handle_date_callback(call)
        
        # Handle time selection
        elif data.startswith("time_"):
            handle_time_callback(call)
        
        # Handle service selection
        elif data.startswith("service_"):
            handle_service_callback(call)
        
        # Handle booking confirmation
        elif data == "confirm_booking":
            confirm_booking(call)
        
        elif data == "cancel_booking_process":
            cancel_booking_process(call)

        # Answer callback to remove loading state
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error handling callback: {e}")
        bot.answer_callback_query(call.id, "Sorry, something went wrong!")

# === Booking Process Functions ===

def start_booking_process(message):
    """Start the booking process"""
    chat_id = message.chat.id
    user_states[chat_id] = {"step": "get_name", "booking_data": {}}
    
    # Create a cancel keyboard
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Back to Main Menu"))
    
    bot.send_message(
        chat_id, 
        "🔸 Let's book your appointment!\n\n👤 What's your full name?",
        reply_markup=markup
    )

def handle_booking_steps(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if not state:
        return
    
    # Check if user wants to go back
    if message.text == "🔙 Back to Main Menu":
        cancel_booking_process_by_message(message)
        return
    
    if state["step"] == "get_name":
        handle_name_input(message, state)

def handle_name_input(message, state):
    name = message.text.strip()
    
    # Validate name
    if len(name) < 2 or len(name) > 50:
        bot.send_message(
            message.chat.id, 
            "❌ Please enter a valid name (2-50 characters)\n\n👤 What's your full name?"
        )
        return
    
    # Store name and move to date selection
    state["booking_data"]["name"] = name
    state["booking_data"]["user_id"] = message.from_user.id
    state["step"] = "get_date"
    
    # Show date selection
    markup = create_date_keyboard()
    bot.send_message(
        message.chat.id,
        f"Great, {name}! 📅\n\nWhat date would you like to book?",
        reply_markup=markup
    )

def handle_date_callback(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    
    if not state or state["step"] != "get_date":
        return
    
    date_data = call.data.replace("date_", "")
    
    # Parse date
    if date_data == "today":
        appointment_date = datetime.now()
    elif date_data == "tomorrow":
        appointment_date = datetime.now() + timedelta(days=1)
    else:
        try:
            appointment_date = datetime.strptime(date_data, "%Y-%m-%d")
        except ValueError:
            bot.send_message(chat_id, "❌ Invalid date format. Please try again.")
            return
    
    # Check if it's Sunday (closed)
    if appointment_date.weekday() == 6:
        bot.send_message(chat_id, "❌ We're closed on Sundays. Please choose another date.")
        return
    
    # Store date and get available slots
    date_str = appointment_date.strftime("%Y-%m-%d")
    state["booking_data"]["date"] = date_str
    state["step"] = "get_time"
    
    available_slots = get_available_slots(date_str)
    
    if available_slots:
        markup = create_time_keyboard(available_slots)
        bot.edit_message_text(
            f"🕐 Available times for {appointment_date.strftime('%A, %d %B %Y')}:\n\nPlease select a time:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    else:
        bot.edit_message_text(
            f"❌ No available slots for {appointment_date.strftime('%A, %d %B %Y')}.\n\nPlease choose another date.",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=create_date_keyboard()
        )
        state["step"] = "get_date"

def handle_time_callback(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    
    if not state or state["step"] != "get_time":
        return
    
    selected_time = call.data.replace("time_", "")
    selected_date = state["booking_data"]["date"]
    
    # Double-check availability
    if not check_availability(selected_date, selected_time):
        bot.answer_callback_query(call.id, "❌ That time slot is no longer available!")
        
        # Refresh available slots
        available_slots = get_available_slots(selected_date)
        if available_slots:
            markup = create_time_keyboard(available_slots)
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        return
    
    # Store time and move to service selection
    state["booking_data"]["time"] = selected_time
    state["step"] = "get_service"
    
    markup = create_services_keyboard()
    bot.edit_message_text(
        "✂️ What service would you like?\n\nPlease select from our menu:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

def handle_service_callback(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    
    if not state or state["step"] != "get_service":
        return
    
    selected_service = call.data.replace("service_", "")
    state["booking_data"]["service"] = selected_service
    
    # Show booking confirmation
    booking_data = state["booking_data"]
    appointment_date = datetime.strptime(booking_data["date"], "%Y-%m-%d")
    service_price = SERVICES.get(selected_service, {}).get("price", "N/A")
    
    confirmation_text = f"""
📋 BOOKING CONFIRMATION

👤 Name: {booking_data['name']}
📅 Date: {appointment_date.strftime('%A, %d %B %Y')}
🕐 Time: {booking_data['time']}
✂️ Service: {selected_service}
💰 Price: ${service_price}

Please confirm your booking:
    """
    
    # Create confirmation keyboard
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Confirm Booking", callback_data="confirm_booking"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking_process")
    )
    
    bot.edit_message_text(
        confirmation_text,
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

def confirm_booking(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    
    if not state:
        return
    
    booking_data = state["booking_data"]
    
    # Create full datetime string for booking system
    full_datetime = f"{booking_data['date']} {booking_data['time']}"
    
    try:
        # Add booking to system
        success = add_booking(
            booking_data["name"],
            full_datetime,
            booking_data["service"],
            booking_data["user_id"]
        )
        
        if success:
            # Send success message
            appointment_date = datetime.strptime(booking_data["date"], "%Y-%m-%d")
            confirmation_msg = f"""
✅ BOOKING CONFIRMED!

👤 Name: {booking_data['name']}
📅 Date: {appointment_date.strftime('%A, %d %B %Y')}
🕐 Time: {booking_data['time']}
✂️ Service: {booking_data['service']}

📧 Booking ID: {booking_data.get('id', 'Generated')}

We'll send you a reminder 1 hour before your appointment!

Thank you for choosing Elite Barber Shop! 💈
            """
            
            # Schedule reminder
            try:
                appointment_datetime = datetime.strptime(full_datetime, "%Y-%m-%d %I:%M %p")
                reminder_time = appointment_datetime - timedelta(hours=1)
                
                if reminder_time > datetime.now():
                    reminder_msg = f"⏰ Reminder: You have a {booking_data['service']} appointment at {booking_data['time']} today at Elite Barber Shop!"
                    schedule_reminder(chat_id, reminder_msg, reminder_time)
            except Exception as e:
                print(f"Failed to schedule reminder: {e}")
            
            # Send confirmation and return to main menu
            markup = create_main_menu()
            bot.edit_message_text(
                confirmation_msg,
                chat_id=chat_id,
                message_id=call.message.message_id
            )
            bot.send_message(chat_id, "How else can I help you today?", reply_markup=markup)
            
        else:
            bot.edit_message_text(
                "❌ Booking failed. The time slot may have been taken by another customer.\n\nPlease try booking again with a different time.",
                chat_id=chat_id,
                message_id=call.message.message_id
            )
            # Return to main menu
            markup = create_main_menu()
            bot.send_message(chat_id, "Please try again:", reply_markup=markup)
    
    except Exception as e:
        print(f"Booking error: {e}")
        bot.edit_message_text(
            "❌ System error occurred while booking. Please try again later or contact support.",
            chat_id=chat_id,
            message_id=call.message.message_id
        )
        markup = create_main_menu()
        bot.send_message(chat_id, "Please try again:", reply_markup=markup)
    
    # Clear user state
    if chat_id in user_states:
        del user_states[chat_id]

def cancel_booking_process(call):
    """Cancel the booking process"""
    chat_id = call.message.chat.id
    
    bot.edit_message_text(
        "❌ Booking cancelled.\n\nHow else can I help you?",
        chat_id=chat_id,
        message_id=call.message.message_id
    )
    
    # Return to main menu
    markup = create_main_menu()
    bot.send_message(chat_id, "Main Menu:", reply_markup=markup)
    
    # Clear user state
    if chat_id in user_states:
        del user_states[chat_id]

def cancel_booking_process_by_message(message):
    """Cancel booking process from message"""
    chat_id = message.chat.id
    
    bot.send_message(
        chat_id,
        "❌ Booking cancelled.\n\nHow else can I help you?",
        reply_markup=create_main_menu()
    )
    
    # Clear user state
    if chat_id in user_states:
        del user_states[chat_id]

# === Other Functions ===

def start_cancel_process(message):
    """Start the cancellation process"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user_bookings = get_user_bookings(user_id)
        
        if not user_bookings:
            bot.send_message(
                chat_id, 
                "📭 You don't have any active bookings to cancel.\n\nWould you like to book an appointment?",
                reply_markup=create_main_menu()
            )
            return
        
        # Create inline keyboard with user's bookings
        markup = types.InlineKeyboardMarkup()
        
        for booking in user_bookings:
            booking_date = datetime.strptime(booking['date'], '%Y-%m-%d')
            button_text = f"{booking['service']} - {booking_date.strftime('%d %b')} at {booking['time']}"
            markup.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"cancel_{booking['id']}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"))
        
        bot.send_message(
            chat_id,
            "📋 Select the booking you want to cancel:",
            reply_markup=markup
        )
        
    except Exception as e:
        print(f"Error in cancel process: {e}")
        bot.send_message(
            chat_id,
            "❌ Error retrieving your bookings. Please try again later.",
            reply_markup=create_main_menu()
        )

def show_available_slots(message):
    """Show available time slots for today"""
    chat_id = message.chat.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        available_slots = get_available_slots(today)
        
        if available_slots:
            slots_msg = f"📅 Available Slots for Today ({datetime.now().strftime('%A, %d %B')}):\n\n"
            for slot in available_slots:
                slots_msg += f"🕐 {slot}\n"
            slots_msg += "\n💡 Click 'Book Appointment' to schedule!"
        else:
            slots_msg = "❌ No available slots for today.\n\n💡 Try booking for tomorrow or another day!"
        
        bot.send_message(chat_id, slots_msg, reply_markup=create_main_menu())
        
    except Exception as e:
        print(f"Error showing slots: {e}")
        bot.send_message(
            chat_id,
            "❌ Error retrieving available slots. Please try again.",
            reply_markup=create_main_menu()
        )

def show_user_bookings(message):
    """Show user's upcoming bookings"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        bookings = get_user_bookings(user_id)
        
        if bookings:
            bookings_msg = "📋 Your Upcoming Appointments:\n\n"
            for booking in bookings:
                appointment_date = datetime.strptime(booking['date'], '%Y-%m-%d')
                bookings_msg += f"✂️ {booking['service']}\n"
                bookings_msg += f"📅 {appointment_date.strftime('%A, %d %B %Y')}\n"
                bookings_msg += f"🕐 {booking['time']}\n"
                bookings_msg += f"📧 ID: {booking['id']}\n\n"
        else:
            bookings_msg = "📭 You don't have any upcoming appointments.\n\n💡 Would you like to book one?"
        
        bot.send_message(chat_id, bookings_msg, reply_markup=create_main_menu())
        
    except Exception as e:
        print(f"Error showing user bookings: {e}")
        bot.send_message(
            chat_id,
            "❌ Error retrieving your bookings. Please try again.",
            reply_markup=create_main_menu()
        )

def show_services_menu(message):
    """Show services and pricing"""
    services_msg = "✂️ ELITE BARBER SHOP SERVICES\n\n"
    
    for service, details in SERVICES.items():
        services_msg += f"🔸 {service}\n"
        services_msg += f"   💰 ${details['price']} | ⏱️ {details['duration']} min\n\n"
    
    services_msg += "💡 Click 'Book Appointment' to schedule your service!"
    
    bot.send_message(message.chat.id, services_msg, reply_markup=create_main_menu())

# === Error Handlers ===

@bot.message_handler(content_types=['photo', 'document', 'audio', 'video', 'voice', 'location', 'contact', 'sticker'])
def handle_non_text(message):
    """Handle non-text messages"""
    bot.send_message(
        message.chat.id,
        "I can only process text messages right now. How can I help you with your appointment?",
        reply_markup=create_main_menu()
    )

# === Run Flask App ===
if __name__ == "__main__":
    print("🚀 Elite Barber Shop Bot Starting...")
    print(f"🤖 Bot Token: {API_TOKEN[:10]}...")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# === For Local Testing (Uncomment for polling) ===
# if __name__ == "__main__":
#     print("🚀 Starting bot in polling mode...")
#     bot.polling(none_stop=True)