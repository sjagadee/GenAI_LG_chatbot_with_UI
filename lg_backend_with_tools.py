
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from typing import TypedDict, Annotated
from dotenv import load_dotenv
import sqlite3
import requests
import os

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1-nano")

# tools definition

search_tool = DuckDuckGoSearchRun()

@tool
def calculator(first: float, second: float, operator: str) -> dict:
    """
    Performs arithmetic operations of two numbers. 
    Supported operations: add, sub, mul, div
    """

    try:
        if operator == 'add':
            result = first + second
        elif operator == 'sub':
            result = first - second
        elif operator == 'mul':
            result = first * second
        elif operator == 'div':
            if second == 0:
                return {'error': 'Cannot divide by zero'}
            result = first / second
        else:
            return {'error': 'Invalid operator'}
        return {'first_number': first, 'second_number': second, 'operation': operator, 'result': result}
    except Exception as e:
        return {'error': str(e)}
    
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Returns the price of a stock. Uses AlphaVantage API to fetch the price.
    """
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
        response = requests.get(url)
        return {'symbol': symbol, 'price': response.json()}
    except Exception as e:
        return {'error': str(e)}

@tool
def get_weather(location: str) -> dict:
    """
    Returns the weather of a location. Uses Weatherstack API to fetch the weather.
    """
    url = f'https://api.weatherstack.com/current?access_key={os.getenv("WEATHER_API_KEY")}&query={location}'

    response = requests.get(url)

    return response.json()

# Make tool list
tools = [
    search_tool,
    calculator,
    get_stock_price,
    get_weather
]

# Make LLM tool aware
llm_with_tools = llm.bind_tools(tools)

# state definition

# base message is the parent of all message types, hence it is used to add any type of messages
# add_messages is optimized version of operator.add to add messages (while using reducer function)
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# node definition

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # call llm to get response
    response = llm_with_tools.invoke(messages)

    # add response to state
    return {'messages': [response]}

tool_node = ToolNode(tools)

# connect to sqlite database
conn = sqlite3.connect('langgraph.db', check_same_thread=False)

# define checkpointer for memory
checkpointer = SqliteSaver(conn=conn)

# define state graph
graph = StateGraph(ChatState)

# add nodes
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

# add edges
graph.add_edge(START, "chat_node")

# add conditional edges - if the tools are required then the flow goes to tool node else it goes to end
graph.add_conditional_edges("chat_node", tools_condition)

# add edges - tool node to chat node
graph.add_edge("tools", 'chat_node')

# compile the graph
chatbot = graph.compile(checkpointer=checkpointer)

# checkpointer list - to get all threads uniquely
def get_threads():
    global checkpointer
    unique_thread_ids = set()
    for check in checkpointer.list(None):
        unique_thread_ids.add(check.config['configurable']['thread_id'])

    return list(unique_thread_ids)
