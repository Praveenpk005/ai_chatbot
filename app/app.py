import os

import streamlit as st
from google import genai
from google.genai import types


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Gemini Chatbot",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Praveen's AI Chatbot")
st.caption("A simple chatbot that remembers messages during this browser session.")

MODEL_NAME = "gemini-3.5-flash-lite"
MAX_OUTPUT_TOKENS = 1000


# -----------------------------
# API key and Gemini client
# -----------------------------
def get_api_key():
    """Read the API key from Streamlit secrets or an environment variable."""
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except (FileNotFoundError, KeyError):
        key = None

    return key or os.getenv("GEMINI_API_KEY")


api_key = get_api_key()

if not api_key:
    st.error(
        "Gemini API key not found. Add GEMINI_API_KEY to "
        "`.streamlit/secrets.toml` or set it as an environment variable."
    )
    st.code('GEMINI_API_KEY = "AQ.Ab8RN6JdNLmC8Pf5usKkWudhYYkQ0_qyWNp33ZRW3eyXZKPZUQ"', language="toml")
    st.stop()

try:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000),
    )
except Exception as exc:
    st.error(f"Could not initialize the Gemini client: {exc}")
    st.stop()


# -----------------------------
# Session state
# -----------------------------
if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# Chat function
# -----------------------------
def chat(user_message: str) -> str:
    """Send the conversation to Gemini and return its reply."""
    updated_conversation = st.session_state.conversation + [
        {
            "role": "user",
            "parts": [{"text": user_message}],
        }
    ]

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=updated_conversation,
        config=types.GenerateContentConfig(
            max_output_tokens=MAX_OUTPUT_TOKENS
        ),
    )

    reply = response.text
    if not reply:
        raise RuntimeError("Gemini returned an empty response.")

    # Commit both messages only after a successful response.
    st.session_state.conversation = updated_conversation + [
        {
            "role": "model",
            "parts": [{"text": reply}],
        }
    ]

    return reply


# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.subheader("Chat controls")
    st.caption(f"Model: `{MODEL_NAME}`")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.conversation = []
        st.session_state.messages = []
        st.rerun()

    st.info(
        "Conversation history is kept in Streamlit session state. "
        "It is not permanent storage and may be lost when the session resets."
    )

# -----------------------------
# Display previous messages
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# Chat input
# -----------------------------
user_prompt = st.chat_input("Ask Gemini something...")

if user_prompt:
    # Show the user's message immediately.
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
            try:
                reply = chat(user_prompt)
                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
            except Exception as exc:
                st.error(f"Gemini request failed: {type(exc).__name__}: {exc}")
                st.caption(
                    "Your message is visible above, but it was not added "
                    "to the saved conversation history because the request failed."
                )
