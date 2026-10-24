import uuid

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from weather_tool import (
    search_location,
    get_weather,
    compare_weather,
    get_forecast,
)

# ======================================
# 1. Configure the local language model
# ======================================

llm = ChatOllama(
    model="qwen3.5:4b",
    temperature = 0,
    reasoning = False, 
)

# ======================================
# 2. Define LangChain tools
# ======================================

@tool
def search_location_tool(query: str) -> dict:
    """Find matching cities or locations by name.

    Use this tool for location discovery or ambiguous place names.
    The result includes candidate cities, countries and coordinates.
    """
    return search_location(query)

@tool 
def get_weather_tool(city: str, day: str = "today") -> dict:
    """Get the daily weather forecast for today or tomorrow.

    Args:
        city: City name, optionally with country.
        day: Either 'today' or 'tomorrow'.
    """
    return get_weather(city, day)

@tool
def compare_weather_tool(
    city_a: str,
    city_b: str,
    day: str = "today"
) -> dict:
    """Compare daily weather in two cities.

    Args:
        city_a: First city.
        city_b: Second city.
        day: Either 'today' or 'tomorrow'.
    """
    return compare_weather(city_a, city_b, day)

@tool
def get_forecast_tool(
    city: str,
    days: int = 7
) -> dict:
    """Get a daily weather forecast for 1 to 16 days.

    Args:
        city: City name, optionally with country.
        days: Number of forecast days, from 1 to 16.
    """
    return get_forecast(city, days)

tools = [
    search_location_tool,
    get_weather_tool,
    compare_weather_tool,
    get_forecast_tool,
]

# ======================================
# 3. Set agent instructions
# ======================================

SYSTEM_PROMPT = """
You are a helpful AI weather assistant.

You have four weather tools:
- search_location_tool
- get_weather_tool
- compare_weather_tool
- get_forecast_tool

Rules:
1. Always use a tool to answer real weather questions.
2. Never invent temperature or precipitation data.
3. Remember cities and dates from earlier messages.
4. Use compare_weather_tool to compare two cities.
5. Use get_forecast_tool for multi-day forecasts.
6. Use search_location_tool for ambiguous places or
   requests to find locations.
7. If the user says "What about tomorrow?", use the
   previous city unless a different city was specified.
8. For missing or ambiguous location information,
   ask a clarification question rather than guessing.
9. The tools provide daily forecast values, not live
   current temperature measurements.
10. Be concise and explain the result clearly.
"""

# ======================================
# 4. Configure conversation memory
# ======================================

checkpointer = InMemorySaver()

# ======================================
# 5. Create the LangChain agent
# ======================================

agent = create_agent(
    model=llm, 
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# ======================================
# 6. Create a session
# ======================================

thread_id = str(uuid.uuid4())

def ask_agent(question: str):
    """Send a question to the LangChain agent."""

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 20,
    }

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config = config
    )

    return result

def show_tool_calss(result):
    """Display tool calls recorded in the conversation."""

    for message in result["messages"]:
        if message.type == "ai" and message.tool_calls:
            for call in message.tool_calls:
                print(f"[Tool call] {call['name']}")
                print(f"[Arguments] {call['args']}")

        if message.type == "tool":
            print(f"[Tool result] {str(message.content)[:300]}")

# ======================================
# 7. Interactive terminal
# ======================================

def main():
    global thread_id

    print("=== LangChain Weather Agent ===")
    print("Model: Qwen3 4B via Ollama")
    print("Commands: /reset, /memory, /exit\n")

    while True:
        print("======================================")
        print(f"[Thread ID] {thread_id}")
        question = input("You: ").strip()

        if question.lower() == "/exit":
            print("Exiting...")
            break

        if question.lower() == "/reset":
            thread_id = str(uuid.uuid4())
            print("[Memory] Conversation reset. \n")
            continue

        if question.lower() == "/memory":
            state = agent.get_state({
                "configurable": {"thread_id": thread_id}
            })
            messages = state.values.get("messages", [])

            print(f"[Memory] {len(messages)} messages in conversation:")
            for msg in messages:
                print(f"- {msg.type}: {str(msg.content)[:100]}")
            print()
            continue

        if not question:
            print("[Error] Please enter a question or command.\n")
            continue

        try:
            result = ask_agent(question)

            answer = result["messages"][-1].content
            print(f"\nAgent: {answer}\n")

            # Uncomment to inspect the agent's tool history.
            # show_tool_calls(result)

        except Exception as exc:
            print(f"[Error] {exc}\n")

if __name__ == "__main__":
    main()
