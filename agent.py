import json
from ollama import chat
from weather_tool import get_weather

MODEL = "qwen3.5:4b"

SYSTEM_PROMPT =  """
You are a friendly AI weather assistant.

Rules:
- Use get_weather whenever the user requests real weather data.
- The tool supports today and tomorrow only.
- Never invent weather measurements.
- If a city is missing, ask the user for the city.
- If a request is beyond the tool's capabilities, explain the limit.
- Use only the retrieved data when reporting weather measurements.
- Give short, practical recommendations when appropriate.
"""

TOOLS = [get_weather]

AVAILABLE_COMMANDS = {
    "get_weather": get_weather,
}

def run_agent(user_message: str) -> str:
    """
    Run the weather agent with the given user message.

    Args:
        user_message (str): The user's message.

    Returns:
        str: The agent's response.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for _ in range(4):
        response = chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            # max_tokens=500,
            # temperature=0.7,
            think=False
        )

        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content or "I'm sorry, I couldn't generate a response."

        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            print(f"[Agent] Calling tool: {tool_name} with args: {tool_args}")


            if tool_name not in AVAILABLE_COMMANDS:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = AVAILABLE_COMMANDS[tool_name](**tool_args)
                except Exception as e:
                    result = {"error": str(e)}

            print(f"[Tool] Tool {tool_name} returned: {result}")

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(result),
            })

    return "The agent reached its tool-call limit. Please try again."

def main():
    print("Welcome to the Weather Agent!")
    print("You can ask for the weather in a city for today or tomorrow.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input.strip():
            print("Please enter a valid message.")
            continue

        try: 
            answer = run_agent(user_input)
            print(f"Agent: {answer}\n")
        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    main()


        

    # response = chat(
    #     model=MODEL,
    #     messages=messages,
    #     tools=TOOLS,
    #     max_tokens=500,
    #     temperature=0.7,
    # )

    # return response["content"]
