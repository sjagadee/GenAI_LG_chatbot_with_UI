import streamlit as st
from lg_backend import chatbot
from langchain_core.messages import HumanMessage

# basically there are two major components in chatbot
# 1. Chat input
# 2. Chat messages - a list of messages

CONFIG = {'configurable': {'thread_id': 'thread-1'}}

st.title('LangGraph Chatbot')

if 'message_history' not in st.session_state:
    st.session_state.message_history = []

for message in st.session_state.message_history:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Enter your message')

if user_input:

    st.session_state.message_history.append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):

        ai_response = st.write_stream(
            # getting the stream response in chunks making it easier to read
            # like typewriter effect
            message_chunk.content for message_chunk, _ in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state.message_history.append({'role': 'assistant', 'content': ai_response})