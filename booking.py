# =========================
# File: booking.py
# Purpose: Handle booking management with Google Sheets integration
# =========================

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

import gspread
from google.oauth2.service_account import Credentials
from config import BOOKING_DB_PATH, GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID

# Google Sheets setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_sheets_client():
    """Initialize Google Sheets client with better error handling"""
    try:
        # Check if credentials file exists
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS):
            print(f"Warning: Google Sheets credentials file not found at {GOOGLE_SHEETS_CREDENTIALS}")
            return None
            
        creds = Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def get_worksheet(worksheet_name="Bookings"):
    """Get the specified worksheet with error handling"""
    try:
        client = get_google_sheets_client()
        if not client:
            print("Google Sheets client not available")
            return None
            
        sheet = client.open_by_key(SPREADSHEET_ID)
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            # Create worksheet if it doesn't exist
            print(f"Creating new worksheet: {worksheet_name}")
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            # Add headers
            headers = [
                "ID", "Name", "Date", "Time", "Service", 
                "User ID", "Status", "Created", "Phone", "Notes"
            ]
            worksheet.append_row(headers)
            print("Headers added to new worksheet")
        return worksheet
    except Exception as e:
        print(f"Error accessing worksheet: {e}")
        return None

# === Local JSON Database Functions ===

def ensure_booking_file():
    """Ensure booking file exists"""
    if not os.path.exists(BOOKING_DB_PATH):
        with open(BOOKING_DB_PATH, 'w') as f:
            json.dump([], f)
        print(f"Created new booking file: {BOOKING_DB_PATH}")

