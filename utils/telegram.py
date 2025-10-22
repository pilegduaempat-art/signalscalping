# utils/telegram.py
"""
Telegram notification functions
"""
import requests


def send_telegram_message(text: str, bot_token: str = None, chat_id: str = None):
    """
    Send message via Telegram bot
    
    Args:
        text: Message text to send
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
    
    Returns:
        Boolean indicating success
    """
    if not bot_token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False
