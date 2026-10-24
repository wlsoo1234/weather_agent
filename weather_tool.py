
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

def search_location(query: str) -> dict:
    """
    Search for a location using the geocoding API.

    Args:
        query: The location query string.
    """

    if len(query.strip()) < 2  :
        raise ValueError("Query must be at least 2 characters long.")

    try:
        response = requests.get(GEOCODING_API_URL, params={"name": query, "count": 5, "language": "en"}, timeout=10)
        response.raise_for_status()
        locations = response.json().get("results", [])

        if not locations:
            raise ValueError(f"No results found for '{query}'.")

        return {
            "query": query,
            "locations": [
                {
                    "name": loc["name"],
                    "country": loc.get("country", ""),
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                }
                for loc in locations
            ],
        }

    except requests.RequestException as e:
        raise RuntimeError(f"Error searching for location: {e}")

def resolve_location(city: str) -> dict:
    """
    Resolve a city name to its geographical coordinates.

    Args:
        city: City name, optionally with a country.
    Returns:
        A dictionary containing the resolved location information.
    """

    city_name, separator, country_name = city.partition(",")
    try:
        result = search_location(city)
    except ValueError:
        if not separator:
            raise
        result = search_location(city_name.strip())

    if "error" in result:
        raise ValueError(f"Error resolving location: {result['error']}")

    locations = result["locations"]

    if separator:
        country = country_name.strip().casefold()
        country = {
            "uk": "united kingdom",
            "england": "united kingdom",
            "us": "united states",
            "usa": "united states",
        }.get(country, country)
        locations = [
            location for location in locations
            if location["country"].casefold() == country
        ]

    if not locations:
        raise ValueError(f"City '{city}' not found.")

    return locations[0]  # Return the first matching location


def fetch_daily_forecast(city:str, days:int = 7) -> dict:
    """
    Fetch the daily weather forecast for a given city.

    Args:
        city: City name, optionally with a country.
        days: Number of days to fetch the forecast for (default is 7).
    """

    if days < 1 or days > 16:
        raise ValueError("days must be between 1 and 16")

    location = resolve_location(city)

    try:
        weather_response = requests.get(
            FORECAST_API_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": (
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,weather_code"
                ),
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=10,
        )
        weather_response.raise_for_status()

        data = weather_response.json()
        daily = data["daily"]

        forecast = []

        for i, date in enumerate(daily["time"]):
            code = daily["weather_code"][i]
            forecast.append({
                "date": date,
                "condition": WEATHER_CODES.get(code, f"Unknown weather code: {code}"),
                "max_temp_c": daily["temperature_2m_max"][i],
                "min_temp_c": daily["temperature_2m_min"][i],
                "max_rain_probability_percent": (
                    daily["precipitation_probability_max"][i]
                ),
            })

        return {
            "location": location,
            "timezone": data.get("timezone", "unknown"),
                "forecast": forecast,
        }

    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching daily forecast: {e}")

# def get_weather(city: str, day: str = "today") -> dict:
#     """
#     Get the weather forecast for a given city and day.

#     Args:
#         city: City name, optionally with a country.
#         day: Either 'today' or 'tomorrow'.
#     Returns:
#         A dictionary containing the weather forecast.
#     """

#     if day not in ("today", "tomorrow"):
#         raise ValueError("day must be either 'today' or 'tomorrow'")

#     try:
#         location_response = requests.get(GEOCODING_API_URL, params={"name": city, "count": 1, "language": "en"}, timeout=10)

#         location_response.raise_for_status()
#         locations = location_response.json().get("results", [])

#         if not locations:
#             raise ValueError(f"City '{city}' not found.")

#         location = locations[0]
#         weather_response = requests.get(
#             FORECAST_API_URL,
#             params={
#                 "latitude": location["latitude"],
#                 "longitude": location["longitude"],
#                 "current": "temperature_2m,relative_humidity_2m,weathercode",
#                 "daily":(
#                     "temperature_2m_max,temperature_2m_min,"
#                     "precipitation_probability_max,weather_code"
#                 ),
#                 "timezone": "auto",
#                 "forecast_days": 2,
#             },
#             timeout=10,
#         )
#         weather_response.raise_for_status()
#         weather_data = weather_response.json()