def load_bookings():
    """Load all bookings from the JSON file"""
    try:
        ensure_booking_file()
        with open(BOOKING_DB_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        print("Booking file not found, creating new one")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing booking file: {e}")
        return []
    except Exception as e:
        print(f"Error loading bookings: {e}")
        return []

def save_bookings(bookings):
    """Save all bookings to the JSON file"""
    try:
        with open(BOOKING_DB_PATH, 'w') as f:
            json.dump(bookings, f, indent=2)
        print(f"Saved {len(bookings)} bookings to file")
    except Exception as e:
        print(f"Error saving bookings: {e}")

# === Enhanced Booking Functions ===

def add_booking(name: str, datetime_str: str, service: str, user_id: int = None) -> bool:
    """Add a new booking to both local storage and Google Sheets"""
    try:
        print(f"Adding booking: {name}, {datetime_str}, {service}, {user_id}")
        
        booking_id = str(uuid.uuid4())[:8]
        
        # Parse datetime with better error handling
        try:
            booking_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            print(f"Error parsing datetime: {datetime_str}")
            return False
            
        date_str = booking_datetime.strftime("%Y-%m-%d")
        time_str = booking_datetime.strftime("%I:%M %p")
        
        print(f"Parsed date: {date_str}, time: {time_str}")
        
        # Check availability first
        if not check_availability(date_str, time_str):
            print(f"Time slot not available: {date_str} {time_str}")
            return False
        
        booking = {
            "id": booking_id,
            "name": name.strip(),
            "date": date_str,
            "time": time_str,
            "service": service,
            "user_id": user_id,
            "status": "confirmed",
            "created": datetime.now().isoformat(),
            "phone": "",
            "notes": ""
        }
        
        print(f"Created booking object: {booking}")
        
        # Save to local JSON first
        bookings = load_bookings()
        bookings.append(booking)
        save_bookings(bookings)
        
        print("Booking saved to local file")
        
        # Try to save to Google Sheets (don't fail if this doesn't work)
        try:
            sync_to_google_sheets(booking, action="add")
            print("Booking synced to Google Sheets")
        except Exception as e:
            print(f"Warning: Could not sync to Google Sheets: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error adding booking: {e}")
        return False

def sync_to_google_sheets(booking: Dict, action: str = "add"):
    """Sync booking data to Google Sheets"""
    try:
        worksheet = get_worksheet()
        if not worksheet:
            print("Cannot sync to Google Sheets - worksheet not available")
            return False
        
        row_data = [
            booking["id"],
            booking["name"],
            booking["date"],
            booking["time"],
            booking["service"],
            str(booking.get("user_id", "")),
            booking["status"],
            booking["created"],
            booking.get("phone", ""),
            booking.get("notes", "")
        ]
        
        if action == "add":
            worksheet.append_row(row_data)
            print(f"Added booking {booking['id']} to Google Sheets")
        elif action == "update":
            # Find the row and update it
            all_records = worksheet.get_all_records()
            for i, record in enumerate(all_records, start=2):  # Start from row 2 (after headers)
                if record["ID"] == booking["id"]:
                    for j, value in enumerate(row_data, start=1):
                        worksheet.update_cell(i, j, value)
                    print(f"Updated booking {booking['id']} in Google Sheets")
                    break
        
        return True
    except Exception as e:
        print(f"Error syncing to Google Sheets: {e}")
        return False

def check_availability(date_str: str, time_str: str) -> bool:
    """Check if a time slot is available"""
    try:
        bookings = load_bookings()
        
        # Check for existing bookings at the same date and time
        for booking in bookings:
            if (booking["date"] == date_str and 
                booking["time"] == time_str and 
                booking["status"] in ["confirmed", "pending"]):
                return False
        
        # Check if the time slot is in the past
        booking_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
        if booking_datetime <= datetime.now():
            return False
        
        return True
    except Exception as e:
        print(f"Error checking availability: {e}")
        return False

def get_bookings_by_date(date_str: str) -> List[Dict]:
    """Get all bookings for a specific date"""
    try:
        bookings = load_bookings()
        return [b for b in bookings if b["date"] == date_str and b["status"] != "cancelled"]
    except Exception as e:
        print(f"Error getting bookings by date: {e}")
        return []

def get_bookings_for_date(date_str: str) -> List[Dict]:
    """Alias for get_bookings_by_date for backward compatibility"""
    return get_bookings_by_date(date_str)

def get_bookings_by_user(user_id: int) -> List[Dict]:
    """Get all bookings for a specific user"""
    try:
        bookings = load_bookings()
        return [b for b in bookings if b.get("user_id") == user_id and b["status"] != "cancelled"]
    except Exception as e:
        print(f"Error getting bookings by user: {e}")
        return []

def get_user_bookings(user_id: int) -> List[Dict]:
    """Alias for get_bookings_by_user for backward compatibility"""
    return get_bookings_by_user(user_id)

def get_booking_by_id(booking_id: str) -> Optional[Dict]:
    """Get a specific booking by ID"""
    try:
        bookings = load_bookings()
        for booking in bookings:
            if booking["id"] == booking_id:
                return booking
        return None
    except Exception as e:
        print(f"Error getting booking by ID: {e}")
        return None

def update_booking(booking_id: str, updates: Dict) -> bool:
    """Update an existing booking"""
    try:
        bookings = load_bookings()
        
        for i, booking in enumerate(bookings):
            if booking["id"] == booking_id:
                # Update the booking with new data
                for key, value in updates.items():
                    if key in booking:
                        booking[key] = value
                
                # Save to local file
                save_bookings(bookings)
                
                # Try to sync to Google Sheets
                try:
                    sync_to_google_sheets(booking, action="update")
                    print(f"Updated booking {booking_id} in Google Sheets")
                except Exception as e:
                    print(f"Warning: Could not sync update to Google Sheets: {e}")
                
                return True
        
        print(f"Booking {booking_id} not found")
        return False
    except Exception as e:
        print(f"Error updating booking: {e}")
        return False

def cancel_booking(booking_id: str) -> bool:
    """Cancel a booking"""
    try:
        return update_booking(booking_id, {"status": "cancelled"})
    except Exception as e:
        print(f"Error cancelling booking: {e}")
        return False

def get_available_slots(date_str: str, start_hour: int = 9, end_hour: int = 17, slot_duration: int = 60) -> List[str]:
    """Get available time slots for a given date"""
    try:
        available_slots = []
        current_time = datetime.strptime(f"{date_str} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date_str} {end_hour:02d}:00", "%Y-%m-%d %H:%M")
        
        while current_time < end_time:
            time_str = current_time.strftime("%I:%M %p")
            if check_availability(date_str, time_str):
                available_slots.append(time_str)
            current_time += timedelta(minutes=slot_duration)
        
        return available_slots
    except Exception as e:
        print(f"Error getting available slots: {e}")
        return []

def get_upcoming_bookings(days_ahead: int = 7) -> List[Dict]:
    """Get upcoming bookings within the specified number of days"""
    try:
        bookings = load_bookings()
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for booking in bookings:
            if booking["status"] in ["confirmed", "pending"]:
                booking_date = datetime.strptime(booking["date"], "%Y-%m-%d").date()
                if today <= booking_date <= end_date:
                    upcoming.append(booking)
        
        # Sort by date and time
        upcoming.sort(key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %I:%M %p"))
        return upcoming
    except Exception as e:
        print(f"Error getting upcoming bookings: {e}")
        return []

def cleanup_old_bookings(days_old: int = 30):
    """Remove old bookings from the database"""
    try:
        bookings = load_bookings()
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        filtered_bookings = []
        removed_count = 0
        
        for booking in bookings:
            booking_date = datetime.strptime(booking["date"], "%Y-%m-%d")
            if booking_date >= cutoff_date or booking["status"] == "confirmed":
                filtered_bookings.append(booking)
            else:
                removed_count += 1
        
        if removed_count > 0:
            save_bookings(filtered_bookings)
            print(f"Removed {removed_count} old bookings")
        
        return removed_count
    except Exception as e:
        print(f"Error cleaning up old bookings: {e}")
        return 0

def export_bookings_to_csv(filename: str = None) -> str:
    """Export all bookings to a CSV file"""
    try:
        import csv
        
        if not filename:
            filename = f"bookings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        bookings = load_bookings()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'date', 'time', 'service', 'user_id', 'status', 'created', 'phone', 'notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for booking in bookings:
                writer.writerow(booking)
        
        print(f"Exported {len(bookings)} bookings to {filename}")
        return filename
    except Exception as e:
        print(f"Error exporting bookings: {e}")
        return None

def get_booking_statistics() -> Dict:
    """Get booking statistics"""
    try:
        bookings = load_bookings()
        
        stats = {
            "total_bookings": len(bookings),
            "confirmed": len([b for b in bookings if b["status"] == "confirmed"]),
            "pending": len([b for b in bookings if b["status"] == "pending"]),
            "cancelled": len([b for b in bookings if b["status"] == "cancelled"]),
            "today": 0,
            "this_week": 0,
            "this_month": 0
        }
        
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        for booking in bookings:
            if booking["status"] in ["confirmed", "pending"]:
                booking_date = datetime.strptime(booking["date"], "%Y-%m-%d").date()
                
                if booking_date == today:
                    stats["today"] += 1
                if booking_date >= week_start:
                    stats["this_week"] += 1
                if booking_date >= month_start:
                    stats["this_month"] += 1
        
        return stats
    except Exception as e:
        print(f"Error getting booking statistics: {e}")
        return {}

# === Testing Functions ===

def test_booking_system():
    """Test the booking system functionality"""
    print("Testing booking system...")
    
    # Test adding a booking
    test_datetime = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %I:%M %p")
    result = add_booking("Test User", test_datetime, "Test Service", user_id=123)
    print(f"Add booking test: {'PASSED' if result else 'FAILED'}")
    
    # Test getting bookings
    bookings = load_bookings()
    print(f"Load bookings test: {'PASSED' if len(bookings) > 0 else 'FAILED'}")
    
    # Test availability check
    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    available = check_availability(date_str, "09:00 AM")
    print(f"Availability check test: {'PASSED' if isinstance(available, bool) else 'FAILED'}")
    
    # Test statistics
    stats = get_booking_statistics()
    print(f"Statistics test: {'PASSED' if isinstance(stats, dict) else 'FAILED'}")
    
    print("Testing completed!")

if __name__ == "__main__":
    test_booking_system()