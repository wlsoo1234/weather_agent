
import requests

# GEOCODING_API_URL = "https://api.openweathermap.org/geo/1.0/direct"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_weather(city: str, day: str = "today") -> dict:
    """
    Get the weather forecast for a given city and day.

    Args:
        city: City name, optionally with a country.
        day: Either 'today' or 'tomorrow'.
    Returns:
        A dictionary containing the weather forecast.
    """

    if day not in ("today", "tomorrow"):
        raise ValueError("day must be either 'today' or 'tomorrow'")

    try: 
        location_response = requests.get(GEOCODING_API_URL, params={"name": city, "count": 1, "language": "en"}, timeout=10)

        location_response.raise_for_status()
        locations = location_response.json().get("results", [])

        if not locations:
            raise ValueError(f"City '{city}' not found.")

        location = locations[0]
        weather_response = requests.get(
            FORECAST_API_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weathercode",
                "daily":(
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,weather_code"
                ),
                "timezone": "auto",
                "forecast_days": 2,
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        index = 0 if day == "today" else 1
        daily_data = weather_data["daily"]
        code = daily_data["weather_code"][index]

        result = {
            "city": location["name"],
            "country": location.get("country", ""),
            "date": daily_data["time"][index],
            "condition": WEATHER_CODES.get(code, f"Unknown weather code: {code}"),
            "temperature_max": daily_data["temperature_2m_max"][index],
            "temperature_min": daily_data["temperature_2m_min"][index],
            "precipitation_probability": daily_data["precipitation_probability_max"][index],
        }

        if day == "today":
            current_data = weather_data["current"]
            result.update({
                "current_temperature": current_data["temperature_2m"],
                "current_humidity": current_data["relative_humidity_2m"],
                "current_condition": WEATHER_CODES.get(current_data["weathercode"], f"Unknown weather code: {current_data['weathercode']}"),
                "observation_time": current_data.get("time", ""),
            })

        return result

    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching weather data: {e}")

if __name__ == "__main__":
    city = input("Enter city name (optionally with country): ")
    day = input("Enter day ('today' or 'tomorrow'): ")

    try:
        weather_info = get_weather(city, day)
        print(f"Weather forecast for {weather_info['city']}, {weather_info['country']} on {weather_info['date']}:")
        print(f"Condition: {weather_info['condition']}")
        print(f"Max Temperature: {weather_info['temperature_max']}°C")
        print(f"Min Temperature: {weather_info['temperature_min']}°C")
        print(f"Precipitation Probability: {weather_info['precipitation_probability']}%")

        if day == "today":
            print(f"Current Temperature: {weather_info['current_temperature']}°C")
            print(f"Current Humidity: {weather_info['current_humidity']}%")
            print(f"Current Condition: {weather_info['current_condition']}")
            print(f"Observation Time: {weather_info['observation_time']}")

    except Exception as e:
        print(e)
        