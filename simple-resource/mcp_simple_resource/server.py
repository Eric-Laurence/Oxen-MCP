import anyio
import click
import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.types import Tool, ToolDefinition
from openai import OpenAI
from oxen import DataFrame


load_dotenv()


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
@click.option(
    "--repo", 
    default="username/repository", 
    help="Oxen repository in format username/repository"
)
@click.option(
    "--dataframe", 
    default="data.parquet", 
    help="Dataframe file path in the repository"
)
def main(port: int, transport: str, repo: str, dataframe: str) -> int:
    app = Server("oxen-embedding-search")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment variables")
    
    openai_client = OpenAI(api_key=openai_api_key)
    
    # Initialize Oxen DataFrame
    try:
        df = DataFrame(repo, dataframe)
        # Enable nearest neighbors if not already enabled
        df.enable_nearest_neighbors(column="embedding")
    except Exception as e:
        print(f"Error initializing Oxen DataFrame: {e}")
        df = None

    @app.list_tools()
    async def list_tools() -> List[ToolDefinition]:
        # Define the embedding similarity search tool
        return [
            ToolDefinition(
                name="oxen_embedding_search",
                description="Searches for similar content in an Oxen dataframe based on semantic similarity to the provided query. Converts query to an embedding using OpenAI and performs nearest neighbors search.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to embed and find similar content for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, args: Dict[str, Any]) -> Any:
        if name != "oxen_embedding_search":
            raise ValueError(f"Unknown tool: {name}")
        
        if df is None:
            return {
                "error": "Oxen DataFrame not properly initialized",
                "message": "Check the repository and dataframe path, and make sure embeddings are configured correctly."
            }
        
        query = args.get("query")
        limit = args.get("limit", 5)
        
        if not query:
            return {"error": "Missing required parameter: query"}
        
        try:
            # Generate embedding for the query using OpenAI
            response = openai_client.embeddings.create(
                input=query,
                model="text-embedding-3-large"
            )
            
            # Search the Oxen dataframe
            results = df.query(
                find_embedding_where={"text": query},
                sort_by_similarity_to="embedding",
                page_size=limit
            )
            
            # Format the results
            formatted_results = []
            for _, row in results.iterrows():
                formatted_results.append({
                    "text": row.get("text", ""),
                    "similarity": float(row.get("similarity", 0)) if "similarity" in row else None
                })
            
            return {
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results)
            }
            
        except Exception as e:
            return {
                "error": f"Error performing similarity search: {str(e)}",
                "query": query
            }

    # Server transport handling
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0
