/**
 * Common timezones with user-friendly display labels.
 * Stored value is always the IANA timezone key.
 * Searchable by label, IANA key, or abbreviation.
 */
const TIMEZONE_CHOICES = [
  // North America
  { value: 'Pacific/Honolulu', label: 'Hawaii (HST)', region: 'North America' },
  { value: 'America/Anchorage', label: 'Alaska (AKST)', region: 'North America' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)', region: 'North America' },
  { value: 'America/Phoenix', label: 'Arizona (no DST)', region: 'North America' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)', region: 'North America' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)', region: 'North America' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)', region: 'North America' },
  { value: 'America/Halifax', label: 'Atlantic Time (Canada)', region: 'North America' },
  { value: 'America/St_Johns', label: 'Newfoundland (Canada)', region: 'North America' },
  { value: 'America/Mexico_City', label: 'Mexico City', region: 'North America' },
  { value: 'America/Tijuana', label: 'Tijuana (Pacific Mexico)', region: 'North America' },

  // Central & South America
  { value: 'America/Bogota', label: 'Bogota, Lima', region: 'South America' },
  { value: 'America/Caracas', label: 'Caracas', region: 'South America' },
  { value: 'America/Santiago', label: 'Santiago', region: 'South America' },
  { value: 'America/Sao_Paulo', label: 'Brasilia, Sao Paulo', region: 'South America' },
  { value: 'America/Argentina/Buenos_Aires', label: 'Buenos Aires', region: 'South America' },

  // Europe
  { value: 'Atlantic/Reykjavik', label: 'Reykjavik (no DST)', region: 'Europe' },
  { value: 'Europe/London', label: 'London, Dublin, Edinburgh', region: 'Europe' },
  { value: 'Europe/Paris', label: 'Paris, Berlin, Amsterdam', region: 'Europe' },
  { value: 'Europe/Helsinki', label: 'Helsinki, Kyiv, Bucharest', region: 'Europe' },
  { value: 'Europe/Moscow', label: 'Moscow, St. Petersburg', region: 'Europe' },
  { value: 'Europe/Istanbul', label: 'Istanbul', region: 'Europe' },
  { value: 'Europe/Lisbon', label: 'Lisbon', region: 'Europe' },
  { value: 'Europe/Madrid', label: 'Madrid', region: 'Europe' },
  { value: 'Europe/Warsaw', label: 'Warsaw, Prague', region: 'Europe' },
  { value: 'Europe/Athens', label: 'Athens', region: 'Europe' },

  // Africa
  { value: 'Africa/Cairo', label: 'Cairo', region: 'Africa' },
  { value: 'Africa/Lagos', label: 'Lagos, West Africa', region: 'Africa' },
  { value: 'Africa/Johannesburg', label: 'Johannesburg, South Africa', region: 'Africa' },
  { value: 'Africa/Nairobi', label: 'Nairobi, East Africa', region: 'Africa' },

  // Middle East
  { value: 'Asia/Dubai', label: 'Dubai, Abu Dhabi', region: 'Middle East' },
  { value: 'Asia/Riyadh', label: 'Riyadh, Kuwait', region: 'Middle East' },
  { value: 'Asia/Tehran', label: 'Tehran', region: 'Middle East' },
  { value: 'Asia/Jerusalem', label: 'Jerusalem, Tel Aviv', region: 'Middle East' },

  // Asia
  { value: 'Asia/Karachi', label: 'Karachi, Islamabad', region: 'Asia' },
  { value: 'Asia/Kolkata', label: 'Mumbai, New Delhi, Kolkata', region: 'Asia' },
  { value: 'Asia/Dhaka', label: 'Dhaka', region: 'Asia' },
  { value: 'Asia/Bangkok', label: 'Bangkok, Hanoi, Jakarta', region: 'Asia' },
  { value: 'Asia/Singapore', label: 'Singapore, Kuala Lumpur', region: 'Asia' },
  { value: 'Asia/Shanghai', label: 'Beijing, Shanghai, Hong Kong', region: 'Asia' },
  { value: 'Asia/Tokyo', label: 'Tokyo, Osaka', region: 'Asia' },
  { value: 'Asia/Seoul', label: 'Seoul', region: 'Asia' },
  { value: 'Asia/Taipei', label: 'Taipei', region: 'Asia' },

  // Oceania
  { value: 'Australia/Perth', label: 'Perth (Western Australia)', region: 'Oceania' },
  { value: 'Australia/Adelaide', label: 'Adelaide (South Australia)', region: 'Oceania' },
  { value: 'Australia/Sydney', label: 'Sydney, Melbourne', region: 'Oceania' },
  { value: 'Pacific/Auckland', label: 'Auckland, Wellington', region: 'Oceania' },
  { value: 'Pacific/Fiji', label: 'Fiji', region: 'Oceania' },
];

/**
 * Look up the friendly label for an IANA timezone key.
 * Returns the IANA key itself if no friendly label exists.
 */
export function getTimezoneLabel(ianaKey) {
  const entry = TIMEZONE_CHOICES.find((tz) => tz.value === ianaKey);
  return entry ? entry.label : ianaKey;
}

export default TIMEZONE_CHOICES;
