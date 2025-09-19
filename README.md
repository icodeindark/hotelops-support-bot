# HotelOpsAI Support Bot 🤖

A LangGraph-based intelligent support chatbot for HotelOpsAI with comprehensive user management, FAQ system, and session state management.

## Features

### 🔧 **Core Functionality**
- **Interactive User Management**: Create, edit, delete users with multi-turn conversations
- **Smart Session Management**: Persistent conversation state across interactions
- **FAQ System**: Categorized FAQ database with intelligent search
- **Service Management**: Work order and service tracking
- **Troubleshooting Assistant**: Contextual problem-solving guidance

### 🚀 **Technical Architecture**
- **LangGraph**: State-based conversation flow management
- **Streamlit**: Real-time chat interface with debug panel
- **Google Gemini 2.0 Flash**: Natural language processing
- **Session Persistence**: Multi-turn conversation context
- **Smart Routing**: Intent-based query routing to specialized handlers

### 📊 **Comprehensive Logging System**

The bot includes a robust logging system that tracks all actions, errors, and API calls:

#### **Log Categories**
- **Main Logs**: Application flow, user sessions, chat interactions
- **Agent Logs**: LangGraph state transitions and routing decisions
- **User Management**: User creation, editing, deletion activities
- **Session Logs**: Session state changes and persistence
- **FAQ Logs**: Search queries and result matching
- **LLM Logs**: API calls to Google Gemini with token usage
- **API Logs**: External API calls with status and response times
- **Error Logs**: Comprehensive error tracking with stack traces

#### **Log Features**
- **Real-time Monitoring**: Live log viewer in the debug panel
- **Structured Format**: Timestamp, level, component, function, line number
- **Session Tracking**: All logs linked to user sessions
- **Error Context**: Full stack traces for debugging
- **API Monitoring**: Track quota usage and response times

#### **Log File Location**
Logs are automatically created in the `logs/` directory with timestamp-based filenames:
```
logs/hotelops_bot_YYYYMMDD_HHMMSS.log
```

## Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/icodeindark/hotelops-support-bot.git
cd hotelops-support-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
Create a `.env` file:
```env
GEN_API_KEY=your_gemini_api_key_here
```

5. **Run the application**
```bash
streamlit run main.py
```

## Usage Examples

### **User Management**
```
User: "i wanna add a user to the system"
Bot: Initiates interactive user creation workflow

User: "John Doe,john@hotel.com,555-1234,manager"
Bot: Processes structured data and creates user
```

### **FAQ Queries**
```
User: "how to create a user?"
Bot: Returns relevant FAQ with step-by-step instructions

User: "what are privilege levels?"
Bot: Explains user roles and permissions
```

### **Service Management**
```
User: "list all services"
Bot: Shows current work orders and services

User: "create new service"
Bot: Guides through service creation process
```

## File Structure

```
hotelops-support-bot/
├── agents/
│   ├── __init__.py
│   └── support_agent.py          # LangGraph agent definition
├── context/
│   ├── __init__.py
│   ├── faq.json                  # FAQ database
│   ├── role_context.py           # Agent persona definition
│   ├── services.json             # Service templates
│   ├── troubleshooting.json      # Troubleshooting guides
│   └── users_data.json           # User data storage
├── tools/
│   ├── __init__.py
│   ├── faq_tools.py              # FAQ search and management
│   ├── interactive_user_manager.py # User management workflows
│   ├── service_tools.py          # Service management
│   ├── session_manager.py        # Session state management
│   ├── troubleshooting.py        # Troubleshooting logic
│   ├── user_data_manager.py      # User CRUD operations
│   └── user_tools.py             # User utilities
├── utils/
│   └── json_utils.py             # JSON file operations
├── logs/                         # Log files (auto-generated)
├── logger_config.py              # Logging configuration
├── llm_utils.py                  # Google Gemini integration
├── main.py                       # Streamlit application
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Configuration

### **Logging Configuration**
Modify `logger_config.py` to adjust:
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Log format and structure
- File rotation and retention
- Component-specific logging

### **Agent Behavior**
Customize agent responses in:
- `context/role_context.py` - Agent persona
- `context/faq.json` - FAQ responses
- `agents/support_agent.py` - Routing logic

### **Data Storage**
JSON-based storage (development):
- `context/users_data.json` - User accounts
- `context/services.json` - Service templates

## Development

### **Adding New Features**
1. Create new tools in `tools/` directory
2. Update `agents/support_agent.py` routing
3. Add relevant logging calls
4. Update FAQ database if needed

### **Debugging**
- Use the Debug Panel in the Streamlit interface
- Monitor live logs for real-time troubleshooting
- Check log files for detailed error traces

### **Testing User Management**
```bash
# Test user creation
"add user John Doe, john@hotel.com, 555-1234, manager"

# Test listing users
"show all users"

# Test user editing
"edit user john@hotel.com"
```

## API Integration

Currently uses:
- **Google Gemini 2.0 Flash**: Natural language processing
- **Future**: HotelOpsAI backend API integration

## Error Handling

The system includes comprehensive error handling:
- **API Quota Management**: Graceful handling of rate limits
- **Session Recovery**: Automatic session state restoration
- **User-Friendly Messages**: Clear error communication
- **Detailed Logging**: Full error context for debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive logging to new features
4. Test thoroughly with the debug panel
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues:
1. Check the logs in the debug panel
2. Review the FAQ database
3. Open an issue on GitHub
4. Contact the development team

---

**Built with ❤️ for HotelOpsAI**
