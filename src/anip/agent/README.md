# Pydantic AI Agents

This directory contains intelligent agents built with [Pydantic AI](https://ai.pydantic.dev/) for various tasks in the ANIP system.

## News Agent

The **News Agent** is an intelligent assistant that can search for news articles using multiple sources:

1. **DuckDuckGo Search** - External web search for breaking news and real-time information
2. **Internal Database Search** - Semantic search over analyzed articles with ML predictions

### Features

- 🔍 **Semantic Search**: Uses embeddings for intelligent similarity matching
- 🎯 **Multi-Source**: Combines external and internal sources
- 📊 **ML Insights**: Access to topic classification and sentiment analysis
- 🤖 **Intent Understanding**: Automatically chooses the right tools based on query
- 📈 **Database Stats**: Can analyze what's available in the database

### Agent Architecture

Following Pydantic AI patterns:

```python
from anip.agent import search_news

# Simple usage
result = await search_news("artificial intelligence news", max_results=5)

print(result.summary)  # AI-generated summary
print(result.articles)  # List of relevant articles
print(result.sources_used)  # Which sources were queried
```

### Tools Available

1. **`search_duckduckgo`**
   - External web search
   - Best for: Breaking news, real-time events
   - Returns: Title, URL, snippet, source

2. **`search_news_database`**
   - Semantic search using embeddings
   - Best for: Analyzed content, topic/sentiment filtering
   - Returns: Full article metadata with relevance scores

3. **`search_news_database_text`**
   - Text-based keyword search
   - Best for: Fallback when semantic search unavailable
   - Returns: Articles matching keywords

4. **`get_database_stats`**
   - Database statistics and distribution
   - Best for: Understanding available data
   - Returns: Counts, topics, sentiments, date ranges

### Usage Examples

#### Example 1: General News Search

```python
from anip.agent import search_news

result = await search_news(
    "climate change latest developments",
    max_results=5,
    search_provider="both"  # Use both DuckDuckGo and database
)

print(f"Summary: {result.summary}")
print(f"Found {result.total_results} articles")

for article in result.articles:
    print(f"- {article.title}")
    print(f"  Source: {article.source}")
    print(f"  Sentiment: {article.sentiment}")
```

#### Example 2: Database-Only Search with Filters

```python
from anip.agent import news_agent, NewsAgentDependencies

deps = NewsAgentDependencies(
    user_query="AI innovations",
    max_results=3,
    search_provider="database"
)

result = await news_agent.run(
    "Find positive technology news about AI",
    deps=deps
)

print(result.output.summary)
```

#### Example 3: With Custom Tools

```python
from anip.agent import news_agent
from pydantic_ai import RunContext

@news_agent.tool
async def check_breaking_news(ctx: RunContext) -> dict:
    """Custom tool to check if query is about breaking news."""
    # Your custom logic
    return {"is_breaking": True, "category": "technology"}

result = await news_agent.run("Latest tech news", deps=deps)
```

### Dependencies

The agent uses `NewsAgentDependencies` for dependency injection:

```python
@dataclass
class NewsAgentDependencies:
    user_query: str          # User's original query
    max_results: int = 5     # Max results per tool
    search_provider: str = "duckduckgo"  # Preferred provider
```

### Output Structure

The agent returns `NewsAgentOutput`:

```python
class NewsAgentOutput(BaseModel):
    summary: str                      # AI-generated summary
    articles: List[NewsSearchResult]  # Found articles
    sources_used: List[str]           # Sources queried
    query_intent: str                 # Interpreted intent
    total_results: int                # Total count
```

Each article is a `NewsSearchResult`:

```python
class NewsSearchResult(BaseModel):
    title: str
    url: str
    snippet: Optional[str]
    source: Optional[str]
    published_at: Optional[str]
    topic: Optional[str]              # ML prediction
    sentiment: Optional[str]          # ML prediction
    relevance_score: Optional[float]  # Similarity score (0-1)
```

### Running the Agent

#### As a Script

```bash
# Run the example usage
python -m anip.agent.news_agent

# Or with uv
uv run python -m anip.agent.news_agent
```

#### In Your Code

```python
import asyncio
from anip.agent import search_news

async def main():
    result = await search_news(
        "machine learning breakthroughs 2024",
        max_results=5
    )
    
    print(result.summary)
    for article in result.articles:
        print(f"- {article.title} ({article.source})")

asyncio.run(main())
```

### Integration with Pydantic Logfire

Monitor your agent in real-time:

```python
import logfire
from anip.agent import news_agent

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()

# Agent calls will now be logged to Logfire
result = await news_agent.run("AI news", deps=deps)
```

### Model Configuration

The agent uses `openai:gpt-4o` by default, but you can change it:

```python
from anip.agent import news_agent

# Change model for a specific run
result = await news_agent.run(
    "your query",
    deps=deps,
    model="anthropic:claude-3-5-sonnet-20241022"
)
```

### Best Practices

1. **Choose the Right Tool**:
   - Use DuckDuckGo for breaking news
   - Use database search for analyzed content
   - Let the agent decide when using "both"

2. **Leverage ML Predictions**:
   - Filter by topic when you know the category
   - Use sentiment filtering for opinion analysis

3. **Handle Errors Gracefully**:
   - Tools return error dictionaries on failure
   - Agent will try alternative approaches

4. **Monitor Performance**:
   - Use Pydantic Logfire for observability
   - Track tool usage and response times

## Adding New Agents

To add a new agent:

1. Create a new file in this directory (e.g., `summary_agent.py`)
2. Define dependencies and output models
3. Create the agent with tools
4. Export from `__init__.py`
5. Add documentation here

Example structure:

```python
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

@dataclass
class YourDependencies:
    # Your dependencies
    pass

class YourOutput(BaseModel):
    # Your output structure
    pass

your_agent = Agent(
    'openai:gpt-4o',
    deps_type=YourDependencies,
    output_type=YourOutput,
    instructions="Your instructions"
)

@your_agent.tool
async def your_tool(ctx: RunContext[YourDependencies]) -> dict:
    """Your tool implementation."""
    pass
```

## Dependencies

Make sure you have the required packages:

```bash
uv add pydantic-ai httpx numpy
```

## References

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Pydantic AI Tools & Toolsets](https://ai.pydantic.dev/tools/)
- [Pydantic Logfire](https://docs.pydantic.dev/logfire/)