#         index = 0 if day == "today" else 1
#         daily_data = weather_data["daily"]
#         code = daily_data["weather_code"][index]

#         result = {
#             "city": location["name"],
#             "country": location.get("country", ""),
#             "date": daily_data["time"][index],
#             "condition": WEATHER_CODES.get(code, f"Unknown weather code: {code}"),
#             "temperature_max": daily_data["temperature_2m_max"][index],
#             "temperature_min": daily_data["temperature_2m_min"][index],
#             "precipitation_probability": daily_data["precipitation_probability_max"][index],
#         }

#         if day == "today":
#             current_data = weather_data["current"]
#             result.update({
#                 "current_temperature": current_data["temperature_2m"],
#                 "current_humidity": current_data["relative_humidity_2m"],
#                 "current_condition": WEATHER_CODES.get(current_data["weathercode"], f"Unknown weather code: {current_data['weathercode']}"),
#                 "observation_time": current_data.get("time", ""),
#             })

#         return result

#     except requests.RequestException as e:
#         raise RuntimeError(f"Error fetching weather data: {e}")

def get_weather(city: str, day: str = "today") -> dict:
    """Get today's or tomorrow's daily weather forecast.

    Args:
        city: City name, optionally followed by country.
        day: Either 'today' or 'tomorrow'.
    """
    if day not in ("today", "tomorrow"):
        return {"error": "day must be today or tomorrow"}

    try:
        index = 0 if day == "today" else 1
        result = fetch_daily_forecast(city, days=index + 1)

        return {
            "location": result["location"],
            "timezone": result["timezone"],
            "forecast": result["forecast"][index],
        }

    except (requests.RequestException, ValueError, KeyError) as exc:
        return {"error": str(exc)}

def compare_weather(city1: str, city2: str, day: str = "today"):
    """Compare the weather forecast for two cities.

    Args:
        city1: First city name, optionally followed by country.
        city2: Second city name, optionally followed by country.
        day: Either 'today' or 'tomorrow'.
    """
    first = get_weather(city1, day)
    second = get_weather(city2, day)

    if "error" in first or "error" in second:
        return {
            "error": first.get("error") or second.get("error"),
            "city_a_result": first,
            "city_b_result": second,
            }

    a = first["forecast"]
    b = second["forecast"]

    return {
        "day": day,
        "city_a": first,
        "city_b": second,
        "max_temperature_difference": round(abs(a["max_temp_c"] - b["max_temp_c"]), 1),
        "rain_probability_difference_points": abs(a["max_rain_probability_percent"] - b["max_rain_probability_percent"]),
    }

def get_forecast(city: str, days: int = 7) -> dict:
    """Get the daily weather forecast for a given city.

    Args:
        city: City name, optionally followed by country.
        days: Number of days to fetch the forecast for (default is 7).
    """
    try:
        result = fetch_daily_forecast(city, days=days)
        return result
    except (requests.RequestException, ValueError, KeyError) as exc:
        return {"error": str(exc)}



if __name__ == "__main__":
    # city = input("Enter city name (optionally with country): ")
    # day = input("Enter day ('today' or 'tomorrow'): ")

    # try:
    #     weather_info = get_weather(city, day)
    #     print(f"Weather forecast for {weather_info['city']}, {weather_info['country']} on {weather_info['date']}:")
    #     print(f"Condition: {weather_info['condition']}")
    #     print(f"Max Temperature: {weather_info['temperature_max']}°C")
    #     print(f"Min Temperature: {weather_info['temperature_min']}°C")
    #     print(f"Precipitation Probability: {weather_info['precipitation_probability']}%")

    #     if day == "today":
    #         print(f"Current Temperature: {weather_info['current_temperature']}°C")
    #         print(f"Current Humidity: {weather_info['current_humidity']}%")
    #         print(f"Current Condition: {weather_info['current_condition']}")
    #         print(f"Observation Time: {weather_info['observation_time']}")

    # except Exception as e:
    #     print(e)

    print(search_location("New York"))
    print(get_forecast("New York", 5))
    print(get_weather("New York", "today"))
    print(compare_weather("New York", "Los Angeles", "today"))
    print(get_forecast("Los Angeles", 3))
