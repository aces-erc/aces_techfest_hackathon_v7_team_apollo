from twilio.rest import Client

account_sid = 'ACa72adc5cdd59a11f2aa935f3c4ec5509'
auth_token = 'b1fc212c56363e91d0d6b996c3cacd1a'

Client = Client(account_sid, auth_token)

to_number = '+9779807941286'
from_number = '+13204349487'

call = Client.calls.create(
    twiml='<Response><Dial>+9779807941286</Dial></Response>',
    to=to_number,
    from_=from_number
)

print(call.sid)
