# 🚀 MCP With LangGraph and CrewAI - A Beginners Guide with Examples

This repository demonstrates how to use MCP tools with both **LangGraph** and **Crew AI**. 

---

## 📋 Prerequisites

- **Python** 3.12 or higher  
- **Docker** (for Docker-based MCP server)  
- **Git** (optional, for cloning the repository)  

---

## 🛠️ Setup Instructions

### 1. Install `uv`

See [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Initialize the Project

```bash
mkdir my-mcp-project
cd my-mcp-project
uv init
uv venv
.\.venv\Scripts\activate
uv sync
```
**Note**: 
### (Optional) Add further packages according to your requirements

```bash
uv add <package-name>
# Example:
uv add langgraph
```

---

# 🧩 LangGraph Example

This section covers the original example using LangGraph and MCP tools.

## Running MCP Tools

You can run MCP tools via Docker or a local server.

### Option 1: Docker

```bash
docker pull mcp/playwright
docker run -i --rm mcp/playwright
```

Keep the terminal running to maintain the container.

### Option 2: Local Server

Add tools to the server as needed.  
Run:

```bash
python .\server\user.py
```

---

## Running the Agent

Once the MCP server (Docker or local) is running, execute:

```bash
python .\langgraph_examples\client.py
```

---

## Notes

- Ensure the server (Docker or local) is running before executing `client.py`.
- To manage dependencies or remove unused packages, edit `pyproject.toml` and run `uv sync`.

---

# 🤖 Crew AI Examples

This section demonstrates how to use Crew AI with MCP tools. All outputs (like PDFs) are saved in the `saved_pdfs` directory.

---

### Note: You can use groq models instead of azure openai, but there might be issues with rate limits on free tier.

---

## 1. Single MCP Example

**File:** `crew.py`

**Run:**
```bash
python .\crewAI_examples\crew.py
```
**Note**: Make sure the MCP servers are running.

**What it does:**  
- Connects to MCP tools via Docker (or optionally HTTP).
- Uses Crew AI to create an agent that:
  - Navigates to www.google.com
  - Fetches the page title
  - Saves the page as `google.pdf` in the `saved_pdfs` directory

**Key snippet:**
```python
server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output", 
        "mcp/playwright"
    ]
)
```

The argument "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output" mounts the local host directory to the Docker container for sharing PDF output files. Remove it if you do not require access to the directory of the container.

---

## 2. Multiple MCPs Example (User & Time Servers)

**File:** `crew_multiple_tasks.py`

### About the Local Servers

You can create a separate MCP server (e.g., `time.py`) with tools related to time.


You can then connect to both `user.py` (user tools) and `time.py` (time tools) in your Crew AI workflow.

**Run in different terminals:**
```bash
python .\server\time.py
```
```bash
python .\server\user.py 
```
**Execute the Client:**
---
```bash
python .\crewAI_examples\crew_multiple_tasks.py
```

---

**What it does:**  
- Connects to multiple MCP servers:
  - **User server** (e.g., `user.py`): provides user-related tools (like getting your name, calculating birth year, etc.)
  - **Time server** (e.g., `time_server.py`): provides time-related tools (like current time, time after X minutes, time difference, etc.)
  - **Playwright** Docker-based MCP tools (e.g., browser automation)
- Merges tools from all sources
- Uses Crew AI to create an agent that:
  - Navigates to www.bing.com
  - Fetches the page title
  - Gets your name from the user MCP server
  - Uses time functions from the time MCP server (e.g., gets current time, calculates time difference)
  - Puts the name or time in a text box
  - Saves the page as `bing.pdf` in the `saved_pdfs` directory



**Example code for loading multiple MCP servers:**
```python
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

docker_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output",
        "mcp/playwright"
    ]
)
#both servers running on different port
user = {
    "url": "http://localhost:8000/mcp",
    "transport": "streamable-http"
}

time = {
    "url": "http://localhost:5000/mcp",
    "transport": "streamable-http"
}

from contextlib import ExitStack

def load_all_mcp_tools(server_params_list):
    all_tools = []
    stack = ExitStack()
    adapters = [stack.enter_context(MCPServerAdapter(params)) for params in server_params_list]
    for adapter in adapters:
        all_tools.extend(adapter)
    return all_tools, stack

server_params_list = [docker_params, user, time]   #add or remove servers from this list
all_tools, stack = load_all_mcp_tools(server_params_list)
with stack:
    # Use all_tools in your Crew AI agent
    ...
```

This lets your Crew AI agent access and use tools from all connected MCP servers in a single workflow.

---

**Note:**  
- All output files (like PDFs) are saved in the `saved_pdfs` directory.
- Make sure the required environment variables are set (see `.env.example` if available).
- For Azure OpenAI, ensure your credentials are configured as shown in the code.

---