"""Single shared Africa's Talking SDK client, so every module talks to AT
the same way instead of re-initializing credentials everywhere."""
import africastalking

from app.config import settings

africastalking.initialize(settings.at_username, settings.at_api_key)

sms = africastalking.SMS
voice = africastalking.Voice
