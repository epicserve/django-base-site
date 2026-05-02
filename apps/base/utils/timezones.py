# Friendly display labels for common IANA timezones.
# Must stay in sync with src/js/utils/timezones.js

TIMEZONE_LABELS = {
    # North America
    "Pacific/Honolulu": "Hawaii (HST)",
    "America/Anchorage": "Alaska (AKST)",
    "America/Los_Angeles": "Pacific Time (US & Canada)",
    "America/Phoenix": "Arizona (no DST)",
    "America/Denver": "Mountain Time (US & Canada)",
    "America/Chicago": "Central Time (US & Canada)",
    "America/New_York": "Eastern Time (US & Canada)",
    "America/Halifax": "Atlantic Time (Canada)",
    "America/St_Johns": "Newfoundland (Canada)",
    "America/Mexico_City": "Mexico City",
    "America/Tijuana": "Tijuana (Pacific Mexico)",
    # Central & South America
    "America/Bogota": "Bogota, Lima",
    "America/Caracas": "Caracas",
    "America/Santiago": "Santiago",
    "America/Sao_Paulo": "Brasilia, Sao Paulo",
    "America/Argentina/Buenos_Aires": "Buenos Aires",
    # Europe
    "Atlantic/Reykjavik": "Reykjavik (no DST)",
    "Europe/London": "London, Dublin, Edinburgh",
    "Europe/Paris": "Paris, Berlin, Amsterdam",
    "Europe/Helsinki": "Helsinki, Kyiv, Bucharest",
    "Europe/Moscow": "Moscow, St. Petersburg",
    "Europe/Istanbul": "Istanbul",
    "Europe/Lisbon": "Lisbon",
    "Europe/Madrid": "Madrid",
    "Europe/Warsaw": "Warsaw, Prague",
    "Europe/Athens": "Athens",
    # Africa
    "Africa/Cairo": "Cairo",
    "Africa/Lagos": "Lagos, West Africa",
    "Africa/Johannesburg": "Johannesburg, South Africa",
    "Africa/Nairobi": "Nairobi, East Africa",
    # Middle East
    "Asia/Dubai": "Dubai, Abu Dhabi",
    "Asia/Riyadh": "Riyadh, Kuwait",
    "Asia/Tehran": "Tehran",
    "Asia/Jerusalem": "Jerusalem, Tel Aviv",
    # Asia
    "Asia/Karachi": "Karachi, Islamabad",
    "Asia/Kolkata": "Mumbai, New Delhi, Kolkata",
    "Asia/Dhaka": "Dhaka",
    "Asia/Bangkok": "Bangkok, Hanoi, Jakarta",
    "Asia/Singapore": "Singapore, Kuala Lumpur",
    "Asia/Shanghai": "Beijing, Shanghai, Hong Kong",
    "Asia/Tokyo": "Tokyo, Osaka",
    "Asia/Seoul": "Seoul",
    "Asia/Taipei": "Taipei",
    # Oceania
    "Australia/Perth": "Perth (Western Australia)",
    "Australia/Adelaide": "Adelaide (South Australia)",
    "Australia/Sydney": "Sydney, Melbourne",
    "Pacific/Auckland": "Auckland, Wellington",
    "Pacific/Fiji": "Fiji",
}


def get_timezone_label(iana_key):
    """Return a friendly label for an IANA timezone, or the key itself if not mapped."""
    return TIMEZONE_LABELS.get(iana_key, iana_key)
