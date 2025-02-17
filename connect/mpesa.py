import base64
import json
from datetime import datetime
from django.conf import settings
import logging
import urllib.request
import urllib.parse
import urllib.error
import requests
import http.client




def my_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('mpesa_phone')
        # Process the phone number...

logger = logging.getLogger(__name__)

def generate_password(shortcode, passkey, timestamp):
    """Generate password for M-Pesa API"""
    data_to_encode = shortcode + passkey + timestamp
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')

def initiate_stk_push(phone_number, amount, account_reference):
    """Initiate M-Pesa STK Push payment"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = generate_password(
            settings.MPESA_SHORTCODE,
            settings.MPESA_PASSKEY,
            timestamp
        )

        headers = {
            'Content-Type': 'application/json',
        }

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://random-string.ngrok.io/mpesa/callback/",
            "AccountReference": account_reference,
            "TransactionDesc": "EcoFarm Connect Payment" 
        }

        # Convert payload to JSON bytes
        data = json.dumps(payload).encode('utf-8')

        # Create request
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )

        # Send request and get response
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            logger.info(f"STK Push Response: {response_data}")
            return response_data

    except urllib.error.URLError as e:
        logger.error(f"STK Push Error: {str(e)}")
        return {"ResponseCode": "1", "ResponseDescription": str(e)}
    except Exception as e:
        logger.error(f"STK Push Error: {str(e)}")
        return {"ResponseCode": "1", "ResponseDescription": str(e)}

def verify_transaction(transaction_id):
    try:
        # Implement verification logic here
        return {
            'ResponseCode': '0',
            'ResponseDescription': 'Success'
        }
    except Exception as e:
        logger.error(f"Transaction Verification Error: {str(e)}")
        return {
            'ResponseCode': '1',
            'ResponseDescription': f'Error: {str(e)}'
        }

def process_mpesa_payment(phone_number, amount, account_reference):
    conn = http.client.HTTPSConnection("sandbox.safaricom.co.ke")
    
    headers = {
        "Authorization": "Bearer <your_access_token>",
        "Content-Type": "application/json"
    }
    
    payload = {
        "BusinessShortCode": "<your_shortcode>",
        "Password": "<your_password>",
        "Timestamp": "<your_timestamp>",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": "<your_shortcode>",
        "PhoneNumber": phone_number,
        "CallBackURL": "<your_callback_url>",
        "AccountReference": account_reference,
        "TransactionDesc": "Payment for order"
    }
    
    conn.request("POST", "/mpesa/stkpush/v1/processrequest", json.dumps(payload), headers)
    
    res = conn.getresponse()
    data = res.read()
    
    return json.loads(data.decode("utf-8"))