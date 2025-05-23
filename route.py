# route.py

from semantic_router import Route, RouteLayer
from semantic_router.encoders import HuggingFaceEncoder

# 1. Định nghĩa các Route với utterance đa dạng hơn để bắt tốt hơn các câu hỏi thực tế
small_talk = Route(
    name="small_talk",
    utterances=[
        "Hey, how are you?",
        "Hello",
        "Hi there",
        "Good morning",
        "What's up?",
        "How’s your day?",
        "are there anything in your history",
        "I mean the history of your conversation",
        "How are you doing?",
        "Nice to meet you"
    ]
)

book_info = Route(
    name="book_info",
    utterances=[
        "Tell me about The Great Gatsby",
        "Who wrote To Kill a Mockingbird?",
        "What is the plot of 1984?",
        "Author of Harry Potter?",
        "Give me more suggestion",
        "When was Moby Dick published?",
        "What is Harry Potter about?",
        "Is Pride and Prejudice a romance novel?",
        "Give me details about War and Peace",
        "Summarize The Catcher in the Rye",
        "What genre is Dune?"
    ]
)   

book_recommendation = Route(
    name="book_recommendation",
    utterances=[
        "Can you recommend a sci-fi book?",
        "I like fantasy novels, any suggestions?",
        "Suggest a book like Harry Potter",
        "Which one of them focus on grow vegetables?"
        "What should I read next?",
        "Must-read mystery books?",
        "Give me a good fantasy recommendation",
        "I want to read something like 1984"
    ]
)

book_tracker = Route(
    name="book_tracker",
    utterances=[
        "Add 1984 to my reading list",
        "I finished Dune",
        "Mark The Hobbit as read",
        "Remove Dracula from my reading list",
        "Show books I’ve read",
        "What books are in my list?",
        "Track my reading progress"
    ]
)

# 2. Tập hợp các Route
routes = [small_talk, book_info, book_recommendation, book_tracker]

# 3. Khởi tạo bộ mã hóa và RouteLayer
encoder = HuggingFaceEncoder()
encoder.score_threshold = 0.3  # Có thể tinh chỉnh để kiểm soát độ nhạy

rl = RouteLayer(encoder=encoder, routes=routes)


