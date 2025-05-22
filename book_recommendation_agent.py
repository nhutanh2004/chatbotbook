import json
import re
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Example interactions for Gemini prompt
examples = """
Example Input: "I want a book similar to 'Dune' by Frank Herbert."
Example Output: {"book_name": "Dune", "author_name": "Frank Herbert", "genre": "Science Fiction"}

Example Input: "Recommend me a mystery book."
Example Output: {"book_name": null, "author_name": null, "genre": "Mystery"}

Example Input: "Can you suggest books by Agatha Christie?"
Example Output: {"book_name": null, "author_name": "Agatha Christie", "genre": null}
"""

def format_chat_history(chat_history):
    """Format conversation history as context for Gemini."""
    if not chat_history:
        return ""

    history_text = ""
    for msg in chat_history[-6:]:  # Limit to last 6 messages
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    return history_text

def extract_book_info_gemini(user_input: str, chat_history=None):
    """Extract book title, author, and genre using Gemini."""
    history_text = format_chat_history(chat_history) if chat_history else ""

    prompt = f"""
    You are an intelligent assistant for extracting book-related information.
    Given a user's input, determine:
    - Book title (if mentioned)
    - Author (if mentioned)
    - Genre (if mentioned)

    Respond **only** in JSON format:
    {{"book_name": "...", "author_name": "...", "genre": "..."}}
    If a field is unknown, set it to null.

    Here are example cases:
    {examples}

    Conversation history:
    {history_text}

    Current User Input: {user_input}
    Only return JSON:
    """
    
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Extract JSON response
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {"error": "No valid JSON found"}

def search_books_by_author(author_name):
    """Find books by author using Open Library."""
    url = f"https://openlibrary.org/search.json?author={author_name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        books = [
            {"title": book["title"], "author": author_name}
            for book in data.get("docs", [])[:10]  # Return up to 10 books
        ]
        return books if books else "No books found for this author."
    
    return "No books found for this author in Open Library."

def search_open_library_by_genre(genre):
    """Find books by genre using Open Library."""
    genre = genre.replace(" ","_").lower()
    url = f"https://openlibrary.org/subjects/{genre}.json?details=false"
    print(url)
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        books = [
            {"title": book["title"], "author": book.get("authors", [{"name": "Unknown"}])[0]["name"]}
            for book in data.get("works", [])[:10]  # Return up to 10 books
        ]
        return books if books else "No books found for this genre."
    
    return "No books found for this genre in Open Library."

def generate_final_response(book_info, recommendations, user_input, chat_history=None):
    """Generate a final response using Gemini for better conversational flow."""
    history_text = format_chat_history(chat_history) if chat_history else ""

    prompt = f"""
    You are an expert in book recommendations assisting users in a conversation.

    User asked: "{user_input}"

    Here is the previous conversation:
    {history_text}

    Based on the extracted book information:
    {book_info}

    Here are recommended books:
    {recommendations}

    Provide an engaging, helpful, and friendly response, incorporating book recommendations naturally.
    """
    
    response = model.generate_content(prompt)
    return response.text.strip()

def recommend_books(user_input: str, chat_history=None):
    """Recommend books using Gemini and Open Library."""
    extracted_info = extract_book_info_gemini(user_input, chat_history)

    if "error" in extracted_info:
        return extracted_info["error"]

    book_name = extracted_info.get("book_name")
    author_name = extracted_info.get("author_name")
    genre = extracted_info.get("genre")

    recommendations = None

    if author_name:
        recommendations = search_books_by_author(author_name)
    elif genre:
        recommendations = search_open_library_by_genre(genre)
    
    return generate_final_response(extracted_info, recommendations, user_input, chat_history)

if __name__ == "__main__":
    # Sample test queries
    test_queries = [
        # "Recommend books similar to 'The Hobbit' by J.R.R. Tolkien.",
        "Suggest books in the fantasy genre.",
        # "Find books written by Agatha Christie.",
        # "Recommend science fiction books.",
        # "What are some mystery novels?",
    ]

    # Simulating an empty chat history (can be replaced with previous interactions)
    chat_history = []

    # Run the test cases
    for query in test_queries:
        print(f"\n📝 **User Query:** {query}")
        response = recommend_books(query, chat_history)
        print(f"📚 **Response:** {response}")
