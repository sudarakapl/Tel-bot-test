# CEO Tasks Bot

## Overview

CEO Tasks Bot is a Telegram bot that automatically extracts tasks from messages and organizes them in Google Sheets. The bot creates separate tabs for different chat groups, enabling efficient task management across teams and projects.

## Features

- **Simple Task Identification**: Identifies tasks from messages starting with a # symbol
- **Multi-group Support**: Creates separate worksheet tabs for each chat group
- **Google Sheets Integration**: Tasks are stored in easily accessible Google Sheets
- **Permission Management**: Restricts sheet access to authorized users
- **Command Interface**: Simple commands for managing and viewing tasks

## Architecture

The project follows a modular architecture with clean separation of concerns:

### Technical Stack

- Python 3.8+
- python-telegram-bot: Telegram API integration
- gspread & oauth2client: Google Sheets API integration
- python-dotenv: Environment variable management

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Telegram bot token (from BotFather)
- Google Cloud project with Sheets API enabled
- Google service account credentials

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/ceo-tasks-bot.git
   cd ceo-tasks-bot
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. Set up environment variables (create a .env file):

   ```
   BOT_TOKEN=your_telegram_bot_token
   AUTHORIZED_USERS=your_telegram_user_id,your_telegram_user_id
   SHEET_NAME=Your Task Sheet Name
   GOOGLE_PROJECT_ID=your_project_id
   GOOGLE_PRIVATE_KEY_ID=your_key_id
   GOOGLE_PRIVATE_KEY="your_private_key"
   GOOGLE_CLIENT_EMAIL=your_client_email@example.com
   GOOGLE_CLIENT_ID=your_client_id
   ```

4. Run the bot:
   ```
   python main.py
   ```

## Bot Commands

- `/start`: Introduction and help
- `/sheet`: Get the Google Sheet URL (restricted to authorized users)
- `/tabs`: List all available tabs/groups
- `/summary`: Show task count summary across all groups

## How It Works

### Task Extraction

The bot uses a simple approach to identify tasks:

- Any message from an authorized user that starts with a # symbol is considered a task
- Each line starting with # in a multi-line message is treated as a separate task
- The # symbol is removed from the beginning of the task when stored

### Google Sheets Integration

Each chat group gets its own worksheet with consistent formatting:

- Color-coded headers
- Appropriate column widths
- Proper cell alignments
- Built-in filters

## Permissions

- The bot only processes messages from authorized users
- Sheet access is restricted based on configuration

## Security Considerations

- Service account credentials are stored in environment variables, not in code
- The Google Sheet can be configured as view-only for non-editors
- Command access is restricted to authorized users

## Future Improvements

- Task status updates via Telegram
- Reminder notifications for upcoming due dates
- Task assignment and reassignment
- Support for recurring tasks
- Integration with other productivity tools
- Data visualization and reporting features

## License

MIT License

_Note: This bot was created to streamline task management for busy executives and teams. Feel free to customize it to meet your specific needs._
