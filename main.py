import streamlit as st
from route import rl
from book_info_agent import get_book_info
from book_recommendation_agent import recommend_books
from small_talk_agent import small_talker
# from book_tracker import init_book_db, track_books, view_books
import time

# Giao diện Sidebar
st.sidebar.title("Book Companion Chatbot")

# Lưu lịch sử trò chuyện dạng list[dict]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Hiển thị lịch sử
def display_history(history):
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

display_history(st.session_state.chat_history)

# Hàm định tuyến
def router(query: str, history):
    print(">Router")
    route = rl(query)

    if route.name == 'small_talk':
        print("small talking")
        return small_talker(query, history)

    elif route.name == 'book_info':
        print("Fetching book information")
        return get_book_info(query, history)

    elif route.name == 'book_recommendation':
        print("Recommending books")
        return recommend_books(query, history)

    # elif route.name == 'book_tracker':
    #     print("Tracking books")
    #     response = track_books(query, history)
    #     books = view_books()
    #     if books:
    #         st.write("Danh sách sách của bạn:")
    #         st.dataframe(books)
    #     else:
    #         st.write("Chưa có sách nào được lưu.")
    else:
        return "Sorry, I don't have in it in my knowledge base. Can you try something else."

# Nhận input từ người dùng
user_input = st.chat_input("Aske me anything about books")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = router(user_input, st.session_state.chat_history)

    st.session_state.chat_history.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        full_res = ""
        holder = st.empty()
        if response and isinstance(response, str):
            for word in response.split():
                full_res += word + " "
                time.sleep(0.05)
                holder.markdown(full_res + "▋")
        holder.markdown(full_res)

# Xóa lịch sử
if st.sidebar.button("Clear Chat"):
    st.session_state.chat_history.clear()
