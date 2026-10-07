"""
Mama Pedhewale - Shiprocket Logistics & Shipping Integration Service
Handles server-side token authentication, order creation, courier serviceability,
AWB assignment, pickup scheduling, shipping labels, and real-time shipment tracking.
"""

import os
import time
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Configurable constants & defaults
DEFAULT_BASE_URL = "https://apiv2.shiprocket.in/v1/external"
DEFAULT_SWEET_HSN = "21069099"  # HSN Code for traditional Indian sweets/mithai
TOKEN_EXPIRY_BUFFER = 3600       # Re-authenticate 1 hour before nominal expiry
DEFAULT_PICKUP_PINCODE = "415003" # Mama Pedhewale Satara Kitchen Pincode

# Configurable package defaults for box dimensions (in cm) and minimum dead weight (in kg)
# Standard Indian sweets rigid box packaging dimensions
DEFAULT_PACKAGE_LENGTH = float(os.environ.get('SHIPROCKET_DEFAULT_LENGTH', '15.0'))
DEFAULT_PACKAGE_BREADTH = float(os.environ.get('SHIPROCKET_DEFAULT_BREADTH', '15.0'))
DEFAULT_PACKAGE_HEIGHT = float(os.environ.get('SHIPROCKET_DEFAULT_HEIGHT', '10.0'))
DEFAULT_MIN_WEIGHT_KG = float(os.environ.get('SHIPROCKET_MIN_WEIGHT_KG', '0.5'))
MIN_WEIGHT_KG = DEFAULT_MIN_WEIGHT_KG

# In-memory Token Cache
_token_cache = {
    'token': None,
    'expires_at': 0
}

class ShiprocketError(Exception):
    """Base exception for Shiprocket API errors."""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class ShiprocketConfigError(ShiprocketError):
    """Raised when Shiprocket credentials or settings are missing."""
    pass

def get_config():
    """Returns current Shiprocket environment configuration."""
    return {
        'email': os.environ.get('SHIPROCKET_EMAIL', '').strip(),
        'password': os.environ.get('SHIPROCKET_PASSWORD', '').strip(),
        'base_url': os.environ.get('SHIPROCKET_BASE_URL', DEFAULT_BASE_URL).rstrip('/'),
        'pickup_location': os.environ.get('SHIPROCKET_PICKUP_LOCATION', '').strip(),
        'pickup_pincode': os.environ.get('SHIPROCKET_PICKUP_PINCODE', DEFAULT_PICKUP_PINCODE).strip(),
        'webhook_secret': (os.environ.get('SHIPROCKET_WEBHOOK_SECRET', '') or os.environ.get('SHIPROCKET_WEBHOOK_TOKEN', '')).strip(),
        'auto_create': os.environ.get('SHIPROCKET_AUTO_CREATE', 'true').lower() in ['true', '1', 'yes']
    }

def is_configured():
    """Checks whether valid Shiprocket credentials are set in environment."""
    cfg = get_config()
    return bool(cfg['email'] and cfg['password'])

def get_shiprocket_token(force_refresh=False):
    """
    Retrieves a valid Shiprocket JWT authentication token.
    Uses in-memory cache and automatically refreshes when expired or upon request.
    Never exposes credentials or raw auth headers to caller.
    """
    global _token_cache
    now = time.time()

    if not force_refresh and _token_cache['token'] and now < _token_cache['expires_at']:
        return _token_cache['token']

    cfg = get_config()
    if not cfg['email'] or not cfg['password']:
        raise ShiprocketConfigError("Shiprocket email or password not configured in environment variables.")

    url = f"{cfg['base_url']}/auth/login"
    payload = {
        'email': cfg['email'],
        'password': cfg['password']
    }

    try:
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
    except requests.exceptions.RequestException as e:
        logger.error(f"Shiprocket authentication connection error: {e}")
        raise ShiprocketError(f"Failed to connect to Shiprocket API: {str(e)}")

    if res.status_code != 200:
        logger.error(f"Shiprocket auth failed with status {res.status_code}")
        try:
            err_json = res.json()
            err_msg = err_json.get('message') or err_json.get('error') or f"HTTP {res.status_code}"
        except Exception:
            err_msg = f"HTTP {res.status_code}"
        raise ShiprocketError(f"Shiprocket authentication failed: {err_msg}", status_code=res.status_code)

    data = res.json()
    token = data.get('token')
    if not token:
        raise ShiprocketError("Shiprocket auth succeeded but no token returned in response.")

    # Typically valid for 10 days (864000 seconds)
    expires_in = int(data.get('expires_in', 864000))
    _token_cache['token'] = token
    _token_cache['expires_at'] = now + max(60, expires_in - TOKEN_EXPIRY_BUFFER)

    logger.info("Shiprocket token successfully acquired and cached.")
    return token

