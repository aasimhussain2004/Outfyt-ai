import streamlit as st
from tavily import TavilyClient

# Initialize Tavily Client
try:
    tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    tavily_client = None

def search_tavily(query):
    """
    Search for fashion items using Tavily API.
    Returns a list of dictionaries with title, url, and content.
    """
    if not tavily_client:
        return []
        
    try:
        # Search for shopping results specifically
        response = tavily_client.search(
            query=f"{query} buy online india fashion", 
            search_depth="basic",
            include_images=True,
            max_results=5
        )
        
        results = []
        # Process Images if available
        images = response.get("images", [])
        
        for i, res in enumerate(response.get("results", [])):
            img_url = images[i] if i < len(images) else ""
            results.append({
                "title": res.get("title", "Fashion Item"),
                "url": res.get("url", "#"),
                "image": img_url,
                "content": res.get("content", "")
            })
            
        return results
    except Exception as e:
        # print(f"Tavily Error: {e}")
        return []

def perform_search(query, max_results=3):
    """
    Executes a search and returns a formatted string for the LLM.
    """
    if not tavily_client:
        return None

    try:
        # General Search for Trends
        response = tavily_client.search(
            query=f"{query} latest fashion trends 2024", 
            search_depth="advanced",
            max_results=max_results
        )
        
        results_text = "### 🌐 Web Search Results:\n"
        for res in response.get("results", []):
            results_text += f"- **{res.get('title')}**: {res.get('content')} ({res.get('url')})\n"
            
        return results_text, response.get("results", [])
    except Exception as e:
        return f"Search Error: {e}", []
