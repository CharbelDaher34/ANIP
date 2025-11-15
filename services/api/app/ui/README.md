# ANIP Chat UI

A modern, responsive chat interface for the ANIP News Intelligence system powered by AI agents.

## Overview

The ANIP Chat UI provides an intuitive interface for users to interact with the news intelligence system through natural language queries. It leverages the Pydantic AI agent to search across multiple news sources and provide comprehensive, analyzed responses.

## Features

- 🎨 **Modern UI**: Clean, responsive design with smooth animations
- 💬 **Conversation Management**: Create, view, and delete conversations
- 🤖 **AI-Powered Search**: Integrates with the news agent for intelligent responses
- 📊 **Rich Results**: Display sources with metadata (topic, sentiment, relevance)
- 🔍 **Multi-Source Search**: Query both DuckDuckGo and internal database
- 📱 **Responsive**: Works on desktop, tablet, and mobile devices
- 🎯 **Collapsible Sources**: Expand/collapse source sections to manage screen space
- 🔎 **Detailed Source View**: Click any source to view full details in a modal
- ⌨️ **Keyboard Shortcuts**: ESC to close modals, smooth interactions
- 🎬 **Smooth Animations**: Slide-up modals, fade-in effects, smooth transitions

## Architecture

### Frontend
- **Pure HTML/CSS/JavaScript** - No frameworks required
- **Vanilla JS** - Lightweight and fast
- **REST API** - Communicates with backend via JSON APIs

### Backend Integration
- **FastAPI** - Serves static files and API endpoints
- **SQLAlchemy** - Persists conversations and messages
- **Pydantic AI Agent** - Processes queries and searches news sources

### Database Models

#### Conversation
- `id`: Primary key
- `title`: Conversation title
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- Relationship: Has many messages

#### Message
- `id`: Primary key
- `conversation_id`: Foreign key to conversation
- `user_query`: User's question
- `summary`: AI-generated summary
- `answer`: AI-generated comprehensive answer
- `query_intent`: Interpreted intent
- `duckduckgo_results`: JSON array of DuckDuckGo results
- `database_results`: JSON array of database results
- `sources_used`: JSON array of source names
- `total_results`: Total result count
- `duckduckgo_count`: DuckDuckGo result count
- `database_count`: Database result count
- `created_at`: Creation timestamp

## File Structure

```
services/ui/
├── README.md                   # This file
└── static/
    ├── index.html             # Main UI template
    ├── styles.css             # All styles and responsive design
    └── app.js                 # Application logic and API calls
```

## API Endpoints

### Conversations

#### GET /api/conversations/
Get all conversations ordered by most recent.

**Response:**
```json
[
  {
    "id": 1,
    "title": "Chat 2025-11-15...",
    "created_at": "2025-11-15T10:00:00",
    "updated_at": "2025-11-15T10:30:00",
    "message_count": 5
  }
]
```

#### POST /api/conversations/
Create a new conversation.

**Request:**
```json
{
  "title": "My New Chat"
}
```

**Response:**
```json
{
  "id": 2,
  "title": "My New Chat",
  "created_at": "2025-11-15T11:00:00",
  "updated_at": "2025-11-15T11:00:00",
  "message_count": 0
}
```

#### GET /api/conversations/{conversation_id}
Get a specific conversation.

#### DELETE /api/conversations/{conversation_id}
Delete a conversation and all its messages.

### Messages

#### GET /api/conversations/{conversation_id}/messages
Get all messages in a conversation.

**Response:**
```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "user_query": "Latest AI news",
    "summary": "Recent developments in AI...",
    "answer": "Comprehensive answer...",
    "query_intent": "Breaking news search",
    "duckduckgo_results": [...],
    "database_results": [...],
    "sources_used": ["DuckDuckGo", "Internal Database"],
    "total_results": 8,
    "duckduckgo_count": 5,
    "database_count": 3,
    "created_at": "2025-11-15T10:05:00"
  }
]
```

#### POST /api/conversations/{conversation_id}/messages
Create a new message (calls the news agent).

