# 🚀 MCP With Langgraph and CrewAI - A Beginners Guide with Examples

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

### 3. Add Packages

```bash
uv add <package-name>
# Example:
uv add langchain
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
python user.py
```

---

## Running the Agent

Once the MCP server (Docker or local) is running, execute:

```bash
python main.py
```

---

## Notes

- Ensure the server (Docker or local) is running before executing `main.py`.
- To manage dependencies or remove unused packages, edit `uv.toml` and run `uv sync`.

---

# 🤖 Crew AI Examples

This section demonstrates how to use Crew AI with MCP tools. All outputs (like PDFs) are saved in the `saved_pdfs` directory.

---
### Note: You can use groq models instead of azure openai, but there might be issues with rate limits on free tier.

## 1. Single MCP Example

**File:** `crew.py`

**Run:**
```bash
python crew.py
```

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

The argument "-v", f"{host_pdf_dir}:/tmp/playwright-mcp-output"  mounts the local host directory to the Docker container for sharing PDF output files. Remove it if you do not require access to the directory of the container.

---

## 2. Multiple MCPs Example

**File:** `crew_multiple_tasks.py`

**Run:**
```bash
python crew_multiple_tasks.py
```

**What it does:**  
- Connects to both Docker-based and local MCP servers
- Merges tools from both sources
- Uses Crew AI to create an agent that:
  - Navigates to www.google.com
  - Fetches the page title
  - Gets your name from a tool on mcp server running locally
  - Puts the name in a text box
  - Saves the page as `google.pdf` in the `saved_pdfs` directory

**Key snippet:**
```python
with MCPServerAdapter(docker_params) as docker_tools, MCPServerAdapter(http_params) as http_tools:
    all_tools = docker_tools + http_tools  # Merge tools
    # ...
```

---

**Note:**  
- All output files (like PDFs) are saved in the `saved_pdfs` directory.
- Make sure the required environment variables are set (see `.env.example` if available).
- For Azure OpenAI, ensure your credentials are configured as shown in
