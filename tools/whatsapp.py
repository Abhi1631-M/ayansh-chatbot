import os
import requests

def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Send a plain text message to a user via the Meta WhatsApp Cloud API.
    """
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not token or not phone_id:
        print("Warning: WhatsApp credentials not configured in environment.")
        return False

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send WhatsApp message: {e}")
        if e.response is not None:
            print("Response:", e.response.text)
        return False
