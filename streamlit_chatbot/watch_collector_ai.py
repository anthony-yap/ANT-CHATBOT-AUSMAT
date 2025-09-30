import streamlit as st
import json
import time
from google import generativeai
from google.generativeai import types
from google.generativeai.errors import APIError

# --- Configuration and Initialization ---
# Set the page configuration for a wide, attractive layout
st.set_page_config(
    page_title="Gemini Watch Collection Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🚨 CRITICAL: Since the external API key setting is unavailable,
# you MUST paste your Gemini API Key directly into the quotes below
# for the app to initialize the client.
# Please ensure you have replaced the quotes with your actual key string.
GEMINI_API_KEY = "AIzaSyAJdpmCfjAxo0ADGVtNexMRq4RVOYMAFvA" # <-- PASTE YOUR API KEY HERE

# --- Helper Functions ---

# Function to safely retrieve the API client
def get_gemini_client():
    """Initializes and returns the Gemini client using the provided API key."""
    
    # Check if the key is still empty after the user was supposed to paste it
    if not GEMINI_API_KEY:
        # If the key is empty AND the environment failed to inject it, display an error
        st.error("Error initializing Gemini client. Please paste your API Key into the GEMINI_API_KEY variable on line 18 in the code editor.")
        st.stop()
        
    try:
        # Use the key provided in the variable
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        # This catches errors if the key is present but invalid/malformed
        st.error(f"Error initializing Gemini client: Check your key format. Details: {e}")
        st.stop()


# Function to handle API call with exponential backoff
def call_gemini_with_backoff(client, system_instruction, chat_history, user_query):
    """
    Calls the Gemini API with exponential backoff for resilience.
    Includes the system instruction, current chat history, and Google Search tool.
    """
    
    # Construct the full history for the API call
    full_history = []
    
    # Add previous messages from history
    for message in chat_history:
        role = "user" if message["role"] == "user" else "model"
        
        # FIX: Using direct dictionary structure for parts to avoid SDK function errors
        content_parts = [{"text": message["content"]}]
        full_history.append(types.Content(role=role, parts=content_parts))
    
    # Add the current user message
    user_content_parts = [{"text": user_query}]
    full_history.append(types.Content(role="user", parts=user_content_parts))

    # Define the request configuration
    config = types.GenerateContentConfig(
        # System instruction is defined outside the history and applied globally
        system_instruction=system_instruction,
        # Enable Google Search grounding
        tools=[{"google_search": {}}],
    )

    retries = 0
    max_retries = 5
    
    while retries < max_retries:
        try:
            # Using the client method to generate content
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=full_history,
                config=config
            )
            return response

        except APIError as e:
            # Handle rate limiting (status code 429)
            if e.response.status_code == 429 and retries < max_retries - 1:
                wait_time = 2 ** retries
                time.sleep(wait_time)
                retries += 1
            else:
                raise e
        except Exception as e:
            # Handle other exceptions
            raise e

    raise APIError("Maximum retries reached for API call.")

# --- UI Components and Logic ---

