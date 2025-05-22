import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def format_chat_history(chat_history):
    """Format conversation history as context for the Gemini model."""
    if not chat_history:
        return ""
    
    history_text = ""
    for msg in chat_history[-6:]:  # Limiting to last 6 messages
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    return history_text

def small_talker(input_text: str, chat_history=None) -> str:
    """Process user input and generate responses using Gemini AI."""
    history_text = format_chat_history(chat_history) if chat_history else ""
    
    prompt = f"""
    You are an AI assistant engaged in casual conversation. Respond naturally and conversationally.
    
    Previous conversation history:
    {history_text}

    User Input:
    {input_text}

    Generate a thoughtful and engaging response:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response else "I'm not sure how to respond."
    except Exception as e:
        return f"Error generating response: {str(e)}"
