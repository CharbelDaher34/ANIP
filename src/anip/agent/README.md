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

### Agent Architecture

Following Pydantic AI patterns:

```python
from anip.agent import search_news

# Simple usage
result = await search_news("artificial intelligence news", max_results=5)

print(result.summary)  # AI-generated summary
print(result.answer)  # Comprehensive answer
print(result.duckduckgo_results)  # DuckDuckGo results
print(result.database_results)  # Database results
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
print(f"Answer: {result.answer}")
print(f"Found {result.total_results} articles")

# DuckDuckGo results
for article in result.duckduckgo_results:
    print(f"- {article.title} (DuckDuckGo)")
    print(f"  URL: {article.url}")

# Database results
for article in result.database_results:
    print(f"- {article.title} (Database)")
    print(f"  Source: {article.source}")
    print(f"  Sentiment: {article.sentiment}")
    print(f"  Relevance: {article.relevance_score}")
```

#### Example 2: Database-Only Search

```python
from anip.agent import search_news

result = await search_news(
    "machine learning innovations",
    max_results=3,
    search_provider="database"  # Only search internal database
)

print(f"Summary: {result.summary}")
print(f"Answer: {result.answer}")
print(f"Found {result.database_count} articles from database")

for article in result.database_results:
    print(f"- {article.title}")
    print(f"  Topic: {article.topic}")
    print(f"  Sentiment: {article.sentiment}")
    print(f"  Relevance: {article.relevance_score}")
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
    summary: str                                    # AI-generated summary
    answer: str                                     # Comprehensive answer synthesizing all results
    query_intent: str                              # Interpreted intent
    duckduckgo_results: List[NewsSearchResult]     # Results from DuckDuckGo search
    database_results: List[NewsSearchResult]        # Results from internal database search
    sources_used: List[str]                        # Sources queried
    total_results: int                              # Total count
    duckduckgo_count: int                          # Number of DuckDuckGo results
    database_count: int                             # Number of database results
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
    print(result.answer)
    
    # Process DuckDuckGo results
    for article in result.duckduckgo_results:
        print(f"- {article.title} (DuckDuckGo)")
    
    # Process database results
    for article in result.database_results:
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

## Dependencies

Make sure you have the required packages:

```bash
uv add pydantic-ai httpx numpy
```

## References

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Pydantic AI Tools & Toolsets](https://ai.pydantic.dev/tools/)
- [Pydantic Logfire](https://docs.pydantic.dev/logfire/)

