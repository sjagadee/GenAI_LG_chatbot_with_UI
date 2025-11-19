import streamlit as st
from lg_backend_with_db import chatbot, get_threads
from langchain_core.messages import HumanMessage
from uuid import uuid4

# basically there are two major components in chatbot
# 1. Chat input
# 2. Chat messages - a list of messages

# *************** Utility functions ***************

def generate_thread_id():
    return str(uuid4())

def create_new_session():
    st.session_state.thread_id = generate_thread_id()
    add_thread(st.session_state.thread_id)
    st.session_state.message_history = []

def add_thread(thread_id):
    if thread_id not in st.session_state.session_threads:
        st.session_state.session_threads.append(thread_id)

def load_session(thread_id):
    st.session_state.thread_id = thread_id

    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})

    messages = state.values.get('messages', []) if state and hasattr(state, 'values') else []

    compatible_messages = []
    for message in messages:
        if isinstance(message, HumanMessage):
            compatible_messages.append({'role': 'user', 'content': message.content})
        else:
            compatible_messages.append({'role': 'assistant', 'content': message.content})

    st.session_state.message_history = compatible_messages

# *************** Session state - to store messages ***************

if 'message_history' not in st.session_state:
    st.session_state.message_history = []

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

if 'session_threads' not in st.session_state:
    st.session_state.session_threads = get_threads()

add_thread(st.session_state.thread_id)

CONFIG = {'configurable': {'thread_id': st.session_state.thread_id}}

# *************** Side bar ***************
st.sidebar.title('LangGraph Chatbot')

st.sidebar.button('New Chat', on_click=create_new_session)

st.sidebar.header('My Conversations')

for thread_id in st.session_state.session_threads[::-1]:
    # st.sidebar.button(thread_id, on_click=lambda: st.session_state.thread_id = thread_id)
    st.sidebar.button(thread_id, on_click=load_session, args=(thread_id,))

# *************** Chat messages section ***************

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