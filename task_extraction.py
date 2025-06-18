import re


def extract_tasks_from_message(message):
    """Extract tasks from a message by checking if it starts with #"""
    # Check if the message starts with #
    message_text = message.strip()

    if message_text.startswith("#"):
        # Remove just the # from the beginning of the message
        task = message_text[1:].strip()
        if task:  # Make sure there's actual content after the #
            return [task]

    return []


def is_valid_task(text):
    """All tasks starting with # are considered valid"""
    return bool(text.strip())


def find_hidden_tasks(message):
    """
    No hidden tasks in the simplified approach
    All tasks must explicitly start with #
    """
    return []
