from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN, AUTHORIZED_USERS
from task_extraction import extract_tasks_from_message, find_hidden_tasks
from sheets_manager import (
    append_task_to_sheet,
    get_spreadsheet_url,
    get_all_worksheets,
    get_worksheet_summary,
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming messages and extract tasks starting with #"""
    message = update.message
    if not message or not message.from_user:
        return

    user = message.from_user
    chat = message.chat

    # Check if the user is authorized
    is_authorized = user.id in AUTHORIZED_USERS

    # If not authorized, exit
    if not is_authorized:
        return

    text = message.text
    if not text:
        return

    # Get chat name (for the sheet tab)
    if chat.type == "private":
        chat_name = f"Private_{user.username or user.first_name}"
    else:
        chat_name = chat.title

    # Extract tasks that start with #
    tasks = extract_tasks_from_message(text)

    if tasks:
        tasks_added = 0
        for task in tasks:
            if append_task_to_sheet(task, user.full_name, text, chat_name, chat.id):
                tasks_added += 1

        if tasks_added > 0:
            await message.reply_text(f"✅ Added {tasks_added} task(s) to the list.")
        else:
            await message.reply_text("❌ Failed to add tasks. Please try again later.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    await update.message.reply_text(
        "👋 Hello! I'm your task assistant. Add me to groups or send me messages directly, "
        "and I'll extract and organize tasks into Google Sheets!"
    )


async def sheet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the Google Sheet link"""
    sheet_url = get_spreadsheet_url()
    if sheet_url:
        await update.message.reply_text(f"📊 Here's the task list: {sheet_url}")
    else:
        await update.message.reply_text("❌ Unable to retrieve the sheet link.")


async def tabs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available tabs"""
    tabs = get_all_worksheets()

    if tabs:
        message = "📊 Available task lists:\n\n"
        for i, tab in enumerate(tabs, 1):
            message += f"{i}. {tab}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No task lists created yet.")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show task summary across all tabs"""
    summary = get_worksheet_summary()

    if summary:
        message = "📈 Task Summary:\n\n"
        total_tasks = 0

        for tab, count in summary.items():
            total_tasks += count
            message += f"{tab}: {count} tasks\n"

        message += f"\nTotal: {total_tasks} tasks"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No task lists created yet.")


def create_bot():
    """Create and configure the bot"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("sheet", sheet_command))
    app.add_handler(CommandHandler("tabs", tabs_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set up commands for the command menu
    commands = [
        BotCommand("start", "Start the bot and get help"),
        BotCommand(
            "sheet", "Get the Google Sheet URL (anyone with the link can edit it)"
        ),
        BotCommand("tabs", "List all available tabs/groups"),
        BotCommand("summary", "Show task count summary"),
    ]

    # Set the commands during startup
    async def setup_hook(self):
        await self.bot.set_my_commands(commands)

    app.post_init = setup_hook

    return app
