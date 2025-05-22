import json
import requests
import re
import time
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

# Cấu hình Gemini API
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Các ví dụ mẫu
examples = """
Example Input: "Tell me about Harry Potter by J.K. Rowling."
Example Output: {"book_name": "Harry Potter", "author_name": "J.K. Rowling", "genre": "Fiction"}

Example Input: "What is the genre of The Catcher in the Rye?"
Example Output: {"book_name":"The Catcher in the Rye" , "author_name": null, "genre": null}

Example Input: "Who wrote The Hobbit"
Example Output: {"book_name": "The Hobbit", "author_name": null, "genre": null}
"""

def format_chat_history(chat_history):
    """Chuyển đổi lịch sử chat từ Streamlit sang định dạng văn bản"""
    if not chat_history:
        return ""
    
    history_text = ""
    for msg in chat_history[-6:]:  # Lấy 6 tin nhắn gần nhất (khoảng 3 lượt hội thoại)
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    return history_text

def extract_book_info_gemini(user_input: str, chat_history=None):
    """Trích xuất thông tin sách bằng Gemini, có xem xét lịch sử trò chuyện"""
    history_text = format_chat_history(chat_history) if chat_history else ""
    
    prompt = f"""
    You are an intelligent assistant that extracts book-related information from user queries.
    Consider this conversation history for context:
    {history_text}

    Respond only with a single line of JSON like this:
    {{"book_name": "...", "author_name": "...", "genre": "..."}}
    If a field is unknown, use null.

    {examples}

    Current User Input: {user_input}
    Only return JSON:
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Chỉ lấy phần JSON đầu tiên nếu có
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"error": "No valid JSON found"}
    except Exception as e:
        return {"error": f"Gemini error: {str(e)}"}

def search_open_library(book_name):
    """Tìm kiếm thông tin sách trên Open Library"""
    search_url = f"https://openlibrary.org/search.json?q={book_name}"
    try:
        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["numFound"] > 0:
                book_data = data["docs"][0]
                work_key = book_data.get("key")
                
                if work_key:
                    work_id = work_key.split("/")[-1]
                    detail_url = f"https://openlibrary.org/works/{work_id}.json"
                    detail_response = requests.get(detail_url, timeout=10)
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        description = (
                            detail_data.get("description", {}).get("value")
                            if isinstance(detail_data.get("description"), dict)
                            else detail_data.get("description", "No description")
                        )
                        
                        return {
                            "title": book_data.get("title", "Unknown"),
                            "author": book_data.get("author_name", ["Unknown"])[0],
                            "publish_year": book_data.get("first_publish_year", "Unknown"),
                            "description": description,
                            "subjects": detail_data.get("subjects", []),
                            "subject_places": detail_data.get("subject_places", []),
                            "subject_times": detail_data.get("subject_times", []),
                        }
        return {"error": "Can not find infomation on Open Library"}
    except Exception as e:
        return {"error": f"Lỗi Open Library: {str(e)}"}

def search_wikipedia(book_name):
    """Tìm kiếm thông tin sách trên Wikipedia"""
    try:
        params = {
            "format": "json",
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "redirects": 1,
            "titles": book_name
        }
        response = requests.get("https://en.wikipedia.org/w/api.php", params=params, timeout=10)
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "extract" in page:
                return page["extract"][:1000]  # Giới hạn độ dài
        return {"error": "No infomation found on Wikipedia"}
    except Exception as e:
        return {"error": f"Wikipedia error: {str(e)}"}

def generate_final_response(book_info, wiki_data, library_data, user_input, chat_history=None):
    """Tạo phản hồi cuối cùng với ngữ cảnh hội thoại"""
    history_text = format_chat_history(chat_history) if chat_history else ""
    
    prompt = f"""
        You are an expert in books helping users in a conversation.

        User asked: "{user_input}"

        Here is the previous conversation:
        {history_text}

        Use only the following information to answer:

        Wikipedia Summary:
        {wiki_data}

        Open Library Details:
        {library_data}

        Be helpful, concise, and conversational if needed.
        If there is no information available be honest and say you don't know.
        """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Errol when finding book infomation: {str(e)}"

def get_book_info(query, chat_history=None):
    """Xử lý truy vấn sách với ngữ cảnh hội thoại"""
    # Trích xuất thông tin sách với ngữ cảnh
    extracted_info = extract_book_info_gemini(query, chat_history)
    
    if "error" in extracted_info:
        return extracted_info["error"]
    
    book_name = extracted_info.get("book_name")
    author_name = extracted_info.get("author_name")    
    if not book_name and author_name:
        wiki_result = search_wikipedia(author_name)
        if "error" in wiki_result:
            return f"I couldn't find information about {author_name}. Would you like book recommendations instead?"
        return generate_final_response(
            extracted_info,
            wiki_result,  # Author info from Wikipedia
            None,  # Không cần Open Library ở đây
            query,
            chat_history
        )  
    # Tìm kiếm song song
    with ThreadPoolExecutor() as executor:
        future_wiki = executor.submit(search_wikipedia, book_name)
        future_lib = executor.submit(search_open_library, book_name)
        wiki_result = future_wiki.result()
        lib_result = future_lib.result()
    
    # Tạo phản hồi cuối cùng
    return generate_final_response(
        extracted_info,
        wiki_result,
        lib_result,
        query,
        chat_history
    )

# Ví dụ sử dụng
if __name__ == "__main__":
    query = "Tell me about The Great Gatsby characters."
    start_time = time.time()
    result = get_book_info(query)
    end_time = time.time()

    print("\n📘 Response:")
    print(result)
    print(f"\n⏱ Execution Time: {end_time - start_time:.2f} seconds")