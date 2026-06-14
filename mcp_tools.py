import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

mcp=FastMCP(name="MCP Tools")
@mcp.tool()

async def fetch_Wikipedia(search_query:str)->str:
    async with httpx.AsyncClient() as client:
        common_url="https://commons.wikimedia.org/w/api.php"
        common_headers={"User-Agent": "AutonomousNewsBot/1.0 (admin@local.test)"}

        # Namespace 6 is explicitly reserved for "Files"(Images, Videos, Audio)
        # iiprop : Image Info Properties if url is specified then it retrieves only the url
        # "utf8": "1" handles character encoding for the JSON output format.
        search_params={
            "action":"query","generator":"search","gsrsearch":search_query,"gsrnamespace":6,"gsrlimit":4,"prop":"imageinfo","iiprop":"url","format":"json","utf8":"1"
        }
        try:
            search=await client.get(common_url,params=search_params,headers=common_headers,timeout=10.0)
            if search.status_code==200:
                data=search.json()
                pages=data.get("query",{}).get("pages",{})
                for _,page_info in pages.items():
                    if "imageinfo" in page_info and len(page_info["imageinfo"])>0:
                        return page_info["imageinfo"][0]["url"]
        except Exception as e:
            print(f"Wikipedia error:{e}")
    return ""

@mcp.tool()
async def fetch_pexel(search_query:str)->str:
    pexels_key=os.getenv("PEXELS_API_KEY")
    if not pexels_key:
        return ""
    async with httpx.AsyncClient() as client:
        try:
            p_url="https://api.pexels.com/v1/search"
            p_params = {"query": search_query, "per_page": 1, "orientation": "landscape"}
            p_headers = {"Authorization": pexels_key}

            search=await client.get(p_url, params=p_params, headers=p_headers, timeout=10.0)
            if search.status_code==200:
                data=search.json()
                if data.get("photos"):
                    return data["photos"][0]["src"]["landscape"]
        except Exception as e:
            print(f"Pexels Error:{e}")
    return ""

if __name__ == "__main__":
    mcp.run(transport="stdio")


