# watch_advisor_simple.py
import os
import streamlit as st
import google.generativeai as genai

# -------------------------
# Simple configuration
# -------------------------
st.set_page_config(
    page_title="Gemini Watch Collection Advisor (Simple)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Read API key from environment or Streamlit secrets
GOOGLE_API_KEY = (
    st.secrets["GOOGLE_API_KEY"]
    if "GOOGLE_API_KEY" in st.secrets
    else os.getenv("GOOGLE_API_KEY")
)

if not GOOGLE_API_KEY:
    st.error(
        "Missing Google API key. Add it to Streamlit secrets (recommended) or set the "
        "environment variable GOOGLE_API_KEY."
    )
    st.stop()

# Configure the google.generativeai library
# NOTE: genai.configure() is the usual pattern for this library.
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Failed to configure google.generativeai: {e}")
    st.stop()

# -------------------------
# Sidebar: Filters (kept as-is)
# -------------------------
st.sidebar.title("⌚ Filter Watch Collection")
st.sidebar.markdown("---")

gender_options = ["Any", "Men's", "Ladies'", "Unisex"]
price_ranges = [
    "Any",
    "$0 - $1,000 (Entry)",
    "$1,000 - $5,000 (Mid-Range)",
    "$5,000 - $15,000 (Luxury)",
    "$15,000+ (High-End)",
]
case_sizes = [
    "Any",
    "34mm or less (Small)",
    "35mm - 38mm (Classic)",
    "39mm - 42mm (Modern)",
    "43mm+ (Oversized)",
]
watch_types = [
    "Any",
    "Diver",
    "GMT/Travel Time",
    "Dress Watch",
    "Chronograph",
    "Everyday (GADA)",
    "Field Watch",
    "Pilot/Aviation",
]
movement_types = [
    "Any",
    "Automatic (Self-Winding)",
    "Manual Wind (Mechanical)",
    "Quartz",
    "Spring Drive (Hybrid)",
]

selected_gender = st.sidebar.selectbox("Gender", gender_options)
selected_price = st.sidebar.selectbox("Price Range", price_ranges)
selected_size = st.sidebar.selectbox("Case Size (Diameter)", case_sizes)
selected_type = st.sidebar.selectbox("Watch Type/Complication", watch_types)
selected_movement = st.sidebar.selectbox("Movement Type", movement_types)

st.sidebar.markdown("---")
st.sidebar.caption("The AI will use these filters to refine its advice.")

# -------------------------
# System prompt and helpers
# -------------------------
filter_context = (
    f"Gender preference: {selected_gender}.\n"
    f"Desired Price Range: {selected_price}.\n"
    f"Preferred Case Size: {selected_size}.\n"
    f"Watch Type/Complication: {selected_type}.\n"
    f"Movement Type: {selected_movement}.\n"
)

SYSTEM_PROMPT = (
    "You are a world-class, discerning watch collection advisor. Your expertise covers "
    "both vintage and modern luxury timepieces, spanning all price points and complexities. "
    "Provide objective, insightful, and knowledgeable advice based on the user's filters. "
    "Highlight brand heritage, long-term value retention, movement quality, and current market trends. "
    "Suggest specific models and brands that fit the user's criteria.\n\n"
    "Current applied watch criteria:\n"
    f"{filter_context}"
)

# -------------------------
# Session state: chat history and initialization
# -------------------------
if "messages" not in st.session_state:
    # messages will be a list of dicts: {"role": "system/user/assistant", "content": "..."}
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Add a friendly assistant greeting
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your Watch Collection Advisor. Use the sidebar filters to set preferences, "
                "then ask me for recommendations or market insights."
            ),
        }
    )

# Update the system prompt in session state if filters changed (so subsequent replies use latest filters)
# We keep a dedicated system entry at messages[0]
st.session_state.messages[0] = {"role": "system", "content": SYSTEM_PROMPT}

# -------------------------
# Helper: call Gemini (simple, non-streaming)
# -------------------------
def call_gemini(messages, model_name="gemini-2.5-flash"):
    """
    messages: list of {"role": "system/user/assistant", "content": str}
    Returns: assistant reply string
    """
    # Build a single prompt by joining the messages in chat format
    # This approach ensures the model sees the conversation (memory is handled locally).
    prompt_parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        # simple role tokens to make conversation clearer to the model
        prompt_parts.append(f"{role.upper()}:\n{content}\n")

    prompt = "\n".join(prompt_parts) + "\nASSISTANT:\n"

    try:
        # NOTE: different versions of google.generativeai may expose different function names.
        # The common pattern is something like genai.generate_text() or genai.generate(). If your
        # installed package uses a different function, replace the call below accordingly.
        #
        # This example uses `genai.generate_text` (replace if necessary).
        response = genai.generate_text(
            model=model_name,
            input=prompt,
            max_output_tokens=800,
            temperature=0.2,
        )
        # Many versions return .text or .output[0].content -- try resilient extraction:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        if hasattr(response, "output") and response.output:
            # if output is a list of content dicts
            first = response.output[0]
            if isinstance(first, dict) and "content" in first:
                return first["content"].strip()
            if isinstance(first, str):
                return first.strip()

        # fallback: string representation
        return str(response).strip()
    except Exception as e:
        # Return a friendly error message to show in chat
        return f"Error calling Gemini model: {e}"

# -------------------------
# UI: chat display and input
# -------------------------
st.title("🗣️ Chat with the Watch Collection Advisor (Simple)")

# Render messages
for msg in st.session_state.messages:
    if msg["role"] == "system":
        # don't display system messages to the user
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
user_prompt = st.chat_input("Ask a question about your perfect watch...")

if user_prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Call Gemini (non-streaming)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        # Call the model with the full conversation (memory preserved in messages)
        assistant_reply = call_gemini(st.session_state.messages, model_name="gemini-2.5-flash")

        # Show the response
        placeholder.markdown(assistant_reply)

    # Save assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# -------------------------
# Footer: quick tips
# -------------------------
st.markdown("---")
st.caption(
    "Notes: This simplified app keeps conversation memory inside Streamlit session state "
    "and sends the entire conversation to the Gemini model each time. "
    "Do NOT paste production API keys into source files; use Streamlit secrets or environment variables."
)
