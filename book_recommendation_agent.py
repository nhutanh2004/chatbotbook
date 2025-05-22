import json
import re
import os
import requests
import google.generativeai as genai
import random
from dotenv import load_dotenv

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Gemini example prompt
examples = """
Example Input: "I want a book similar to 'Dune' by Frank Herbert."
Example Output: {"book_name": "Dune", "author_name": "Frank Herbert", "genre": null}

Example Input: "Recommend me a mystery book."
Example Output: {"book_name": null, "author_name": null, "genre": "Mystery"}

Example Input: "Can you suggest books by Agatha Christie?"
Example Output: {"book_name": null, "author_name": "Agatha Christie", "genre": null}
"""

def format_chat_history(chat_history):
    if not chat_history:
        return ""
    return "\n".join(
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in chat_history[-6:]
    )

def extract_book_info_gemini(user_input, chat_history=None):
    history_text = format_chat_history(chat_history)
    prompt = f"""
    You are an intelligent assistant for extracting book-related information.
    Respond only in JSON with keys: book_name, author_name, genre.
    If not found, set the field to null.

    Examples:
    {examples}

    Conversation history:
    {history_text}

    Current User Input: {user_input}
    Only return JSON:
    """
    response = model.generate_content(prompt)
    match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
    return json.loads(match.group(0)) if match else {"error": "No valid JSON found"}

def get_author_and_subject_from_book(book_name):
    """Lấy author và subjects từ Open Library thông qua work ID."""
    search_url = f"https://openlibrary.org/search.json?q={book_name}"
    try:
        response = requests.get(search_url, timeout=10)
        if response.status_code != 200:
            return None, []

        data = response.json()
        if data.get("numFound", 0) == 0:
            return None, []

        book_data = data["docs"][0]
        author = book_data.get("author_name", ["Unknown"])[0]
        work_key = book_data.get("key")  # e.g., "/works/OL45883W"

        if not work_key:
            return author, []

        work_id = work_key.split("/")[-1]
        detail_url = f"https://openlibrary.org/works/{work_id}.json"
        detail_response = requests.get(detail_url, timeout=10)

        if detail_response.status_code != 200:
            return author, []

        detail_data = detail_response.json()
        subjects = detail_data.get("subjects", [])[:5]  # Lấy tối đa 5 subject
        print("author and subject retrieved",author, subjects)
        return author, subjects

    except Exception as e:
        print(f"[ERROR] OpenLibrary: {e}")
        return None, []


def search_books_by_author(author_name):
    url = f"https://openlibrary.org/search.json?author={author_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    books = [
        {"title": doc["title"], "author": author_name}
        for doc in response.json().get("docs", [])
    ]
    return random.sample(books, min(10, len(books)))


import requests
import random

def search_books_by_subject(subject):
    """Tìm sách theo một chủ đề từ Open Library."""
    url = f"https://openlibrary.org/subjects/{subject.replace(' ', '_').lower()}.json"
    response = requests.get(url)

    if response.status_code != 200:
        return []  

    books = [
        {"title": book["title"], "author": book.get("authors", [{"name": "Unknown"}])[0]["name"]}
        for book in response.json().get("works", [])
    ]

    return random.sample(books, min(10, len(books)))  # Random tối đa 10 sách




def log_gemini_response(prompt, response_text):
    """Lưu prompt & phản hồi từ Gemini vào file JSON."""
    log_entry = {
        "prompt_sent": prompt,
        "response_received": response_text
    }
    
    # Ghi vào file JSON
    with open("gemini_log.json", "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False, indent=4)
        f.write(",\n")  # Dấu phẩy để phân biệt các bản ghi


def generate_final_response(book_info, recommendations, user_input, chat_history=None):
    prompt = f"""
    You are an expert in book recommendations.

    User input: "{user_input}"

    Chat history:
    {format_chat_history(chat_history)}

    Extracted info:
    {book_info}

    Recommended books:
    {json.dumps(recommendations, indent=2)}

    Write a friendly, helpful, and natural-sounding response with recommendations.
    Use line breaks between paragraphs for better readability.
    """
    response = model.generate_content(prompt)
    # log_gemini_response(prompt, response.text)
    return response.text.strip()

def recommend_books(user_input, chat_history=None):
    extracted_info = extract_book_info_gemini(user_input, chat_history)
    if "error" in extracted_info:
        return extracted_info["error"]

    book_name = extracted_info.get("book_name")
    author_name = extracted_info.get("author_name")
    genre = extracted_info.get("genre")
    all_recommendations = []

    if book_name:
        author_from_book, subjects = get_author_and_subject_from_book(book_name)
        if author_from_book:
            author_books = search_books_by_author(author_from_book)
            all_recommendations.extend(author_books)
        if subjects:
            for subject in subjects:
                subject_books = search_books_by_subject(subject)
                all_recommendations.extend(subject_books)

    elif author_name:
        all_recommendations.extend(search_books_by_author(author_name))
    elif genre:
        all_recommendations.extend(search_books_by_subject(genre))

    return generate_final_response(extracted_info, all_recommendations, user_input, chat_history)

if __name__ == "__main__":
    test_queries = [
        "Suggest books in the fantasy genre.",
        "Recommend books like 'The Hobbit'.",
        "Can you suggest a book by J.K. Rowling?",
        "I want to read something similar to The Great Gatsby by F. Scott Fitzgerald.",
        "I loved Pride and Prejudice, any similar books?",
    ]
    chat_history = []

    for query in test_queries:
        print(f"\n📝 User Query: {query}")
        response = recommend_books(query, chat_history)
        print(f"📚 Response: {response}")
