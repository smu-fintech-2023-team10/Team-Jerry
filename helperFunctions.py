from twilio.rest import Client
def send_message(messageBody, recepientNumber, client):
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=messageBody,
    to=recepientNumber
    )
    print(message.sid)
    return