from twilio.rest import Client

account_sid = 'ACa72adc5cdd59a11f2aa935f3c4ec5509'
auth_token = 'b1fc212c56363e91d0d6b996c3cacd1a'

client = Client(account_sid, auth_token)

message = client.messages.create(
    body='Hello there!',
    from_= 'whatsapp:+14155238886',
    to='whatsapp:+9779807941286'
)