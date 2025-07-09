from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta

mcp = FastMCP("Time Tools")



@mcp.tool()
async def get_current_time() -> str:
    """Return the current time in HH:MM:SS format."""
    return datetime.now().strftime("%H:%M:%S")

@mcp.tool()
async def get_time_after_minutes(minutes: int) -> str:
    """Return the time after a given number of minutes from now."""
    new_time = datetime.now() + timedelta(minutes=minutes)
    return new_time.strftime("%H:%M:%S")





if __name__ == "__main__":
    mcp.run(transport="streamable-http")