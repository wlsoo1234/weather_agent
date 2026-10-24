import json
import re
from ollama import chat
from weather_tool import (
    search_location,
    get_weather,
    compare_weather,
    get_forecast,
)

MODEL = "qwen3.5:4b"

SYSTEM_PROMPT =  """
You are a helpful AI weather assistant with conversation memory.

Available tools:
- search_location: find possible matching locations.
- get_weather: get today's or tomorrow's daily weather.
- compare_weather: compare two cities for today or tomorrow.
- get_forecast: obtain a forecast for 1 to 16 days.

Instructions:
1. Use tools for real weather information. Never guess forecast data.
2. Prefer compare_weather when comparing two cities.
3. Prefer get_forecast for multi-day weather requests.
4. Use search_location when location discovery is requested
   or a location is ambiguous.
5. Remember cities and dates from previous conversation turns.
6. Ask for clarification if a location cannot be identified.
7. Today and tomorrow are relative to the selected city's
   local date.
8. The weather tools return daily values. Do not claim that
   daily high temperatures are current temperatures.
9. Use more than one tool when necessary to answer the request.
10. Explain differences clearly and briefly.
11. Use the exact dates and Celsius units returned by the tools. Do not add
    weekday names or Fahrenheit conversions unless the user requests them.
12. When comparing cities, include each city's forecast date; local dates
    can differ across time zones.
"""

TOOLS = [search_location, get_weather, compare_weather, get_forecast]

AVAILABLE_COMMANDS = {
    tool.__name__: tool for tool in TOOLS
}

def needs_answer_retry(content: str, done_reason: str | None) -> bool:
    """Catch empty replies and obvious sentence fragments from the model."""
    answer = content.strip()
    return (
        not answer
        or done_reason == "length"
        or answer.endswith((":", ","))
        or bool(re.search(r"\b(?:a|an|and|at|for|in|of|the|to|with)$", answer, re.I))
    )

def run_agent(user_message: str) -> str:
    """Run one request without retaining conversation memory."""
    return WeatherAgent().run(user_message)

class WeatherAgent:
    def __init__(self):
        self.tools = TOOLS
        self.available_commands = AVAILABLE_COMMANDS

        self.reset_memory()

    def reset_memory(self):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

    def show_memory(self):
        print("\n=== Conversation Memory ===")

        for i, message in enumerate(self.messages):
            if isinstance(message, dict):
                role = message.get("role", "unknown")
                content = message.get("content", "")
            else:
                role = message.role
                content = message.content or ""

            print(f"{i}. [{role}] {str(content)[:180]}")

        print("===========================\n")


    def run(self, user_message: str) -> str:

        self.messages.append({
            "role": "user",
            "content": user_message,
        })

        answer_retries = 0
        retrying_answer = False
        tool_results_this_turn = False

        # Maximum number of model/tool iterations, including answer retries.
        for round_number in range(6):

            response = chat(
                model=MODEL,
                messages=self.messages,
                tools=[] if retrying_answer else self.tools,
                think=False,
            )

            self.messages.append(response.message)

            tool_calls = response.message.tool_calls or []

            if not tool_calls:
                content = (response.message.content or "").strip()
                if needs_answer_retry(content, response.done_reason):
                    if answer_retries >= 2:
                        return "The model could not complete its answer. Please try again."
                    answer_retries += 1
                    retrying_answer = tool_results_this_turn
                    self.messages.append({
                        "role": "user",
                        "content": (
                            "Your last answer was empty or unfinished. Give one complete "
                            "answer to my request using the available tool results. "
                            "Do not invent weather data."
                        ),
                    })
                    continue
                return content

            retrying_answer = False
            tool_results_this_turn = True

            for call in tool_calls:
                name = call.function.name
                arguments = call.function.arguments

                print(
                    f"\n[Agent round {round_number + 1}] "
                    f"Selected tool: {name}"
                )
                print(f"[Arguments] {arguments}")

                function = self.available_commands.get(name)

                if function is None:
                    result = {
                        "error": f"Tool '{name}' is not available."
                    }
                else:
                    try:
                        result = function(**arguments)
                    except Exception as exc:
                        result = {
                            "error": f"Tool execution failed: {exc}"
                        }

                print(
                    "[Tool result] "
                    + json.dumps(result, ensure_ascii=False)[:1000]
                )

                # Save every tool result to conversation memory.
                self.messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(
                        result, ensure_ascii=False
                    ),
                })

        return (
            "I reached the maximum number of tool rounds. "
            "Please try a simpler request."
        )


def main():
    agent = WeatherAgent()

    print("=== Multi-Tool AI Weather Agent ===")
    print("Model:", MODEL)
    print("Tools:", ", ".join(agent.available_commands.keys()))
    print("\nCommands: /memory, /reset, /exit\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "/exit":
            break

        if user_input.lower() == "/reset":
            agent.reset_memory()
            print("[Memory cleared]")
            continue

        if user_input.lower() == "/memory":
            agent.show_memory()
            continue

        if not user_input:
            continue

        try:
            answer = agent.run(user_input)
            print(f"\nAssistant: {answer}\n")

        except Exception as exc:
            print(f"\nError: {exc}\n")
            agent.reset_memory()


if __name__ == "__main__":
    main()
