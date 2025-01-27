from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import time
import json
import re

app = Flask(__name__)

# The only valid API key that will be accepted
VALID_API_KEY = 'pk_test_12345678901234567890123456789012'

# Store to keep generated charges consistent between requests
MOCK_CHARGES_STORE = []

def datetime_to_timestamp(dt):
    """Convert datetime to Unix timestamp"""
    return int(dt.timestamp())

def parse_graphql_filter(query):
    """Extract filter values from GraphQL query"""
    filter_match = re.search(r'filter:\s*{createdAt:\s*{range:\s*\[([\d, ]+)\]}}', query)
    if filter_match:
        timestamps = [int(ts.strip()) for ts in filter_match.group(1).split(',')]
        return timestamps
    return None

def get_size_from_query(query):
    """Extract size from GraphQL query"""
    size_match = re.search(r'charges\s*\(\s*(?:size:\s*(\d+)\s*,?\s*)?', query)
    if size_match and size_match.group(1):
        return int(size_match.group(1))
    return 1000  # Default size in MONEI API

def get_from_query(query):
    """Extract from parameter from GraphQL query"""
    from_match = re.search(r'from:\s*(\d+)', query)
    if from_match:
        return int(from_match.group(1))
    return 0

def generate_mock_address():
    """Generate mock address data"""
    return {
        'city': 'Madrid',
        'country': 'ES',
        'line1': 'Calle Example 123',
        'line2': 'Floor 4',
        'zip': '28001',
        'state': 'Madrid'
    }

def generate_mock_customer():
    """Generate mock customer data"""
    return {
        'email': 'customer@example.com',
        'name': 'John Doe',
        'phone': '+34600000000'
    }

def handle_account_query():
    """Handle the Account query"""
    return {
        'data': {
            'account': {
                'apiKey': VALID_API_KEY
            }
        }
    }

def generate_mock_card():
    """Generate mock card data"""
    return {
        'brand': random.choice(['visa', 'mastercard', 'amex']),
        'country': 'ES',
        'type': random.choice(['credit', 'debit']),
        'threeDSecure': True,
        'threeDSecureVersion': '2.0',
        'threeDSecureFlow': 'challenge',
        'last4': ''.join(random.choices('0123456789', k=4)),
        'cardholderName': 'John Doe',
        'cardholderEmail': 'cardholder@example.com',
        'expiration': f'{random.randint(1, 12):02d}/{random.randint(23, 28)}',
        'bank': 'Test Bank',
        'tokenizationMethod': None,
        '__typename': 'Card'
    }

def generate_mock_session_details():
    """Generate mock session details"""
    return {
        'ip': '192.168.1.1',
        'userAgent': 'Mozilla/5.0',
        'countryCode': 'ES',
        'lang': 'es',
        'deviceType': 'desktop',
        'deviceModel': 'unknown',
        'browser': 'chrome',
        'browserVersion': '100.0',
        'browserAccept': '*/*',
        'browserColorDepth': 24,
        'browserScreenHeight': 1080,
        'browserScreenWidth': 1920,
        'browserTimezoneOffset': -120,
        'os': 'windows',
        'osVersion': '10',
        'source': 'web',
        'sourceVersion': '1.0',
        '__typename': 'SessionDetails'
    }

def generate_mock_trace_details():
    """Generate mock trace details"""
    return {
        'ip': '192.168.1.1',
        'userAgent': 'Mozilla/5.0',
        'countryCode': 'ES',
        'lang': 'es',
        'deviceType': 'desktop',
        'deviceModel': 'unknown',
        'browser': 'chrome',
        'browserVersion': '100.0',
        'browserAccept': '*/*',
        'os': 'windows',
        'osVersion': '10',
        'source': 'web',
        'sourceVersion': '1.0',
        'userId': 'user_1',
        'userEmail': 'user@example.com',
        'userName': 'Test User',
        '__typename': 'TraceDetails'
    }

def generate_mock_metadata():
    """Generate mock metadata"""
    return [
        {'key': 'source', 'value': 'web', '__typename': 'Metadata'},
        {'key': 'integration', 'value': 'direct', '__typename': 'Metadata'}
    ]

def generate_mock_shop():
    """Generate mock shop data"""
    return {
        'name': 'Test Shop',
        'country': 'ES',
        '__typename': 'Shop'
    }

