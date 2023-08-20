from twilio.rest import Client
import Constants
account_sid = Constants.TWILIO_ACCOUNT_SID
auth_token = Constants.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)
def send_message(messageBody):
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=messageBody,
    to='whatsapp:+6597988922'
    )
    print(message.sid)
    return