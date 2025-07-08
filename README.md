# 🚀 MCP Tools Setup Guide for Beginners

This guide outlines the steps to set up and run a project using MCP tools, either with Docker or a local server.

---

## 📋 Prerequisites

- **Python** 3.12 or higher  
- **Docker** (if using the Docker setup)  
- **Git** (optional, for cloning the repository)  

---

## 🛠️ Setup Instructions

### 1️⃣ Install `uv`

> Follow the instructions at  
> [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

---

### 2️⃣ Initialize the Project

**Create a new directory:**
````bash
mkdir my-mcp-project
cd my-mcp-project
````

**Initialize a new uv project:**
````bash
uv init
````

**Create a virtual environment:**
````bash
uv venv
````

**Sync the project dependencies:**
````bash
uv sync
````

---

### 3️⃣ Add Packages

To add additional Python packages to your project, use the following command:
````bash
uv add <package-name>
````

For example:
````bash
uv add langchain
````

---

## 🚀 Running MCP Tools

This repository supports running MCP tools either via Docker or a local server. You can choose one method or use both, depending on your needs.

### Option 1: Using Docker for MCP Server

To run the MCP server using Docker, follow these steps:

**Pull the Playwright Docker image:**
````bash
docker pull mcp/playwright
````

**Run the Docker container:**
````bash
docker run -i --rm mcp/playwright
````

> **Note:** The exact command may vary depending on the image. Check the documentation for available images at [Docker Hub - MCP Images](https://hub.docker.com/search?categories=Machine+learning+%26+AI).

Keep the terminal running to maintain the container.

---

### Option 2: Using a Local Server

To run the MCP server locally, follow these steps:

**Add tools to the server** based on your use case. Currently, the server includes two tools that return a string.

**Run the server:**
````bash
python user.py
````

Keep the terminal running to maintain the server.

---

## 🎭 Running the Agent

Once the MCP server (Docker or local) is running, execute the main script to use your agent with MCP tools:
````bash
python main.py
````

---

## 📝 Notes

- Ensure the server (Docker or local) is running before executing `main.py`.
- If you encounter issues with Docker images, refer to the official documentation for troubleshooting.
- To manage dependencies or remove unused packages, edit the `uv.toml` file and run:
````bash
uv sync
````