def generate_mock_charges():
    """Generate mock charges data"""
    global MOCK_CHARGES_STORE
    
    if not MOCK_CHARGES_STORE:
        statuses = ['SUCCEEDED', 'PENDING', 'FAILED', 'CANCELED', 'REFUNDED', 'PARTIALLY_REFUNDED', 'AUTHORIZED', 'EXPIRED']
        currencies = ['EUR', 'USD']
        
        for i in range(100):
            created_date = datetime.now() - timedelta(days=random.randint(0, 30))
            updated_date = created_date + timedelta(hours=random.randint(1, 24))
            page_opened_at = datetime_to_timestamp(created_date - timedelta(minutes=random.randint(1, 30)))
            
            MOCK_CHARGES_STORE.append({
                'id': f'ch_{i+1}',
                'accountId': f'acc_{i+1}',
                'providerId': 'stripe',
                'checkoutId': f'co_{i+1}',
                'providerInternalId': f'pi_{i+1}',
                'providerReferenceId': f'ref_{i+1}',
                'createdAt': datetime_to_timestamp(created_date),
                'updatedAt': datetime_to_timestamp(updated_date),
                'amount': round(random.uniform(10, 1000), 2),
                'authorizationCode': f'auth_{i+1}',
                'billingDetails': {
                    'email': 'billing@example.com',
                    'name': 'John Doe',
                    'company': 'Example Company',
                    'phone': '+34600000000',
                    'address': generate_mock_address(),
                    'taxId': 'B12345678',
                    '__typename': 'BillingDetails'
                },
                'billingPlan': None,
                'currency': random.choice(currencies),
                'customer': generate_mock_customer(),
                'description': 'Test purchase',
                'descriptor': 'TEST*PURCHASE',
                'livemode': False,
                'orderId': f'order_{i+1}',
                'storeId': f'store_{i+1}',
                'pointOfSaleId': None,
                'terminalId': None,
                'sequenceId': str(i + 1),
                'subscriptionId': None,
                'paymentMethod': {
                    'method': 'card',
                    'card': generate_mock_card(),
                    'cardPresent': None,
                    'bizum': None,
                    'paypal': None,
                    'cofidis': None,
                    'cofidisLoan': None,
                    'trustly': None,
                    'sepa': None,
                    'klarna': None,
                    'mbway': None,
                    '__typename': 'PaymentMethod'
                },
                'cancellationReason': None,
                'lastRefundAmount': 0,
                'lastRefundReason': None,
                'refundedAmount': 0,
                'shippingDetails': {
                    'email': 'shipping@example.com',
                    'name': 'John Doe',
                    'company': 'Example Company',
                    'phone': '+34600000000',
                    'address': generate_mock_address(),
                    'taxId': 'B12345678',
                    '__typename': 'ShippingDetails'
                },
                'shop': generate_mock_shop(),
                'status': random.choice(statuses),
                'statusCode': '200',
                'statusMessage': 'Transaction completed successfully',
                'sessionDetails': generate_mock_session_details(),
                'traceDetails': generate_mock_trace_details(),
                'pageOpenedAt': page_opened_at,
                'metadata': generate_mock_metadata(),
                '__typename': 'Charge'
            })
    
    return MOCK_CHARGES_STORE

def handle_charges_query(query):
    """Handle the Charges query with filtering and pagination"""
    size = get_size_from_query(query)
    date_range = parse_graphql_filter(query)
    start_from = get_from_query(query)
    
    charges = generate_mock_charges()
    
    if date_range:
        charges = filter_charges_by_date(charges, date_range)
    
    # Store total before pagination
    total_charges = len(charges)
    
    # Apply pagination
    charges = charges[start_from:start_from + size]
    
    return {
        'data': {
            'charges': {
                'total': total_charges,
                'items': charges
            }
        }
    }

def filter_charges_by_date(charges, date_range):
    """Filter charges by date range"""
    if not date_range or len(date_range) != 2:
        return charges
    
    start_ts, end_ts = date_range
    return [
        charge for charge in charges
        if start_ts <= charge['createdAt'] <= end_ts
    ]

def handle_refund_mutation(variables):
    """Handle RefundPayment mutation"""
    input_data = variables.get('input', {})
    payment_id = input_data.get('paymentId')
    refund_amount = input_data.get('amount', 0)
    
    # Find the payment in our mock store
    payment = next((p for p in MOCK_CHARGES_STORE if p['id'] == payment_id), None)
    if not payment:
        return {'errors': [{'message': 'Payment not found'}]}
    
    # Update the payment's refund information
    payment['refundedAmount'] = refund_amount
    payment['lastRefundAmount'] = refund_amount
    payment['lastRefundReason'] = input_data.get('refundReason')
    payment['status'] = 'REFUNDED' if refund_amount >= payment['amount'] else 'PARTIALLY_REFUNDED'
    payment['updatedAt'] = int(time.time())
    
    return {
        'data': {
            'refundPayment': {
                'id': payment_id,
                'status': payment['status'],
                'statusCode': '200',
                'statusMessage': 'Refund processed successfully',
                'refundedAmount': payment['refundedAmount'],
                'lastRefundAmount': payment['lastRefundAmount'],
                'lastRefundReason': payment['lastRefundReason'],
                'updatedAt': payment['updatedAt']
            }
        }
    }

@app.route('/', methods=['POST'])
def handle_graphql():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'errors': [{'message': 'Invalid authorization'}]}), 401
    
    api_key = auth_header.split(' ')[1]
    if api_key != VALID_API_KEY:
        return jsonify({'errors': [{'message': 'Invalid API key'}]}), 401

    query = request.json.get('query', '')
    
    if 'account' in query:
        return jsonify(handle_account_query())
    elif 'charges' in query:
        return jsonify(handle_charges_query(query))
    
    return jsonify({'errors': [{'message': 'Invalid query'}]}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 