def shiprocket_request(method, endpoint, params=None, json_data=None, retry_on_401=True):
    """
    Executes an authenticated Shiprocket API request.
    Automatically adds Bearer token and retries once upon token expiration (401).
    """
    cfg = get_config()
    token = get_shiprocket_token()
    url = f"{cfg['base_url']}/{endpoint.lstrip('/')}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}"
    }

    try:
        res = requests.request(method, url, params=params, json=json_data, headers=headers, timeout=25)
    except requests.exceptions.RequestException as e:
        logger.error(f"Shiprocket request failed for {endpoint}: {e}")
        raise ShiprocketError(f"Shiprocket network error on {endpoint}: {str(e)}")

    if res.status_code == 401 and retry_on_401:
        logger.warning(f"Received 401 on {endpoint}. Re-authenticating token and retrying...")
        token = get_shiprocket_token(force_refresh=True)
        headers['Authorization'] = f"Bearer {token}"
        try:
            res = requests.request(method, url, params=params, json=json_data, headers=headers, timeout=25)
        except requests.exceptions.RequestException as e:
            raise ShiprocketError(f"Shiprocket retry error on {endpoint}: {str(e)}")

    try:
        data = res.json()
    except Exception:
        data = {'text': res.text}

    if res.status_code not in [200, 201]:
        err_msg = data.get('message') or data.get('error') or f"Shiprocket error HTTP {res.status_code}"
        logger.error(f"Shiprocket API error on {endpoint}: {res.status_code} - {err_msg}")
        raise ShiprocketError(err_msg, status_code=res.status_code, response_data=data)

    return data

# ==================== ORDER CREATION ====================

def calculate_order_weight(items):
    """
    Calculates total package dead weight in kilograms based on item weight specifications.

    How weight is determined:
    - Extracts net sweet weight from item 'weight_selected' or 'weight' (e.g. 250g -> 0.25kg, 500g -> 0.5kg, 1kg -> 1.0kg).
    - Multiplies item weight by quantity.
    - Adds 0.1 kg box packaging tare allowance (rigid mithai gift box + moisture barrier lining).
    - Applies minimum dead weight floor (DEFAULT_MIN_WEIGHT_KG = 0.5 kg) required by Shiprocket domestic parcel courier guidelines.
    """
    total_kg = 0.0
    for item in items:
        qty = int(item.get('quantity', 1) or 1)
        w_str = str(item.get('weight_selected', '') or item.get('weight', '')).lower()
        if '250' in w_str:
            item_weight = 0.25
        elif '500' in w_str:
            item_weight = 0.5
        elif '1' in w_str and ('kg' in w_str or 'kilo' in w_str or '1000' in w_str):
            item_weight = 1.0
        else:
            item_weight = 0.5
        total_kg += item_weight * qty

    # Net weight + box packaging tare weight (100g)
    packed_weight = total_kg + 0.1
    return round(max(DEFAULT_MIN_WEIGHT_KG, packed_weight), 2)

