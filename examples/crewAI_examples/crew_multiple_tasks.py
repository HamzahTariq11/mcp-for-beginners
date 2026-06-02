from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter
from langchain_groq import ChatGroq
from mcp import StdioServerParameters

import os
from dotenv import load_dotenv

load_dotenv()  

from pathlib import Path

current_dir = os.getcwd()  # Get current working directory
current_dir = os.path.join(current_dir,"crewAI_examples")  
host_pdf_dir = Path(current_dir, "saved_pdfs").as_posix()


# Azure OpenAI configuration
os.environ["AZURE_OPENAI_TYPE"] = "azure"
os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ.get("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_API_BASE"] = os.environ.get("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_VERSION"] = os.environ.get("AZURE_OPENAI_VERSION")
os.environ["OPENAI_API_VERSION"] = os.environ.get("OPENAI_API_VERSION")
os.environ["AZURE_OPENAI_API_KEY"] = (
    os.environ.get("AZURE_OPENAI_API_KEY")
)

server_params_list=[
    StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output",  # this is where it saves the files
        "mcp/playwright"
    ]
)
,
{
    "url":"http://localhost:8000/mcp", #MCP for time
    "transport":"streamable-http"
},
{
    "url": "http://localhost:5000/mcp",  #MCP for user details
    "transport": "streamable-http"
}
]


async def main():
    with MCPServerAdapter(server_params_list) as all_tools:
        print(f"Total tools loaded: {[tool.name for tool in all_tools]}")

        llm = LLM(model="azure/gpt-4o", temperature=0.7)

        agent = Agent(
            role="Agent",
            goal="Use browser tools to fetch content",
            backstory="An expert agent that can interact with web using MCP tools.",
            tools=all_tools,
            llm=llm,
            verbose=True,
        )

        task = Task(
            description="Navigate to www.bing.com and fetch the title. Use the tools to get name and birth year (my age is 25) and also the current time. Fill them on the text box and hit enter and save it as google.pdf.",
            agent=agent,
            expected_output="Page title, the text that was input the search box and saved PDF path",
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())