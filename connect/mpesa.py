import base64
import json
from datetime import datetime
from django.conf import settings
import logging
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)

class MpesaGateway:
    def __init__(self):
        self.env = settings.MPESA_ENVIRONMENT
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        
        if self.env == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
    
    def _make_request(self, url, headers=None, data=None, method='GET'):
        try:
            if data:
                data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers or {},
                method=method
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.URLError as e:
            logger.error(f"Request Error: {str(e)}")
            return None
    
    def get_access_token(self):
        try:
            auth = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            response = self._make_request(url, headers=headers)
            
            return response.get('access_token') if response else None
            
        except Exception as e:
            logger.error(f"Access Token Error: {str(e)}")
            return None

    def initiate_stk_push(self, phone_number, amount, reference):
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    'ResponseCode': '1',
                    'ResponseDescription': 'Failed to get access token'
                }

            # Format phone number
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://yourdomain.com/mpesa/callback",
                "AccountReference": reference,
                "TransactionDesc": f"Payment for {reference}"
            }

            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            response = self._make_request(
                url,
                headers=headers,
                data=payload,
                method='POST'
            )

            return response or {
                'ResponseCode': '1',
                'ResponseDescription': 'Failed to process request'
            }

        except Exception as e:
            logger.error(f"STK Push Error: {str(e)}")
            return {
                'ResponseCode': '1',
                'ResponseDescription': f'Error: {str(e)}'
            }

# Create an instance to use in views
mpesa = MpesaGateway()

def initiate_stk_push(phone_number, amount, account_reference):
    return mpesa.initiate_stk_push(phone_number, amount, account_reference)

def verify_transaction(transaction_id):
    try:
        # Implement verification using urllib if needed
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