def create_shiprocket_order(order_dict, items_list):
    """
    Creates a new custom ad-hoc shipment in Shiprocket for a confirmed Mama Pedhewale order.
    Idempotent: if order is already created in Shiprocket, returns existing shipment IDs.
    """
    # 1. Idempotency Check
    existing_sr_id = order_dict.get('shiprocket_order_id')
    existing_shipment_id = order_dict.get('shiprocket_shipment_id')
    if existing_sr_id and existing_shipment_id:
        logger.info(f"Order {order_dict.get('id')} already has Shiprocket Order ID {existing_sr_id}. Returning existing.")
        return {
            'success': True,
            'shiprocket_order_id': existing_sr_id,
            'shiprocket_shipment_id': existing_shipment_id,
            'status': order_dict.get('shipment_status', 'Created'),
            'message': 'Shiprocket order already created.'
        }

    # 2. Validation
    customer_name = (order_dict.get('customer_name') or 'Customer').strip()
    name_parts = customer_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else 'Customer'

    pincode = str(order_dict.get('pincode', '')).strip()
    phone = str(order_dict.get('customer_phone', '')).strip()
    address1 = str(order_dict.get('address_line1', '')).strip()

    if not pincode or len(pincode) != 6:
        raise ShiprocketError(f"Invalid 6-digit delivery pincode: '{pincode}'")
    if not phone or len(phone) < 10:
        raise ShiprocketError(f"Invalid 10-digit customer mobile number: '{phone}'")
    if not address1:
        raise ShiprocketError("Customer shipping address is missing.")

    cfg = get_config()
    pickup_loc = cfg.get('pickup_location', '').strip()
    if not pickup_loc:
        raise ShiprocketConfigError(
            "Shiprocket pickup location is not configured. Please set SHIPROCKET_PICKUP_LOCATION "
            "in environment variables to match your Shiprocket pickup location nickname."
        )

    # 3. Format line items
    sr_items = []
    for idx, it in enumerate(items_list, 1):
        name = it.get('product_name') or it.get('name') or f"Mama Sweets Item #{idx}"
        sku = it.get('product_id') or f"MP-{idx}"
        wt = it.get('weight_selected') or it.get('weight') or '500g'
        sku_full = f"{sku}-{wt}".replace(' ', '-')
        price = int(it.get('unit_price', 0) or 0)
        qty = int(it.get('quantity', 1) or 1)

        sr_items.append({
            'name': name,
            'sku': sku_full,
            'units': qty,
            'selling_price': price,
            'discount': 0,
            'tax': 0,
            'hsn': DEFAULT_SWEET_HSN
        })

    if not sr_items:
        sr_items.append({
            'name': 'Authentic Satara Sweets Box',
            'sku': 'MP-SATARA-SWEETS-500G',
            'units': 1,
            'selling_price': int(order_dict.get('total_amount', 0)),
            'discount': 0,
            'tax': 0,
            'hsn': DEFAULT_SWEET_HSN
        })

    # 4. Payment Type & Dimensions
    pay_method = str(order_dict.get('payment_method', '')).lower()
    is_cod = (pay_method == 'cod')
    total_amount = int(order_dict.get('total_amount', 0))

    package_weight = calculate_order_weight(items_list)

    # 5. Build Payload
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    payload = {
        'order_id': order_dict['id'],
        'order_date': order_date,
        'pickup_location': pickup_loc,
        'billing_customer_name': first_name,
        'billing_last_name': last_name,
        'billing_address': address1,
        'billing_address_2': order_dict.get('address_line2') or '',
        'billing_city': order_dict.get('city') or 'Satara',
        'billing_pincode': pincode,
        'billing_state': order_dict.get('state') or 'Maharashtra',
        'billing_country': 'India',
        'billing_email': order_dict.get('customer_email') or 'care@mamapedhewale.com',
        'billing_phone': phone,
        'shipping_is_billing': True,
        'order_items': sr_items,
        'payment_method': 'COD' if is_cod else 'Prepaid',
        'sub_total': total_amount,
        'length': DEFAULT_PACKAGE_LENGTH,
        'breadth': DEFAULT_PACKAGE_BREADTH,
        'height': DEFAULT_PACKAGE_HEIGHT,
        'weight': package_weight
    }

    logger.info(f"Sending order creation request to Shiprocket for Order #{order_dict['id']}...")
    res = shiprocket_request('POST', '/orders/create/adhoc', json_data=payload)

    sr_order_id = res.get('order_id')
    sr_shipment_id = res.get('shipment_id')
    status = res.get('status') or 'NEW'

    if not sr_order_id or not sr_shipment_id:
        raise ShiprocketError(f"Unexpected Shiprocket response format: {json.dumps(res)}")

    return {
        'success': True,
        'shiprocket_order_id': str(sr_order_id),
        'shiprocket_shipment_id': str(sr_shipment_id),
        'status': status,
        'raw_response': res
    }

