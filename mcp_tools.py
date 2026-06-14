import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

mcp=FastMCP(name="MCP Tools")
@mcp.tool()
async def fetch_Wikipedia(search_query: str) -> str:
    """Fetches a representative image URL for a topic from Wikipedia."""
    async with httpx.AsyncClient() as client:
        common_headers = {"User-Agent": "AutonomousNewsBot/1.0 (admin@local.test)"}
        search_params = {
            "action": "query", "list": "search",
            "srsearch": search_query, "srlimit": 1,
            "format": "json", "utf8": "1"
        }
        try:
            search = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params=search_params, headers=common_headers, timeout=10.0
            )
            if search.status_code != 200:
                return ""
            
            results = search.json().get("query", {}).get("search", [])
            if not results:
                return ""
            
            page_title = results[0]["title"]
            image_params = {
                "action": "query", "titles": page_title,
                "prop": "pageimages", "pithumbsize": 800,
                "format": "json", "utf8": "1"
            }
            img_response = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params=image_params, headers=common_headers, timeout=10.0
            )
            if img_response.status_code == 200:
                pages = img_response.json().get("query", {}).get("pages", {})
                for _, page_data in pages.items():
                    thumb = page_data.get("thumbnail", {})
                    url   = thumb.get("source", "")
                    if url:
                        print(f"Wikipedia image found for '{page_title}': {url}")
                        return url
        except Exception as e:
            print(f"Wikipedia error: {e}")
    return ""

@mcp.tool()
async def fetch_pexel(search_query: str) -> str:
    """Fetches a stock photo URL from Pexels."""
    pexels_key = os.getenv("PEXELS_API_KEY")
    if not pexels_key:
        print("Pexels: No API key found in environment")
        return ""
    async with httpx.AsyncClient() as client:
        try:
            search = await client.get(
                "https://api.pexels.com/v1/search",
                params={"query": search_query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": pexels_key},
                timeout=10.0
            )
            if search.status_code == 200:
                data   = search.json()
                photos = data.get("photos", [])
                if photos:
                    url = photos[0]["src"]["landscape"]
                    print(f"Pexels found for '{search_query}': {url}")
                    return url
                else:
                    print(f"Pexels: no photos found for '{search_query}'")
            else:
                print(f"Pexels: status {search.status_code}")
        except Exception as e:
            print(f"Pexels Error: {e}")
    return ""
if __name__ == "__main__":
    mcp.run(transport="stdio")


