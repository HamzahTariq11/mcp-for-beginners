from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter
from langchain_groq import ChatGroq
from mcp import StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv()  

from pathlib import Path

current_dir = os.getcwd()  # Get current working directory
host_pdf_dir = Path(current_dir, "saved_pdfs").as_posix()


# Azure OpenAI configuration
os.environ["AZURE_OPENAI_TYPE"] = "azure"
os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ.get("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_API_BASE"] = os.environ.get("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_VERSION"] = os.environ.get("AZURE_OPENAI_VERSION")
os.environ["OPENAI_API_VERSION"] = os.environ.get("OPENAI_API_VERSION")
os.environ["AZURE_OPENAI_API_KEY"] = os.environ.get("AZURE_OPENAI_API_KEY")


# you can use models from groq too but there might be issues with rate limits on free tier

server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output",  # this is where it saves the files
        "mcp/playwright"
    ]
)

# Alternatively, for Streamable HTTP server:
# server_params = {
#     "url": "http://localhost:8000/mcp",
#     "transport": "streamable-http"
# }

async def main():
    with MCPServerAdapter(server_params) as mcp_tools:
        print(f"Available tools: {[tool.name for tool in mcp_tools]}")
        llm = LLM(
            model="azure/gpt-4o",
            temperature=0.7
        )
        # Create agent with MCP tools
        agent = Agent(
            role="Agent",
            goal="Use browser tools to fetch content",
            backstory="An expert agent that can interact with web using MCP tools.",
            tools=mcp_tools,  # Pass the tools from MCPServerAdapter
            llm=llm,
            verbose=True,
        )

        # Define task
        task = Task(
            description="Navigate to www.google.com and fetch the title of the page. Also save the page as google.pdf'.",
            agent=agent,
            expected_output="A string containing the title of the Google homepage, e.g., 'Google'. and filepath to the pdf file, e.g., 'google.pdf'.",
        )

        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        # Run crew
        result = crew.kickoff()
        print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())