# ==================== COURIER SERVICEABILITY & ASSIGNMENT ====================

def check_courier_serviceability(pickup_pincode=None, delivery_pincode=None, weight=0.5, is_cod=False):
    """
    Checks courier serviceability and rates for a given route and parcel weight.
    """
    cfg = get_config()
    pickup_pin = str(pickup_pincode or cfg.get('pickup_pincode') or DEFAULT_PICKUP_PINCODE).strip()
    params = {
        'pickup_postcode': pickup_pin,
        'delivery_postcode': str(delivery_pincode).strip(),
        'weight': str(weight or DEFAULT_MIN_WEIGHT_KG),
        'cod': 1 if is_cod else 0
    }

    res = shiprocket_request('GET', '/courier/serviceability/', params=params)
    data = res.get('data', {})
    available_couriers = data.get('available_courier_companies', [])

    normalized = []
    for c in available_couriers:
        normalized.append({
            'courier_company_id': c.get('courier_company_id'),
            'courier_name': c.get('courier_name'),
            'rate': float(c.get('rate', 0.0)),
            'etd': c.get('etd') or c.get('estimated_delivery_days') or '2-3 Days',
            'rating': float(c.get('rating') or 4.5),
            'cod_charges': float(c.get('cod_charges') or 0.0)
        })

    # Sort by best rate
    normalized.sort(key=lambda x: x['rate'])
    return {
        'success': True,
        'delivery_pincode': delivery_pincode,
        'couriers': normalized,
        'count': len(normalized)
    }

def assign_courier(shipment_id, courier_id=None):
    """
    Assigns courier and generates unique AWB for a shipment.
    Stores actual returned courier name; never fabricates dummy courier names.
    """
    payload = {
        'shipment_id': int(shipment_id)
    }
    if courier_id:
        payload['courier_id'] = int(courier_id)

    res = shiprocket_request('POST', '/courier/assign/awb', json_data=payload)
    resp_data = res.get('response', {}).get('data', {}) or res.get('data', {}) or res

    awb_code = resp_data.get('awb_code')
    courier_name = resp_data.get('courier_name') or None
    courier_company_id = resp_data.get('courier_company_id') or courier_id

    if not awb_code:
        err_msg = res.get('message') or "AWB generation failed."
        raise ShiprocketError(f"Failed to assign courier AWB: {err_msg}")

    return {
        'success': True,
        'awb_code': str(awb_code),
        'courier_name': str(courier_name) if courier_name else None,
        'courier_company_id': str(courier_company_id) if courier_company_id else None,
        'shipment_id': str(shipment_id)
    }

# ==================== PICKUP & LABELS ====================

def request_pickup(shipment_id, pickup_date=None):
    """
    Schedules doorstep courier pickup from Mama Pedhewale Satara kitchen.
    """
    payload = {
        'shipment_id': [int(shipment_id)]
    }
    if pickup_date:
        payload['pickup_date'] = [pickup_date]

    res = shiprocket_request('POST', '/courier/generate/pickup', json_data=payload)
    response_msg = res.get('response', {}).get('data') or res.get('message') or 'Pickup scheduled successfully'

    return {
        'success': True,
        'shipment_id': str(shipment_id),
        'pickup_status': 'Scheduled',
        'message': str(response_msg)
    }

def generate_label(shipment_id):
    """
    Generates and returns shipping label URL for the parcel.
    """
    payload = {
        'shipment_id': [int(shipment_id)]
    }
    res = shiprocket_request('POST', '/courier/generate/label', json_data=payload)
    label_url = res.get('label_url') or res.get('response', {}).get('label_url')

    if not label_url:
        err_msg = res.get('message') or "Label URL could not be generated."
        raise ShiprocketError(err_msg)

    return {
        'success': True,
        'shipment_id': str(shipment_id),
        'label_url': label_url
    }

