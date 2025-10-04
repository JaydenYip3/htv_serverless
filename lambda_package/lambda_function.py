import os
import json
from urllib.parse import parse_qs
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

def lambda_handler(event, _context):
    # Check if this is a Twilio webhook (incoming SMS)
    headers = event.get('headers', {})

    # API Gateway may normalize headers to lowercase or use different casing
    content_type = (headers.get('content-type') or
                    headers.get('Content-Type') or
                    headers.get('content-Type') or '')

    if 'application/x-www-form-urlencoded' in content_type.lower():
        return handle_incoming_sms(event)
    else:
        return handle_send_sms(event)

def handle_incoming_sms(event):
    """Handle incoming SMS from Twilio webhook"""
    # Parse form data from Twilio
    body = event.get('body', '')

    # Handle base64 encoded body if API Gateway encoding is enabled
    if event.get('isBase64Encoded', False):
        import base64
        body = base64.b64decode(body).decode('utf-8')

    params = parse_qs(body)

    from_number = params.get('From', ['Unknown'])[0]
    incoming_message = params.get('Body', [''])[0]

    # Create TwiML response
    resp = MessagingResponse()
    resp.message(f"You said: {incoming_message}")

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/xml'},
        'body': str(resp)
    }

def handle_send_sms(event):
    """Handle outgoing SMS requests"""
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')

    # Parse request body
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }

    to_number = body.get('to')
    message = body.get('message')

    if not all([account_sid, auth_token, from_number]):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Twilio credentials not configured'})
        }

    if not to_number or not message:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required fields: to, message'})
        }

    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)

        # Send SMS
        twilio_message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SMS sent successfully',
                'sid': twilio_message.sid
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }