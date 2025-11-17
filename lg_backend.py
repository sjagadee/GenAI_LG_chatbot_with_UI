from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1-nano")

# state definition

# base message is the parent of all message types, hence it is used to add any type of messages
# add_messages is optimized version of operator.add to add messages (while using reducer function)
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # call llm to get response
    response = llm.invoke(messages)

    # add response to state
    return {'messages': [response]}

# define checkpointer for memory
checkpointer = MemorySaver()

# define state graph
graph = StateGraph(ChatState)

# add nodes to the graph
graph.add_node('chat_node', chat_node)

# add edges to the graph
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

# compile the graph
chatbot = graph.compile(checkpointer=checkpointer)
