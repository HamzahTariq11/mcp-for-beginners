import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()



os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
model=ChatGroq(model="qwen-qwq-32b")

async def main():    
    client = MultiServerMCPClient({
        "playwright": {        #remove whole playwright object if running server locally only
            "transport": "stdio",
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "mcp/playwright"
            ]
        },
        "user_name":{
                "url": "http://localhost:8000/mcp",  # Ensure server is running here
                "transport": "streamable_http",  #remove whole user_name object if running docker only
            }
    })   #keep both objects if running server locally and through docker

    tools = await client.get_tools()

    agent = create_react_agent(model=model, tools=tools)

    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Can you navigate to www.google.com? and tell me all the elements on the page"}]}, #for playwright
    )
    # response = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "What is my name?"}]}, #for local server
    # )
    # response = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "My age is 25. What is my birth year?"}]},
    # )
    print(response['messages'][-1].content)
    

asyncio.run(main())
