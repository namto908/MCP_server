from typing import Any
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase, basic_auth # Import GraphDatabase and basic_auth

load_dotenv() # Load environment variables from .env file

# Initialize FastMCP server
mcp = FastMCP("mcp_server")

# Constants
USER_AGENT = "mcp_server-app/1.0"

# Neo4j Connection Details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Initialize Neo4j Driver
neo4j_driver = None
try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    # Verify connection
    with neo4j_driver.session() as session:
        session.run("RETURN 1")
    print("Successfully connected to Neo4j.")
except Exception as e:
    print(f"Failed to connect to Neo4j: {e}")
    neo4j_driver = None # Ensure driver is None if connection fails

# PostgreSQL Connection Details
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

# Initialize PostgreSQL Connection
postgres_conn = None
try:
    import psycopg
    conn_string = f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
    postgres_conn = psycopg.connect(conn_string)
    print("Successfully connected to PostgreSQL.")
except Exception as e:
    print(f"Failed to connect to PostgreSQL: {e}")
    postgres_conn = None

# Milvus Connection Details
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_USER = os.getenv("MILVUS_USER", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")

# Initialize Milvus Connection
milvus_connected = False
try:
    from pymilvus import connections
    connections.connect(
        "default",
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user=MILVUS_USER,
        password=MILVUS_PASSWORD
    )
    print("Successfully connected to Milvus.")
    milvus_connected = True
except Exception as e:
    print(f"Failed to connect to Milvus: {e}")


@mcp.tool()
async def get_github_user_info() -> str:
    """Get information about the authenticated GitHub user.

    Requires a GitHub Personal Access Token (PAT) set as an environment variable named GITHUB_TOKEN.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return "Error: GITHUB_TOKEN environment variable not set."

    headers = {
        "Authorization": f"token {github_token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }
    github_api_url = "https://api.github.com/user"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(github_api_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            user_info = response.json()
            return f"GitHub User Info:\nLogin: {user_info.get('login')}\nName: {user_info.get('name')}\nPublic Repos: {user_info.get('public_repos')}\nFollowers: {user_info.get('followers')}"
        except httpx.HTTPStatusError as e:
            return f"Error fetching GitHub user info: HTTP Status {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

@mcp.tool()
async def get_github_repos() -> str:
    """Get a list of repositories for the authenticated GitHub user.

    Requires a GitHub Personal Access Token (PAT) set as an environment variable named GITHUB_TOKEN.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return "Error: GITHUB_TOKEN environment variable not set."

    headers = {
        "Authorization": f"token {github_token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }
    github_api_url = "https://api.github.com/user/repos"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(github_api_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            repos = response.json()

            if not repos:
                return "No repositories found for this user."

            repo_list = []
            for repo in repos:
                repo_list.append(f"- {repo.get('name')} ({repo.get('html_url')})\n  Description: {repo.get('description', 'No description')}\n  Private: {repo.get('private')}\n  Fork: {repo.get('fork')}")
            return "\n\n".join(repo_list)
        except httpx.HTTPStatusError as e:
            return f"Error fetching GitHub repositories: HTTP Status {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

@mcp.tool()
async def run_neo4j_query(query: str) -> str:
    """Run a Cypher query against the Neo4j database.

    Requires NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables to be set.
    """
    if not neo4j_driver:
        return "Error: Neo4j driver not initialized. Check Neo4j connection details."

    try:
        with neo4j_driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]
            if not records:
                return "Query executed successfully, but no results returned."
            return str(records) # Convert list of dicts to string for output
    except Exception as e:
        return f"Error executing Neo4j query: {e}"

@mcp.tool()
async def run_postgres_query(query: str) -> str:
    """Run a SQL query against the PostgreSQL database.

    Requires POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB environment variables to be set.
    """
    if not postgres_conn:
        return "Error: PostgreSQL connection not initialized. Check PostgreSQL connection details."

    try:
        with postgres_conn.cursor() as cur:
            cur.execute(query)
            if cur.description:
                records = cur.fetchall()
                if not records:
                    return "Query executed successfully, but no results returned."
                return str(records)
            else:
                postgres_conn.commit()
                return "Query executed successfully with no return value."
    except Exception as e:
        return f"Error executing PostgreSQL query: {e}"

@mcp.tool()
async def list_milvus_collections() -> str:
    """List all collections in the Milvus database."""
    if not milvus_connected:
        return "Error: Milvus connection not initialized. Check Milvus connection details."

    try:
        from pymilvus import utility
        collections = utility.list_collections()
        if not collections:
            return "No collections found in Milvus."
        return f"Milvus Collections:\n- {"\n- ".join(collections)}"
    except Exception as e:
        return f"Error listing Milvus collections: {e}"

@mcp.tool()
async def search_milvus_collection(
    collection_name: str,
    query_vector: list[float],
    top_k: int,
    output_fields: list[str] | None = None,
    filter_expression: str | None = None
) -> str:
    """Search for similar vectors in a Milvus collection.

    Args:
        collection_name: The name of the collection to search in.
        query_vector: The query vector for similarity search.
        top_k: The number of most similar results to return.
        output_fields: Optional list of fields to include in the output.
        filter_expression: Optional expression to filter results before searching.
    """
    if not milvus_connected:
        return "Error: Milvus connection not initialized. Check Milvus connection details."

    try:
        from pymilvus import Collection
        collection = Collection(collection_name)
        collection.load()

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        results = collection.search(
            data=[query_vector],
            anns_field="embedding",  # Assuming the vector field is named 'embedding'
            param=search_params,
            limit=top_k,
            expr=filter_expression,
            output_fields=output_fields
        )

        collection.release()
        return str(results)
    except Exception as e:
        return f"Error searching Milvus collection: {e}"

if __name__ == "__main__":
    # Initialize and run the server in HTTP mode
    mcp.run(transport='http', host='0.0.0.0', port=2409)