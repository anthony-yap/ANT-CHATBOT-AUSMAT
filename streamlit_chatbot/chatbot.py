import streamlit as st
import pandas as pd
import streamlit as st
import google.generativeai as genai

persona_instructions = """
You are a friendly, encouraging study buddy.
Use a cheerful tone, emojis are allowed.
Always offer helpful tips for learning.
"""


# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyAJdpmCfjAxo0ADGVtNexMRq4RVOYMAFvA"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

##Find the "get_gemini_response" function in your code and replace it with this function below

def get_gemini_response(prompt, persona_instructions):
    full_prompt = f"{persona_instructions}\n\nUser: {prompt}\nAssistant:"
    response = model.generate_content(full_prompt)
    return response.text

def main():
    st.title("Watch Hunter")
    
    initialize_session_state()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Chat with Gemini"):
    # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

    # Get Gemini response with persona
        response = get_gemini_response(prompt, persona_instructions)

    # Display assistant response
        with st.chat_message("assistant"):
            st.write(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    with st.sidebar:
        st.title("Filter") 
        st.multiselect("Multi-select", ["Everyday", "Diver", "GMT", "Dress"], default=["Everyday"])
        st.selectbox("Dropdown select", ["Data", "Code", "Travel", "Food", "Sports"], index=0)
        st.slider("Slider", min_value=1, max_value=200, value=60)
        st.select_slider("Option Slider", options=["Very Sad", "Sad", "Okay", "Happy", "Very Happy"], value="Okay")

   
   
if __name__ == "__main__":
    main()

