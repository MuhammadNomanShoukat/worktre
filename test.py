from datetime import datetime
import pytz
from tzlocal import get_localzone  # pip install tzlocal

def convert_time_range_from_gmt_to_local(time_range_str):
    gmt_zone = pytz.timezone('GMT')
    local_zone = get_localzone()  # Auto-detect local system timezone

    today = datetime.now().date()

    # Split time range (e.g., "4:00 AM - 1:00 PM")
    start_str, end_str = time_range_str.split(' - ')

    # Parse into naive datetime (without timezone)
    start_naive = datetime.strptime(f"{today} {start_str}", "%Y-%m-%d %I:%M %p")
    end_naive = datetime.strptime(f"{today} {end_str}", "%Y-%m-%d %I:%M %p")

    # Attach GMT timezone
    start_aware = gmt_zone.localize(start_naive)
    end_aware = gmt_zone.localize(end_naive)

    # Convert to local time
    local_start = start_aware.astimezone(local_zone)
    local_end = end_aware.astimezone(local_zone)

    # Format result (remove leading zero if needed)
    def format_time(dt):
        return dt.strftime('%I:%M %p').lstrip("0")

    return f"{format_time(local_start)} - {format_time(local_end)}"

# ✅ Example usage
time_range = "4:00 AM - 1:00 PM"  # GMT time
converted = convert_time_range_from_gmt_to_local(time_range)
print("Converted to local time:", converted)
