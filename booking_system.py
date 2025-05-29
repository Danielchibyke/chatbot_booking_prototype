
import datetime

# --- Simulated Available Slots ---
# For a prototype, we'll pre-define some slots.
# In a real system, this would come from Google Calendar or a DB.
AVAILABLE_SLOTS = {
    "consultation": {
        "2025-06-03": ["10:00", "11:00", "14:00"], # Tuesday, June 3rd
        "2025-06-04": ["09:00", "10:00", "13:00"], # Wednesday, June 4th
    },
    "haircut": {
        "2025-06-03": ["09:00", "12:00", "15:00"],
        "2025-06-05": ["10:00", "11:00", "14:00"], # Thursday, June 5th
    },
    # Add more services as needed
}

# --- Simulated Booked Appointments ---
BOOKED_APPOINTMENTS = []

def check_availability(service_type, date_str):
    """
    Simulates checking available slots for a given service and date.
    date_str format: YYYY-MM-DD
    """
    if service_type not in AVAILABLE_SLOTS:
        return [] # Service not found

    available_on_date = AVAILABLE_SLOTS[service_type].get(date_str, [])
    
    # Filter out already booked times
    booked_times_on_date = [
        app['time'] for app in BOOKED_APPOINTMENTS
        if app['service'] == service_type and app['date'] == date_str
    ]
    
    truly_available = [
        slot for slot in available_on_date
        if slot not in booked_times_on_date
    ]
    return truly_available

def book_appointment(service_type, date_str, time_str, user_name):
    """
    Simulates booking an appointment.
    Returns True if successful, False otherwise (e.g., slot taken).
    """
    # Check if slot is still available (important for "real-time" accuracy)
    current_available = check_availability(service_type, date_str)
    if time_str not in current_available:
        return False # Slot no longer available or was never available

    appointment = {
        "service": service_type,
        "date": date_str,
        "time": time_str,
        "user_name": user_name,
        "booking_time": datetime.datetime.now().isoformat()
    }
    BOOKED_APPOINTMENTS.append(appointment)
    print(f"\n--- SIMULATED BOOKING CONFIRMED ---")
    print(f"Service: {appointment['service']}")
    print(f"Date: {appointment['date']}")
    print(f"Time: {appointment['time']}")
    print(f"Booked by: {appointment['user_name']}")
    print(f"-----------------------------------\n")
    return True

def get_all_services():
    """Returns a list of all services available."""
    return list(AVAILABLE_SLOTS.keys())

# Example usage (for testing this module directly)
if __name__ == "__main__":
    print("Available services:", get_all_services())
    
    # Test availability
    print(f"Availability for consultation on 2025-06-03: {check_availability('consultation', '2025-06-03')}")
    print(f"Availability for haircut on 2025-06-05: {check_availability('haircut', '2025-06-05')}")

    # Try booking
    success = book_appointment("haircut", "2025-06-05", "10:00", "Alice Smith")
    if success:
        print("Booking successful!")
    else:
        print("Booking failed (slot taken or invalid).")
    
    print(f"Updated availability for haircut on 2025-06-05: {check_availability('haircut', '2025-06-05')}")
    print("\nAll booked appointments:", BOOKED_APPOINTMENTS)