**Request:**
```json
{
  "user_query": "What are the latest AI developments?",
  "max_results": 5,
  "search_provider": "both"
}
```

**Parameters:**
- `user_query`: The user's question
- `max_results`: Maximum results per source (default: 5)
- `search_provider`: "both", "duckduckgo", or "database" (default: "both")

## Usage

### Accessing the UI

Once the API service is running, access the chat UI at:

```
http://localhost:8000/chat
```

### Workflow

1. **Start a New Chat**: Click "New Chat" to create a conversation
2. **Ask Questions**: Type your query about news topics
3. **Configure Search**: Choose search sources (both/DuckDuckGo/database)
4. **View Results**: See AI-generated summary, answer, and sources
5. **Explore Sources**: Click on source items to open articles
6. **Manage Chats**: Switch between conversations or delete old ones

### Search Options

- **Both Sources**: Searches both DuckDuckGo and internal database
- **DuckDuckGo Only**: Only searches external web via DuckDuckGo
- **Database Only**: Only searches analyzed articles in database

## Development

### Adding New Features

#### Frontend (app.js)
- Add new functions in `app.js`
- Use `fetchAPI()` for API calls
- Update rendering functions for new data

#### Backend (conversation_routes.py)
- Add new endpoints in `conversation_routes.py`
- Define Pydantic models for request/response
- Include router in `main.py`

### Styling

All styles are in `styles.css` with CSS variables for easy customization:

```css
:root {
    --primary-color: #2563eb;
    --bg-color: #f8fafc;
    --sidebar-bg: #ffffff;
    /* ... more variables */
}
```

### Testing

```bash
# Test conversation creation
curl -X POST http://localhost:8000/api/conversations/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'

# Test message creation
curl -X POST http://localhost:8000/api/conversations/1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Latest AI news",
    "max_results": 3,
    "search_provider": "both"
  }'
```

## Features in Detail

### Conversation List
- Shows all conversations ordered by most recent
- Displays message count and last updated time
- Click to open a conversation
- Delete conversations with confirmation

### Message Display
- User messages: Blue bubbles on the right
- Agent responses: White cards with detailed information
- AI-generated summary in highlighted box
- Comprehensive answer with sources
- Source sections for DuckDuckGo and database results

### Source Items
- **Collapsible Sections**: Click source section headers to expand/collapse results
- **Hover Effects**: Items lift up slightly on hover to indicate clickability
- **Click to View Details**: Click any source item to open detailed modal view
- **Smooth Transitions**: Animated collapse/expand with smooth max-height transitions

### Source Details Modal
- **Clean Layout**: Organized sections for title, URL, content, and metadata
- **Keyboard Support**: Press ESC to close modal
- **Click Outside**: Click the blurred overlay to close
- **Smooth Animation**: Slide-up animation with fade-in effect
- **Scrollable Content**: Long content scrolls within modal body
- **External Links**: URL opens in new tab with visual indicator
- **Rich Metadata**: Displays all available source information (topic, sentiment, relevance, author, publish date)

### Real-time Updates
- Loading indicators during API calls
- Smooth animations for new messages
- Auto-scroll to latest message
- Disabled inputs while processing

## Responsive Design

The UI adapts to different screen sizes:

- **Desktop (>768px)**: Sidebar + chat area side-by-side
- **Tablet/Mobile (<768px)**: Stacked layout, collapsible sidebar

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security Considerations

- No authentication implemented (add if needed)
- XSS protection via HTML escaping
- CORS configured in FastAPI
- Input validation on backend

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Conversation search and filtering
- [ ] Message editing and deletion
- [ ] Export conversations
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle
- [ ] Message reactions
- [ ] Share conversations

## Troubleshooting

### UI Not Loading
- Check that API service is running
- Verify static files path in main.py
- Check browser console for errors

### API Errors
- Check API service logs
- Verify database connection
- Ensure news agent is configured

### Styling Issues
- Clear browser cache
- Check CSS file is loading
- Verify static files are mounted

## References

- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

