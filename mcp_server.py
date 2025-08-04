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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')