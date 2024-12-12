from twilio.rest import Client

# Twilio account credentials
account_sid = 'AC10edda1e37d8ef701a995e74b51a93d1'
auth_token = '3194ea5c80087e3e43aac641fe8645aa'

# Initialize the Twilio Client
client = Client(account_sid, auth_token)

# Phone numbers
to_number = '+9779804016505'  # The number you want to call
from_number = '+12765826635'  # Your verified or purchased Twilio phone number

# Create the call
call = client.calls.create(
    twiml='<Response><Say>Hello, this is a test call from Twilio.</Say></Response>',
    to=to_number,
    from_=from_number
)

# Print the call SID
print(call.sid)