def main():
    # 1. Initialize Gemini Client
    client = get_gemini_client()

    # 2. Sidebar Filters
    st.sidebar.title("⌚ Filter Watch Collection")
    st.sidebar.markdown("---")

    # Define filter options
    gender_options = ["Any", "Men's", "Ladies'", "Unisex"]
    price_ranges = ["Any", "$0 - $1,000 (Entry)", "$1,000 - $5,000 (Mid-Range)", "$5,000 - $15,000 (Luxury)", "$15,000+ (High-End)"]
    case_sizes = ["Any", "34mm or less (Small)", "35mm - 38mm (Classic)", "39mm - 42mm (Modern)", "43mm+ (Oversized)"]
    watch_types = ["Any", "Diver", "GMT/Travel Time", "Dress Watch", "Chronograph", "Everyday (GADA)", "Field Watch", "Pilot/Aviation"]
    movement_types = ["Any", "Automatic (Self-Winding)", "Manual Wind (Mechanical)", "Quartz", "Spring Drive (Hybrid)"]

    # Selectbox for Gender
    selected_gender = st.sidebar.selectbox("Gender", gender_options)

    # Selectbox for Price Range
    selected_price = st.sidebar.selectbox("Price Range", price_ranges)

    # Selectbox for Case Size
    selected_size = st.sidebar.selectbox("Case Size (Diameter)", case_sizes)

    # Selectbox for Watch Type
    selected_type = st.sidebar.selectbox("Watch Type/Complication", watch_types)

    # Selectbox for Movement
    selected_movement = st.sidebar.selectbox("Movement Type", movement_types)
    
    st.sidebar.markdown("---")
    st.sidebar.caption("The AI will use these filters to refine its advice.")

    # 3. Dynamic System Instruction Generation
    filter_context = f"""
    Gender preference: {selected_gender}.
    Desired Price Range: {selected_price}.
    Preferred Case Size: {selected_size}.
    Watch Type/Complication: {selected_type}.
    Movement Type: {selected_movement}.
    """
    
    system_prompt = f"""
    You are a world-class, discerning watch collection advisor. Your expertise covers both vintage and modern luxury timepieces, spanning all price points and complexities. 
    You have access to current, real-time information via Google Search and MUST use it to ensure your recommendations are accurate and up-to-date.

    Your task is to provide objective, insightful, and knowledgeable advice based on the user's current filter criteria. 
    Always highlight factors like brand heritage, long-term value retention, movement quality, and current market trends (e.g., smaller cases are trending, independent brands are rising, complications are popular). 
    Suggest specific models and brands that fit the user's defined criteria.

    The current applied watch criteria are:
    {filter_context}
    """

    # 4. Main Chat Interface
    st.title("🗣️ Chat with the Watch Collection Advisor")
    st.markdown("Ask the AI about specific watches, brands, or market trends based on the filters you set in the sidebar.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting message
        st.session_state.messages.append({"role": "model", "content": "Hello! I am your Watch Collection Advisor. Use the sidebar filters to define your ideal timepiece, and then ask me for recommendations or advice on the market!"})

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("Ask a question about your perfect watch..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("model"):
            message_placeholder = st.empty()
            
            # Combine the current chat history for the prompt
            chat_history = st.session_state.messages[:-1] # Exclude the current user message

            try:
                # Call Gemini API
                response = call_gemini_with_backoff(
                    client=client,
                    system_instruction=system_prompt,
                    chat_history=chat_history,
                    user_query=prompt
                )
                
                full_response = response.text
                
                # Extract grounding sources if they exist
                sources_text = ""
                
                # --- FIX START: Robust check for grounding metadata ---
                grounding_metadata = response.candidates[0].grounding_metadata
                
                attributions = None
                # Try the known property name first
                if hasattr(grounding_metadata, 'grounding_attributions'):
                    attributions = grounding_metadata.grounding_attributions
                # Fallback check (might be needed for certain library versions/outputs)
                elif hasattr(grounding_metadata, 'groundingAttributions'):
                    attributions = grounding_metadata.groundingAttributions # Handle camelCase if present
                
                if attributions:
                    sources = []
                    for attr in attributions:
                        # Ensure both URI and Title exist for a valid source link
                        if attr.web and attr.web.uri and attr.web.title:
                            sources.append(f"[{attr.web.title}]({attr.web.uri})")
                    if sources:
                        sources_text = "\n\n---\n**Sources:** " + " | ".join(sources)
                # --- FIX END ---

                final_response = full_response + sources_text
                
                # Display the model's response
                message_placeholder.markdown(final_response)
                
                # Add model response to session state
                st.session_state.messages.append({"role": "model", "content": final_response})

            except APIError as e:
                error_message = f"**Error:** Could not connect to Gemini API. Check your API key and connection. Details: `{e}`"
                message_placeholder.error(error_message)
                st.session_state.messages.append({"role": "model", "content": error_message})
            except Exception as e:
                error_message = f"**An unexpected error occurred:** `{e}`"
                message_placeholder.error(error_message)
                st.session_state.messages.append({"role": "model", "content": error_message})


if __name__ == "__main__":
    main()
