# Weather Agent

A weather assistant powered by a local Ollama model and Open-Meteo. The repository has two terminal agents and a Streamlit interface that share the same weather functions:

| Script | Agent implementation | Conversation memory |
| --- | --- | --- |
| `agent.py` | Direct Ollama tool calls | Python message list, kept for the current process |
| `langchain_agent.py` | LangChain agent with LangGraph checkpointing | In-memory checkpoint for the current thread and process |
| `app.py` | Streamlit interface using the LangChain agent | Browser session plus the in-memory LangGraph checkpoint |

## Requirements

- Python 3.10 or newer
- Ollama installed and running locally
- Internet access for Open-Meteo's geocoding and forecast APIs

Both agents use the `qwen3.5:4b` model. Its name is configured separately in each script.

## Setup

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen3.5:4b
```

Start Ollama if it is not already running:

```bash
ollama serve
```

Leave Ollama running and open another terminal in this folder to start an agent.

## Run an agent

Activate the environment and choose one implementation:

```bash
source .venv/bin/activate
python agent.py
```

Or:

```bash
source .venv/bin/activate
python langchain_agent.py
```

Example questions:

```text
Find locations named Springfield.
What's the weather in Kuala Lumpur today?
What about tomorrow?
Give me the 7-day forecast for Tokyo.
Compare tomorrow's weather in London and Singapore, then give me Singapore's 5-day forecast.
```

Both CLIs support `/memory`, `/reset`, and `/exit`. `/memory` shows the messages kept in the current conversation, including tool activity. `/reset` starts a fresh conversation. Memory is held in RAM and is lost when the process exits. Restart the script after changing its code; `/reset` does not reload Python files.

## Run the web interface

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

The sidebar has a **New conversation** button and a **Show tool execution** option. The web interface uses the LangChain agent and keeps its displayed chat in the browser session. Its checkpoint data is held in server memory, so a server restart clears it. [Streamlit's CLI documentation](https://docs.streamlit.io/develop/api-reference/cli/run) describes the `run` command.

## Weather tools and limits

`weather_tool.py` provides four functions used by both agents:

| Function | Purpose |
| --- | --- |
| `search_location(query)` | Return up to five matching locations and coordinates. |
| `get_weather(city, day)` | Return a daily forecast for `today` or `tomorrow`. |
| `compare_weather(city1, city2, day)` | Compare two cities for `today` or `tomorrow`. |
| `get_forecast(city, days)` | Return 1 to 16 days of daily forecasts. |

The functions use Open-Meteo's geocoding and forecast APIs. They provide daily conditions, high and low temperatures in °C, and maximum precipitation probability. They do not provide a live current temperature. No API key is configured in this project.

Forecast dates use each location's local time zone, so “tomorrow” can have a different date for two cities. Weather lookups select the first matching location; use `search_location` or include a country when a city name is ambiguous.

## Troubleshooting

- If the agent cannot connect to Ollama, check that `ollama serve` is running.
- If the model is unavailable, run `ollama pull qwen3.5:4b` or change the model name in the script you use.
- If a city is not found, try its full name and country.
