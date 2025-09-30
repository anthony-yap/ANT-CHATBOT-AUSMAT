import os
import streamlit as st
import google.generativeai as genai

# -------------------------
# Page configuration
# -------------------------
st.set_page_config(
    page_title="Gemini Watch Collection Advisor (Simple)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# API Key Setup
# -------------------------
GOOGLE_API_KEY = (
    st.secrets["GOOGLE_API_KEY"]
    if "GOOGLE_API_KEY" in st.secrets
    else os.getenv("GOOGLE_API_KEY")
)

if not GOOGLE_API_KEY:
    st.error("Missing Google API key. Add it in Streamlit secrets or env var.")
    st.stop()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Failed to configure google.generativeai: {e}")
    st.stop()

# -------------------------
# Sidebar Filters
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
# System Prompt Setup
# -------------------------
filter_context = (
    f"Gender preference: {selected_gender}.\n"
    f"Desired Price Range: {selected_price}.\n"
    f"Preferred Case Size: {selected_size}.\n"
    f"Watch Type/Complication: {selected_type}.\n"
    f"Movement Type: {selected_movement}.\n"
)

SYSTEM_PROMPT = (
    "You are a world-class, discerning watch collection advisor. "
    "Provide objective insights based on the user's filters. "
    "Speak in **neutral, educational, historical terms**. "
    "Do not offer financial or investment advice. "
    "You may describe **historical resale value trends** using phrases such as "
    "'commonly known to hold value' or 'often sought after by collectors', "
    "but avoid speculative or predictive language.\n\n"
    "Current applied watch criteria:\n"
    f"{filter_context}"
)

# -------------------------
# Initialize chat memory
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "assistant",
            "content": "Hello! I'm your Watch Collection Advisor. Ask me anything about watches based on your filters.",
        },
    ]

st.session_state.messages[0]["content"] = SYSTEM_PROMPT

# -------------------------
# Gemini Call with Safe Rephrase
# -------------------------
def call_gemini(messages, model_name="gemini-2.5-flash"):
    def build_prompt(msgs):
        parts = []
        for m in msgs:
            parts.append(f"{m['role'].upper()}:\n{m['content']}\n")
        return "\n".join(parts) + "\nASSISTANT:\n"

    prompt = build_prompt(messages)

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        if response and response.candidates:
            candidate = response.candidates[0]
            if candidate.finish_reason == 1 and candidate.content.parts:
                return candidate.content.parts[0].text

            # Safety blocked → auto rephrase
            if candidate.finish_reason == 2:
                safe_prompt = (
                    "Rewrite the last user question in neutral historical or educational terms without speculation, "
                    "then answer based on historical watch trends only."
                )
                safe_response = model.generate_content(safe_prompt)
                if safe_response and safe_response.candidates:
                    return "⚠️ Some content was rephrased for safety:\n\n" + safe_response.candidates[0].content.parts[0].text

        return "⚠️ Gemini returned no response."

    except Exception as e:
        return f"Error calling Gemini model: {e}"

# -------------------------
# UI
# -------------------------
st.title("🗣️ Chat with the Watch Collection Advisor (Simple)")

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask a question about your perfect watch...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        reply = call_gemini(st.session_state.messages)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

st.markdown("---")
st.caption("Session memory is enabled. You can reset the page to restart.")
