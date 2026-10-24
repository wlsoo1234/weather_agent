
import uuid
import streamlit as st

# Import the agent created in Lesson 4.
from langchain_agent import agent


# ====================================
# 1. Page configuration
# ====================================

st.set_page_config(
    page_title="AI Weather Assistant",
    page_icon="🌤️",
    layout="centered",
)


# ====================================
# 2. Initialize session state
# ====================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "show_tools" not in st.session_state:
    st.session_state.show_tools = True


# ====================================
# 3. Sidebar
# ====================================

with st.sidebar:
    st.title("🌤️ Weather Agent")

    st.write("**Language model:** Qwen3 4B")
    st.write("**Runtime:** Ollama")
    st.write("**Framework:** LangChain")

    st.divider()

    if st.button("🔄 New conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()

    st.checkbox(
        "Show tool execution",
        key="show_tools",
    )

    st.divider()

    st.subheader("Available tools")
    st.write("📍 Location search")
    st.write("🌡️ Daily weather")
    st.write("🔀 Weather comparison")
    st.write("📅 Extended forecasting")


# ====================================
# 4. Main chat interface
# ====================================

st.title("🌤️ AI Weather Assistant")
st.caption("Powered by Qwen3 · Ollama · LangChain")

st.write(
    "Ask about the weather, compare cities, "
    "or request an extended forecast."
)


# ====================================
# 5. Show previous messages
# ====================================

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and st.session_state.show_tools
            and message.get("tool_calls")
        ):
            with st.expander("🔧 Tool execution details"):
                for call in message["tool_calls"]:
                    st.write("**Tool:**", call["name"])
                    st.json(call["args"])


# ====================================
# 6. Accept new user messages
# ====================================

prompt = st.chat_input(
    "Ask me about the weather..."
)

if prompt:

    # Save and display the user's message.
    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the LangChain agent.
    with st.chat_message("assistant"):

        with st.spinner("Checking the weather..."):

            try:
                config = {
                    "configurable": {
                        "thread_id": st.session_state.thread_id
                    },
                    "recursion_limit": 20,
                }

                # Count previous agent messages.
                previous_state = agent.get_state(config)
                previous_messages = previous_state.values.get(
                    "messages", []
                )
                previous_count = len(previous_messages)

                # Run the agent.
                result = agent.invoke(
                    {
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    config=config,
                )

                answer = result["messages"][-1].content

                if not isinstance(answer, str):
                    answer = str(answer)

                # Only inspect messages from this turn.
                new_messages = result["messages"][previous_count:]

                tool_calls = []

                for msg in new_messages:
                    if msg.type == "ai":
                        for call in (msg.tool_calls or []):
                            tool_calls.append({
                                "name": call["name"],
                                "args": call["args"],
                            })

                st.markdown(answer)

                if st.session_state.show_tools and tool_calls:
                    with st.expander("🔧 Tool execution details"):
                        for call in tool_calls:
                            st.write("**Tool:**", call["name"])
                            st.json(call["args"])

                # Save the assistant response for display.
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_calls": tool_calls,
                })

            except Exception as exc:
                st.error(f"Agent error: {exc}")
                st.warning(
                    "Start a new conversation if the "
                    "previous request was interrupted."
                )
