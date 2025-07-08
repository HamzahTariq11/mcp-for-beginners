from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("User Name")

@mcp.tool()
async def get_my_name() -> str:
    """Get the user name."""
    return "My name is Hamzah Tariq"

@mcp.tool()
async def get_my_birthyear(age: int) -> str:
    """Get the user birthyear."""
    current_year = datetime.now().year
    birthyear = current_year - age
    return f"Your birth year is {birthyear}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")