def generate_invoice(order_id):
    """
    Generates and returns printable thermal invoice URL.
    """
    payload = {
        'order_ids': [int(order_id)]
    }
    res = shiprocket_request('POST', '/orders/print/invoice', json_data=payload)
    invoice_url = res.get('invoice_url')

    return {
        'success': True,
        'order_id': str(order_id),
        'invoice_url': invoice_url
    }

# ==================== TRACKING ====================

def track_shipment(awb_code=None, shipment_id=None):
    """
    Retrieves real-time tracking information from Shiprocket for given AWB code or shipment ID.
    Never exposes internal auth tokens to the client. Never fabricates courier name.
    """
    if awb_code:
        endpoint = f"/courier/track/awb/{awb_code.strip()}"
    elif shipment_id:
        endpoint = f"/courier/track/shipment/{shipment_id}"
    else:
        raise ShiprocketError("Either awb_code or shipment_id must be provided for tracking.")

    res = shiprocket_request('GET', endpoint)
    tracking_data = res.get('tracking_data', {})
    track_status = tracking_data.get('track_status', 0)

    shipment_track = tracking_data.get('shipment_track', [])
    first_track = shipment_track[0] if shipment_track else {}

    current_status = first_track.get('current_status') or tracking_data.get('current_status') or 'In Transit'
    courier = first_track.get('courier_name') or None
    scans = tracking_data.get('shipment_track_activities') or first_track.get('scans') or []

    return {
        'success': True,
        'awb_code': awb_code or first_track.get('awb_code'),
        'current_status': current_status,
        'courier_name': courier,
        'expected_date': first_track.get('expected_date'),
        'origin': first_track.get('origin') or 'Satara Hub',
        'destination': first_track.get('destination'),
        'scans': scans,
        'tracking_url': f"https://shiprocket.co/tracking/{awb_code}" if awb_code else None
    }

def normalize_shiprocket_status(raw_status):
    """
    Normalizes Shiprocket tracking / webhook status string into internal:
    (shipment_status, order_status_or_None)
    """
    s = str(raw_status or '').strip().upper()
    if not s:
        return 'Pending', None

    if any(k in s for k in ['RTO', 'RETURN']):
        return 'RTO', None
    if any(k in s for k in ['CANCEL']):
        return 'Cancelled', 'Cancelled'
    if s in ['DELIVERED', 'DLVD']:
        return 'Delivered', 'Delivered'
    if any(k in s for k in ['OUT FOR DELIVERY', 'OFD']):
        return 'Out for Delivery', 'Out for Delivery'
    if any(k in s for k in ['IN TRANSIT', 'TRANSIT', 'SHIPPED', 'DISPATCHED', 'REACHED AT DESTINATION']):
        return 'In Transit', 'Dispatched'
    if any(k in s for k in ['PICKED UP', 'PICKUP DONE']):
        return 'Picked Up', 'Dispatched'
    if any(k in s for k in ['PICKUP SCHEDULED', 'PICKUP GENERATED', 'PICKUP QUEUED']):
        return 'Pickup Scheduled', None
    if any(k in s for k in ['AWB ASSIGNED', 'AWB GENERATED']):
        return 'AWB Assigned', None
    if any(k in s for k in ['NEW', 'CREATED', 'MANIFEST GENERATED']):
        return 'Created', None

    return raw_status.title(), None

def cancel_shipment(awb_code=None, order_ids=None):
    """
    Cancels shipment in Shiprocket if it has not yet been dispatched.
    """
    payload = {}
    if awb_code:
        payload['awbs'] = [str(awb_code)]
    if order_ids:
        payload['ids'] = [int(oid) for oid in order_ids]

    res = shiprocket_request('POST', '/orders/cancel', json_data=payload)
    return {
        'success': True,
        'message': res.get('message', 'Shipment cancellation submitted.')
    }
