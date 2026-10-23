# Weather Agent

A small command-line weather assistant. It uses a local Ollama model to understand a question and calls Open-Meteo for a city's current conditions and forecast.

## Requirements

- Python 3.10 or newer
- Ollama installed and running locally
- Internet access for Open-Meteo's geocoding and forecast APIs

The model name is set to `qwen3.5:4b` in `agent.py`.

## Setup

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:4b
```

Start Ollama if it is not already running:

```bash
ollama serve
```

Leave that process running and use another terminal for the assistant.

## Run

```bash
source .venv/bin/activate
python agent.py
```

Try questions such as:

```text
What's the weather in Kuala Lumpur today?
Will it rain in Penang tomorrow?
```

Type `exit` to quit. The assistant prints tool calls and results as it runs.

## How it works

- `agent.py` sends the conversation and `get_weather` tool definition to Ollama, runs any requested tool calls, and returns the model's answer.
- `weather_tool.py` finds the city through Open-Meteo's geocoding API and fetches a two-day forecast. Today's response also includes current temperature, humidity, conditions, and observation time.
- `requirements.txt` lists the Python dependencies: `ollama` and `requests`.

The tool accepts only `today` and `tomorrow`. City lookup uses the first geocoding result, so add a country to an ambiguous city name. Weather data comes from Open-Meteo; the application does not configure an API key.

## Troubleshooting

- If Ollama cannot be reached, check that `ollama serve` is running.
- If the model is unavailable, run `ollama pull qwen3.5:4b` or change `MODEL` in `agent.py` to a model you have installed.
- If a city is not found, try its full name and country.
