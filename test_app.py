import unittest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from app import app
from database import get_db, init_db
from seed_data import seed_database

class MamaPedhewaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        for k in ['SHIPROCKET_EMAIL', 'SHIPROCKET_PASSWORD', 'SHIPROCKET_WEBHOOK_SECRET', 'SHIPROCKET_WEBHOOK_TOKEN', 'SHIPROCKET_PICKUP_LOCATION']:
            os.environ.pop(k, None)
        seed_database()
        cls.client = app.test_client()

    def setUp(self):
        import os
        for k in ['SHIPROCKET_EMAIL', 'SHIPROCKET_PASSWORD', 'SHIPROCKET_WEBHOOK_SECRET', 'SHIPROCKET_WEBHOOK_TOKEN', 'SHIPROCKET_PICKUP_LOCATION']:
            os.environ.pop(k, None)

    def test_01_homepage_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MAMA PEDHEWALE', response.data)
        self.assertIn(b'Satari Kandi Pedhe', response.data)

    def test_02_products_catalog(self):
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Our Royal Sweets', response.data)

        # Category filter test
        cat_resp = self.client.get('/products?category=pedha')
        self.assertEqual(cat_resp.status_code, 200)
        self.assertIn(b'Satari Kandi Pedhe', cat_resp.data)

    def test_03_product_detail(self):
        response = self.client.get('/product/satara-kandi-pedha')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Pure Buffalo Milk Khoya', response.data)

    def test_04_custom_box_builder(self):
        response = self.client.get('/custom-box')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Build Your Custom Sweet Box', response.data)

    def test_05_checkout_and_cart_pages(self):
        cart_resp = self.client.get('/cart')
        self.assertEqual(cart_resp.status_code, 200)
        checkout_resp = self.client.get('/checkout')
        self.assertEqual(checkout_resp.status_code, 200)

    def test_06_pincode_checker_api(self):
        # Satara origin pincode
        response = self.client.post('/api/check-pincode', 
            data=json.dumps({'pincode': '415001'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['serviceable'])
        self.assertEqual(data['city'], 'Satara')
        self.assertTrue(data['same_day_available'])

        # Invalid pincode
        inv_response = self.client.post('/api/check-pincode',
            data=json.dumps({'pincode': '123'}),
            content_type='application/json'
        )
        self.assertEqual(inv_response.status_code, 400)

    def test_07_order_creation_flow(self):
        order_payload = {
            'customer': {
                'name': 'Ramesh Shinde',
                'phone': '9876543210',
                'email': 'ramesh@example.com',
                'address1': '104, Golden Palms, Shivaji Circle',
                'city': 'Satara',
                'state': 'Maharashtra',
                'pincode': '415001'
            },
            'delivery': {
                'type': 'standard',
                'fee': 0,
                'date': '2026-09-05',
                'slot': 'Morning (9 AM - 1 PM)',
                'gift_message': 'Happy Ganesh Chaturthi!'
            },
            'payment': {
                'method': 'upi'
            },
            'items': [
                {
                    'product_id': 'satara-kandi-pedha',
                    'name': 'Satara Special Kandi Pedha',
                    'price': 360,
                    'weight': '500g',
                    'quantity': 2,
                    'image_url': '/static/images/satara_kandi_pedha.jpg',
                    'is_custom_box': False
                },
                {
                    'product_id': 'shahi-kaju-katli',
                    'name': 'Shahi Kaju Katli',
                    'price': 500,
                    'weight': '500g',
                    'quantity': 1,
                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950',
                    'is_custom_box': False
                }
            ]
        }

        response = self.client.post('/api/orders',
            data=json.dumps(order_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        order_id = data['order_id']
        self.assertTrue(order_id.startswith('MP-'))
        # 360*2 + 500*1 = 1220
        self.assertEqual(data['total_amount'], 1220)

        # Verify order success page
        success_resp = self.client.get(f'/order-success/{order_id}')
        self.assertEqual(success_resp.status_code, 200)
        self.assertIn(order_id.encode(), success_resp.data)
        self.assertIn(b'Ramesh Shinde', success_resp.data)

        # Verify tracking page
        track_resp = self.client.get(f'/track-order?order_id={order_id}')
        self.assertEqual(track_resp.status_code, 200)
        self.assertIn(order_id.encode(), track_resp.data)

        # Verify admin status update with authenticated session
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        update_resp = self.client.post(f'/api/admin/order/{order_id}/status',
            data=json.dumps({'status': 'Packed'}),
            content_type='application/json'
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertTrue(update_resp.get_json()['success'])

        # Verify dispatch triggers AWB and Google Maps route
        dispatch_resp = self.client.post(f'/api/admin/order/{order_id}/status',
            data=json.dumps({'status': 'Dispatched'}),
            content_type='application/json'
        )
        self.assertEqual(dispatch_resp.status_code, 200)

        track_disp = self.client.get(f'/track-order?order_id={order_id}')
        self.assertEqual(track_disp.status_code, 200)
        self.assertIn(b'maps.google.com/maps', track_disp.data)
        self.assertIn(b'Dispatched', track_disp.data)
        self.assertIn(b'MP-EXP-', track_disp.data)

    def test_08_corporate_inquiry(self):
        inq_payload = {
            'company_name': 'Tata Consultancy Services',
            'contact_person': 'Pooja Nair',
            'email': 'pooja@tcs.com',
            'phone': '9822114455',
            'estimated_boxes': 150,
            'event_date': '2026-10-25',
            'message': 'Diwali gifting for executive team.'
        }
        response = self.client.post('/api/corporate-inquiry',
            data=json.dumps(inq_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    def test_09_admin_auth_and_stock(self):
        # 1. Unauthenticated request to /admin redirects to login
        with self.client.session_transaction() as sess:
            sess.pop('admin_logged_in', None)

        unauth_resp = self.client.get('/admin')
        self.assertEqual(unauth_resp.status_code, 302)
        self.assertIn('/admin/login', unauth_resp.headers['Location'])

        # 2. Failed login attempt
        bad_login = self.client.post('/admin/login', data={'username': 'wrong', 'password': 'wrong'})
        self.assertEqual(bad_login.status_code, 200)
        self.assertIn(b'Invalid admin username or password', bad_login.data)

        # 3. Successful login redirects to dashboard
        login_resp = self.client.post('/admin/login', data={'username': 'admin', 'password': 'MamaSatara@1948'}, follow_redirects=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn(b'Mama Pedhewale Dashboard', login_resp.data)

        # 4. Authenticated admin can toggle stock
        response = self.client.post('/api/admin/product/satara-kandi-pedha/toggle-stock')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

        # Toggle back
        response2 = self.client.post('/api/admin/product/satara-kandi-pedha/toggle-stock')
        self.assertTrue(response2.get_json()['in_stock'])

    def test_10_admin_logout(self):
        # Authenticate first
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # Test logout
        logout_resp = self.client.get('/admin/logout')
        self.assertEqual(logout_resp.status_code, 302)

        # After logout, accessing /admin is redirected to /admin/login
        locked_resp = self.client.get('/admin')
        self.assertEqual(locked_resp.status_code, 302)

    def test_11_admin_delete_order(self):
        # 1. Create a test order
        order_payload = {
            'customer': {
                'name': 'Test Deletion Customer',
                'phone': '9999999999',
                'email': 'delete@test.com',
                'address': 'Test Street',
                'city': 'Satara',
                'pincode': '415001'
            },
            'items': [{
                'product_id': 'satara-kandi-pedha',
                'name': 'Satara Kandi Pedha',
                'weight': '500g',
                'quantity': 1,
                'price': 340
            }],
            'total_amount': 340,
            'payment_method': 'cod',
            'delivery_slot': 'Morning'
        }
        res = self.client.post('/api/orders', data=json.dumps(order_payload), content_type='application/json')
        order_id = res.get_json()['order_id']

        # 2. Unauthenticated deletion attempt should fail with 401
        with self.client.session_transaction() as sess:
            sess.pop('admin_logged_in', None)
        unauth_del = self.client.post(f'/api/admin/order/{order_id}/delete')
        self.assertEqual(unauth_del.status_code, 401)

        # 3. Mark as Dispatched to verify pre-dispatch safeguard
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        self.client.post(f'/api/admin/order/{order_id}/status',
            data=json.dumps({'status': 'Dispatched'}),
            content_type='application/json'
        )
        dispatched_del = self.client.post(f'/api/admin/order/{order_id}/delete')
        self.assertEqual(dispatched_del.status_code, 400)
        self.assertIn(b'pre-dispatch', dispatched_del.data)

        # 4. Reset status to Packed/Confirmed and delete successfully
        self.client.post(f'/api/admin/order/{order_id}/status',
            data=json.dumps({'status': 'Packed'}),
            content_type='application/json'
        )
        del_resp = self.client.post(f'/api/admin/order/{order_id}/delete')
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.get_json()['success'])

        # 5. Trying to delete already deleted order returns 404
        del_404 = self.client.post(f'/api/admin/order/{order_id}/delete')
        self.assertEqual(del_404.status_code, 404)

    def test_12_super_admin_price_editing(self):
        # 1. Test regular admin login has is_super_admin = False
        login_staff = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'MamaSatara@1948'
        }, follow_redirects=True)
        self.assertEqual(login_staff.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('admin_logged_in'))
            self.assertFalse(sess.get('is_super_admin', False))

        # 2. Regular admin attempting to update prices should receive 403 Forbidden
        staff_update = self.client.post('/api/admin/product/satara-kandi-pedha/update-prices',
            data=json.dumps({'price_250g': 200, 'price_500g': 380, 'price_1kg': 720}),
            content_type='application/json'
        )
        self.assertEqual(staff_update.status_code, 403)
        self.assertIn(b'Super Admin', staff_update.data)

        # 3. Super admin login
        login_super = self.client.post('/admin/login', data={
            'username': 'superadmin',
            'password': 'MamaSuper@1948'
        }, follow_redirects=True)
        self.assertEqual(login_super.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('admin_logged_in'))
            self.assertTrue(sess.get('is_super_admin', False))

        # 4. Invalid price test (0 or negative price)
        bad_price = self.client.post('/api/admin/product/satara-kandi-pedha/update-prices',
            data=json.dumps({'price_250g': 0, 'price_500g': 380, 'price_1kg': 720}),
            content_type='application/json'
        )
        self.assertEqual(bad_price.status_code, 400)

        # 5. Successful price update by Super Admin
        valid_update = self.client.post('/api/admin/product/satara-kandi-pedha/update-prices',
            data=json.dumps({'price_250g': 210, 'price_500g': 390, 'price_1kg': 750}),
            content_type='application/json'
        )
        self.assertEqual(valid_update.status_code, 200)
        res_data = valid_update.get_json()
        self.assertTrue(res_data['success'])
        self.assertEqual(res_data['price_250g'], 210)
        self.assertEqual(res_data['price_500g'], 390)
        self.assertEqual(res_data['price_1kg'], 750)

        # 6. Verify public store reflects new prices
        store_res = self.client.get('/product/satara-kandi-pedha')
        self.assertEqual(store_res.status_code, 200)
        self.assertIn(b'210', store_res.data)
        self.assertIn(b'390', store_res.data)
        self.assertIn(b'750', store_res.data)

        # Restore original price
        self.client.post('/api/admin/product/satara-kandi-pedha/update-prices',
            data=json.dumps({'price_250g': 180, 'price_500g': 340, 'price_1kg': 650}),
            content_type='application/json'
        )

    def test_13_checkout_renders_razorpay_checkout_js_and_options(self):
        resp = self.client.get('/checkout')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'checkout.razorpay.com/v1/checkout.js', resp.data)
        self.assertIn(b'Online Payment via Razorpay', resp.data)
        self.assertIn(b'razorpay.me/@shashanksanjaypawar', resp.data)

    def test_14_server_side_price_tampering_defense(self):
        # Client tries to forge price to ₹1 instead of real price
        conn = get_db()
        prod = conn.execute("SELECT price_500g FROM products WHERE id = 'satara-kandi-pedha'").fetchone()
        conn.close()
        real_price = prod['price_500g']

        tampered_order = {
            'customer': {
                'name': 'Tamper Test User',
                'phone': '9999999999',
                'email': 'tamper@example.com',
                'address1': 'Fake Lane 1',
                'city': 'Satara',
                'state': 'Maharashtra',
                'pincode': '415001'
            },
            'delivery': {
                'type': 'standard',
                'fee': 60,
                'date': '2026-09-20',
                'slot': 'Standard'
            },
            'payment': {
                'method': 'cod'
            },
            'items': [
                {
                    'product_id': 'satara-kandi-pedha',
                    'name': 'Satara Special Kandi Pedha',
                    'price': 1,  # FAKE/FORGED PRICE PASSED BY TAMPERING CLIENT
                    'weight': '500g',
                    'quantity': 2,
                    'is_custom_box': False
                }
            ]
        }

        resp = self.client.post('/api/orders',
            data=json.dumps(tampered_order),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        
        # Expected total must be based on server-side real_price * 2
        expected_subtotal = real_price * 2
        expected_delivery = 60 if expected_subtotal < 799 else 0
        expected_total = expected_subtotal + expected_delivery
        self.assertEqual(data['total_amount'], expected_total)
        self.assertNotEqual(data['total_amount'], 2 + 60)

    def test_15_razorpay_order_creation_and_verification(self):
        order_data = {
            'customer': {
                'name': 'Rohan Patil',
                'phone': '9876543210',
                'email': 'rohan@example.com',
                'address1': 'Station Road',
                'city': 'Satara',
                'state': 'Maharashtra',
                'pincode': '415001'
            },
            'delivery': {'fee': 0},
            'payment': {'method': 'razorpay'},
            'items': [{'product_id': 'satara-kandi-pedha', 'weight': '500g', 'quantity': 1}]
        }

        # 1. Test missing credentials guard
        with patch('app.RAZORPAY_KEY_ID', ''), patch('app.RAZORPAY_KEY_SECRET', ''):
            resp = self.client.post('/api/payments/razorpay/create-order',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 500)
            self.assertIn('credentials not configured', resp.get_json()['error'])

        # 2. Test successful Razorpay order creation with mock gateway client
        test_secret = 'test_secret_key_12345'
        test_key_id = 'rzp_test_samplekey123'
        
        mock_client = MagicMock()
        mock_client.order.create.return_value = {'id': 'order_fake_rzp_12345'}
        # Utility signature check can raise error or pass
        def mock_verify_payment(params):
            expected = hmac.new(
                test_secret.encode('utf-8'),
                f"{params['razorpay_order_id']}|{params['razorpay_payment_id']}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, params['razorpay_signature']):
                raise Exception("Signature mismatch")
        mock_client.utility.verify_payment_signature.side_effect = mock_verify_payment

        with patch('app.RAZORPAY_KEY_ID', test_key_id), \
             patch('app.RAZORPAY_KEY_SECRET', test_secret), \
             patch('app.get_razorpay_client', return_value=mock_client):

            resp = self.client.post('/api/payments/razorpay/create-order',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 200)
            res_data = resp.get_json()
            self.assertTrue(res_data['success'])
            self.assertEqual(res_data['razorpay_order_id'], 'order_fake_rzp_12345')
            self.assertEqual(res_data['currency'], 'INR')
            self.assertEqual(res_data['key_id'], test_key_id)
            self.assertGreater(res_data['amount'], 0) # In subunit paise
            
            internal_order_id = res_data['order_id']

            # 3. Test Signature Verification - Tampered/Invalid Signature
            bad_verify_resp = self.client.post('/api/payments/razorpay/verify',
                data=json.dumps({
                    'order_id': internal_order_id,
                    'razorpay_payment_id': 'pay_fake_999',
                    'razorpay_order_id': 'order_fake_rzp_12345',
                    'razorpay_signature': 'invalid_signature_hash'
                }),
                content_type='application/json'
            )
            self.assertEqual(bad_verify_resp.status_code, 400)
            self.assertFalse(bad_verify_resp.get_json()['success'])

            # Verify order status in DB was set to Failed
            conn = get_db()
            ord_row = conn.execute("SELECT payment_status FROM orders WHERE id = ?", (internal_order_id,)).fetchone()
            self.assertEqual(ord_row['payment_status'], 'Failed')
            conn.close()

            # 4. Test Signature Verification - Valid HMAC-SHA256
            valid_payload = "order_fake_rzp_12345|pay_fake_999"
            valid_sig = hmac.new(test_secret.encode('utf-8'), valid_payload.encode('utf-8'), hashlib.sha256).hexdigest()

            good_verify_resp = self.client.post('/api/payments/razorpay/verify',
                data=json.dumps({
                    'order_id': internal_order_id,
                    'razorpay_payment_id': 'pay_fake_999',
                    'razorpay_order_id': 'order_fake_rzp_12345',
                    'razorpay_signature': valid_sig
                }),
                content_type='application/json'
            )
            self.assertEqual(good_verify_resp.status_code, 200)
            self.assertTrue(good_verify_resp.get_json()['success'])

            # Verify order in DB marked as Confirmed and Paid
            conn = get_db()
            ord_row = conn.execute("SELECT status, payment_status, razorpay_payment_id FROM orders WHERE id = ?", (internal_order_id,)).fetchone()
            self.assertEqual(ord_row['status'], 'Confirmed')
            self.assertEqual(ord_row['payment_status'], 'Paid')
            self.assertEqual(ord_row['razorpay_payment_id'], 'pay_fake_999')
            conn.close()

    def test_16_razorpay_webhook_processing(self):
        test_secret = 'test_webhook_secret_777'
        
        # Create a pending order in DB
        conn = get_db()
        cursor = conn.cursor()
        order_id = 'ORD-WH-TEST-001'
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                delivery_date, delivery_slot, payment_method, payment_status,
                subtotal, delivery_fee, discount, total_amount, status, razorpay_order_id
            )
            VALUES (?, 'WH Customer', '9876543210', 'wh@example.com',
                'Line 1', 'Satara', 'Maharashtra', '415001', 'standard',
                '2026-09-21', 'Standard', 'razorpay', 'Payment Initiated',
                400, 0, 0, 400, 'Pending', 'order_wh_rzp_888')
        """, (order_id,))
        conn.commit()
        conn.close()

        webhook_payload = {
            'event': 'order.paid',
            'payload': {
                'order': {'entity': {'id': 'order_wh_rzp_888', 'receipt': order_id}},
                'payment': {'entity': {'id': 'pay_wh_rzp_999', 'order_id': 'order_wh_rzp_888'}}
            }
        }
        webhook_body = json.dumps(webhook_payload)
        valid_wh_sig = hmac.new(test_secret.encode('utf-8'), webhook_body.encode('utf-8'), hashlib.sha256).hexdigest()

        with patch('app.RAZORPAY_WEBHOOK_SECRET', test_secret), \
             patch('app.get_razorpay_client', return_value=None):

            # 1. Invalid signature rejection
            bad_resp = self.client.post('/api/payments/razorpay/webhook',
                data=webhook_body,
                headers={'X-Razorpay-Signature': 'invalid_webhook_sig', 'Content-Type': 'application/json'}
            )
            self.assertEqual(bad_resp.status_code, 400)

            # 2. Valid signature acceptance and idempotent status update
            good_resp = self.client.post('/api/payments/razorpay/webhook',
                data=webhook_body,
                headers={'X-Razorpay-Signature': valid_wh_sig, 'Content-Type': 'application/json'}
            )
            self.assertEqual(good_resp.status_code, 200)
            self.assertEqual(good_resp.get_json()['status'], 'ok')

        # Check order updated to Confirmed & Paid
        conn = get_db()
        ord_row = conn.execute("SELECT status, payment_status, razorpay_payment_id FROM orders WHERE id = ?", (order_id,)).fetchone()
        self.assertEqual(ord_row['status'], 'Confirmed')
        self.assertEqual(ord_row['payment_status'], 'Paid')
        self.assertEqual(ord_row['razorpay_payment_id'], 'pay_wh_rzp_999')
        conn.close()

    # ==================== SHIPROCKET TESTS ====================

    def test_17_shiprocket_service_token_and_weight(self):
        import shiprocket_service

        # 1. Test weight calculation
        items = [
            {'product_name': 'Kandi Pedha', 'weight_selected': '250g', 'quantity': 1},
            {'product_name': 'Kaju Katli', 'weight_selected': '500g', 'quantity': 2},
            {'product_name': 'Besan Laddu', 'weight_selected': '1kg', 'quantity': 1}
        ]
        # 0.25*1 + 0.5*2 + 1.0*1 = 2.25 kg + 0.1kg box tare = 2.35 kg
        self.assertEqual(shiprocket_service.calculate_order_weight(items), 2.35)

        # Minimum weight check (0.25kg + 0.1kg tare = 0.35kg, rounded up to 0.5kg min floor)
        min_items = [{'product_name': 'Kandi Pedha', 'weight_selected': '250g', 'quantity': 1}]
        self.assertEqual(shiprocket_service.calculate_order_weight(min_items), 0.5)

        # 2. Test token caching & auth
        shiprocket_service._token_cache['token'] = None
        shiprocket_service._token_cache['expires_at'] = 0

        mock_login_resp = MagicMock()
        mock_login_resp.status_code = 200
        mock_login_resp.json.return_value = {
            'token': 'mock_shiprocket_jwt_token_xyz',
            'expires_in': 864000
        }

        with patch.dict('os.environ', {'SHIPROCKET_EMAIL': 'admin@mamapedhewale.com', 'SHIPROCKET_PASSWORD': 'secret_password'}), \
             patch('requests.post', return_value=mock_login_resp) as mock_post:

            token1 = shiprocket_service.get_shiprocket_token()
            self.assertEqual(token1, 'mock_shiprocket_jwt_token_xyz')
            self.assertEqual(mock_post.call_count, 1)

            # Second call should use in-memory cache without extra HTTP call
            token2 = shiprocket_service.get_shiprocket_token()
            self.assertEqual(token2, 'mock_shiprocket_jwt_token_xyz')
            self.assertEqual(mock_post.call_count, 1)

    def test_18_shiprocket_order_creation_and_idempotency(self):
        import shiprocket_service

        order_dict = {
            'id': 'MP-SR-TEST-001',
            'customer_name': 'Anand Kulkarni',
            'customer_phone': '9822112233',
            'customer_email': 'anand@example.com',
            'address_line1': 'Plot 45, Shukrawar Peth',
            'city': 'Satara',
            'state': 'Maharashtra',
            'pincode': '415002',
            'payment_method': 'cod',
            'total_amount': 720
        }
        items = [{'product_name': 'Satara Pedha', 'weight_selected': '500g', 'quantity': 2, 'unit_price': 360}]

        mock_create_resp = {
            'order_id': 987654,
            'shipment_id': 123456,
            'status': 'NEW'
        }

        with patch.dict('os.environ', {'SHIPROCKET_PICKUP_LOCATION': 'Satara Warehouse'}), \
             patch('shiprocket_service.get_shiprocket_token', return_value='fake_jwt'), \
             patch('shiprocket_service.shiprocket_request', return_value=mock_create_resp):

            res = shiprocket_service.create_shiprocket_order(order_dict, items)
            self.assertTrue(res['success'])
            self.assertEqual(res['shiprocket_order_id'], '987654')
            self.assertEqual(res['shiprocket_shipment_id'], '123456')

            # Test Idempotency: when already created, it returns existing IDs without API call
            order_dict['shiprocket_order_id'] = '987654'
            order_dict['shiprocket_shipment_id'] = '123456'
            order_dict['shipment_status'] = 'Created'

            res_idem = shiprocket_service.create_shiprocket_order(order_dict, items)
            self.assertTrue(res_idem['success'])
            self.assertEqual(res_idem['shiprocket_order_id'], '987654')
            self.assertEqual(res_idem['message'], 'Shiprocket order already created.')

    def test_19_shiprocket_serviceability_awb_pickup_label(self):
        import shiprocket_service

        with patch('shiprocket_service.get_shiprocket_token', return_value='fake_jwt'):
            # 1. Serviceability
            mock_serv = {
                'data': {
                    'available_courier_companies': [
                        {'courier_company_id': 10, 'courier_name': 'Blue Dart Air', 'rate': 90.0, 'etd': '1-2 Days', 'rating': 4.8},
                        {'courier_company_id': 20, 'courier_name': 'Delhivery Surface', 'rate': 60.0, 'etd': '2-3 Days', 'rating': 4.6}
                    ]
                }
            }
            with patch('shiprocket_service.shiprocket_request', return_value=mock_serv):
                s_res = shiprocket_service.check_courier_serviceability('415003', '411001', 0.5)
                self.assertTrue(s_res['success'])
                self.assertEqual(s_res['count'], 2)
                # Sorted by rate ascending
                self.assertEqual(s_res['couriers'][0]['courier_name'], 'Delhivery Surface')

            # 2. Assign AWB
            mock_awb = {'response': {'data': {'awb_code': 'SR-AWB-998877', 'courier_name': 'Delhivery Surface'}}}
            with patch('shiprocket_service.shiprocket_request', return_value=mock_awb):
                a_res = shiprocket_service.assign_courier(123456, 20)
                self.assertTrue(a_res['success'])
                self.assertEqual(a_res['awb_code'], 'SR-AWB-998877')

            # 3. Schedule Pickup
            mock_pickup = {'message': 'Pickup scheduled for tomorrow'}
            with patch('shiprocket_service.shiprocket_request', return_value=mock_pickup):
                p_res = shiprocket_service.request_pickup(123456)
                self.assertTrue(p_res['success'])
                self.assertEqual(p_res['pickup_status'], 'Scheduled')

            # 4. Generate Label
            mock_label = {'label_url': 'https://shiprocket.co/labels/sample.pdf'}
            with patch('shiprocket_service.shiprocket_request', return_value=mock_label):
                l_res = shiprocket_service.generate_label(123456)
                self.assertTrue(l_res['success'])
                self.assertEqual(l_res['label_url'], 'https://shiprocket.co/labels/sample.pdf')

    def test_20_admin_shipping_create_endpoint(self):
        # 1. Create a test order in DB
        conn = get_db()
        cursor = conn.cursor()
        order_id = 'ORD-SR-ADMIN-001'
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                delivery_date, delivery_slot, payment_method, payment_status,
                subtotal, delivery_fee, discount, total_amount, status
            )
            VALUES (?, 'Vijay Patil', '9988776655', 'vijay@example.com',
                'Sadashiv Peth', 'Pune', 'Maharashtra', '411030', 'standard',
                '2026-09-25', 'Standard', 'razorpay', 'Payment Initiated',
                600, 0, 0, 600, 'Pending')
        """, (order_id,))
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, weight_selected, quantity, unit_price, item_total)
            VALUES (?, 'satara-kandi-pedha', 'Satara Kandi Pedha', '500g', 1, 600, 600)
        """, (order_id,))
        conn.commit()
        conn.close()

        # 2. Test 401 Unauthorized without session
        with self.client.session_transaction() as sess:
            sess.clear()
        unauth_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/create')
        self.assertEqual(unauth_resp.status_code, 401)

        # 3. Test 400 when order is unverified (Payment Initiated, not Paid)
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        with patch('shiprocket_service.is_configured', return_value=True):
            bad_pay_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/create')
            self.assertEqual(bad_pay_resp.status_code, 400)
            self.assertIn('cannot be created for unpaid order', bad_pay_resp.get_json()['error'])

        # 4. Mark order as Paid and test successful shipment creation
        conn = get_db()
        conn.execute("UPDATE orders SET payment_status = 'Paid', status = 'Confirmed' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()

        mock_sr_create = {
            'success': True,
            'shiprocket_order_id': '887766',
            'shiprocket_shipment_id': '554433',
            'status': 'NEW'
        }

        with patch('shiprocket_service.is_configured', return_value=True), \
             patch('shiprocket_service.create_shiprocket_order', return_value=mock_sr_create):

            create_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/create')
            self.assertEqual(create_resp.status_code, 200)
            res_data = create_resp.get_json()
            self.assertTrue(res_data['success'])
            self.assertEqual(res_data['shiprocket_order_id'], '887766')
            self.assertEqual(res_data['shiprocket_shipment_id'], '554433')

        # Verify DB updated
        conn = get_db()
        ord_db = conn.execute("SELECT shiprocket_order_id, shiprocket_shipment_id FROM orders WHERE id = ?", (order_id,)).fetchone()
        self.assertEqual(ord_db['shiprocket_order_id'], '887766')
        self.assertEqual(ord_db['shiprocket_shipment_id'], '554433')
        conn.close()

    def test_21_admin_shipping_workflow_endpoints(self):
        order_id = 'ORD-SR-WORKFLOW-001'
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                payment_method, payment_status, subtotal, delivery_fee,
                total_amount, status, shiprocket_order_id, shiprocket_shipment_id
            )
            VALUES (?, 'Sunil Jadhav', '9822334455', 'sunil@example.com',
                'Rajwada', 'Satara', 'Maharashtra', '415001', 'standard',
                'cod', 'Pending', 500, 0, 500, 'Confirmed', '991122', '334455')
        """, (order_id,))
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, weight_selected, quantity, unit_price, item_total)
            VALUES (?, 'satara-kandi-pedha', 'Satara Kandi Pedha', '500g', 1, 500, 500)
        """, (order_id,))
        conn.commit()
        conn.close()

        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        with patch('shiprocket_service.is_configured', return_value=True):
            # 1. Serviceability
            with patch('shiprocket_service.check_courier_serviceability', return_value={'success': True, 'couriers': [{'courier_name': 'Delhivery', 'rate': 55.0}]}):
                serv_resp = self.client.get(f'/api/admin/orders/{order_id}/shipping/serviceability')
                self.assertEqual(serv_resp.status_code, 200)
                self.assertTrue(serv_resp.get_json()['success'])

            # 2. Assign Courier
            with patch('shiprocket_service.assign_courier', return_value={'success': True, 'awb_code': 'AWB-TEST-7788', 'courier_name': 'Delhivery'}):
                assign_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/assign-courier',
                    data=json.dumps({'courier_id': 10}),
                    content_type='application/json')
                self.assertEqual(assign_resp.status_code, 200)
                self.assertEqual(assign_resp.get_json()['awb_code'], 'AWB-TEST-7788')

            # 3. Schedule Pickup
            with patch('shiprocket_service.request_pickup', return_value={'success': True, 'message': 'Pickup booked'}):
                pickup_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/pickup')
                self.assertEqual(pickup_resp.status_code, 200)

            # 4. Generate Label
            with patch('shiprocket_service.generate_label', return_value={'success': True, 'label_url': 'https://sr.co/label.pdf'}):
                label_resp = self.client.post(f'/api/admin/orders/{order_id}/shipping/label')
                self.assertEqual(label_resp.status_code, 200)
                self.assertEqual(label_resp.get_json()['label_url'], 'https://sr.co/label.pdf')

            # 5. Track
            with patch('shiprocket_service.track_shipment', return_value={'success': True, 'current_status': 'In Transit', 'awb_code': 'AWB-TEST-7788'}):
                track_resp = self.client.get(f'/api/admin/orders/{order_id}/shipping/track')
                self.assertEqual(track_resp.status_code, 200)
                self.assertEqual(track_resp.get_json()['tracking']['current_status'], 'In Transit')

    def test_22_public_shipping_track_endpoint(self):
        order_id = 'ORD-SR-PUB-001'
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, address_line1, city, state, pincode,
                payment_method, payment_status, subtotal, delivery_fee, total_amount,
                status, awb_code, courier_name, shipment_status, tracking_url
            )
            VALUES (?, 'Customer A', '9876543210', 'Street 1', 'Satara', 'Maharashtra', '415001',
                'cod', 'Pending', 300, 0, 300, 'Dispatched', 'AWB-PUB-1234', 'Blue Dart', 'In Transit',
                'https://shiprocket.co/tracking/AWB-PUB-1234')
        """, (order_id,))
        conn.commit()
        conn.close()

        resp = self.client.get(f'/api/shipping/track/{order_id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['awb_code'], 'AWB-PUB-1234')
        self.assertEqual(data['courier_name'], 'Blue Dart')
        self.assertEqual(data['shipment_status'], 'In Transit')

    def test_23_shiprocket_webhook_processing(self):
        order_id = 'ORD-SR-WH-COD-001'
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, address_line1, city, state, pincode,
                payment_method, payment_status, subtotal, delivery_fee, total_amount,
                status, shiprocket_shipment_id
            )
            VALUES (?, 'COD Customer', '9876543210', 'Camp', 'Satara', 'Maharashtra', '415001',
                'cod', 'Pending', 450, 0, 450, 'Confirmed', 'SR-SHIP-999')
        """, (order_id,))
        conn.commit()
        conn.close()

        wh_secret = 'whsec_test_secret_123'

        # 1. Test IN TRANSIT webhook event via primary endpoint /api/shipping/webhook
        wh_transit_payload = {
            'order_id': order_id,
            'shipment_id': 'SR-SHIP-999',
            'awb': 'AWB-WH-999',
            'courier_name': 'Delhivery',
            'current_status': 'IN TRANSIT'
        }

        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_SECRET': wh_secret}):
            transit_resp = self.client.post('/api/shipping/webhook',
                data=json.dumps(wh_transit_payload),
                headers={'x-api-key': wh_secret},
                content_type='application/json')
            self.assertEqual(transit_resp.status_code, 200)

            conn = get_db()
            ord_db = conn.execute("SELECT status, shipment_status, awb_code, courier_name, payment_status FROM orders WHERE id = ?", (order_id,)).fetchone()
            self.assertEqual(ord_db['status'], 'Dispatched')
            self.assertEqual(ord_db['shipment_status'], 'In Transit')
            self.assertEqual(ord_db['awb_code'], 'AWB-WH-999')
            self.assertEqual(ord_db['payment_status'], 'Pending')
            conn.close()

            # 2. Test DELIVERED webhook event via legacy alias /api/shipping/shiprocket/webhook
            # CRITICAL: Parcel delivery must NEVER mutate COD payment_status to 'Paid'
            wh_delivered_payload = {
                'order_id': order_id,
                'current_status': 'DELIVERED'
            }

            deliv_resp = self.client.post('/api/shipping/shiprocket/webhook',
                data=json.dumps(wh_delivered_payload),
                headers={'x-api-key': wh_secret},
                content_type='application/json')
            self.assertEqual(deliv_resp.status_code, 200)

            conn = get_db()
            ord_deliv = conn.execute("SELECT status, payment_status, shipment_status FROM orders WHERE id = ?", (order_id,)).fetchone()
            self.assertEqual(ord_deliv['status'], 'Delivered')
            self.assertEqual(ord_deliv['shipment_status'], 'Delivered')
            self.assertEqual(ord_deliv['payment_status'], 'Pending')
            conn.close()

    def test_24_safe_checkout_without_shiprocket(self):
        # Verify that customer checkout succeeds even if Shiprocket is not configured or throws error
        order_payload = {
            'customer': {
                'name': 'Ganesh Gaikwad',
                'phone': '9890123456',
                'email': 'ganesh@example.com',
                'address1': 'Shivaji Nagar',
                'city': 'Satara',
                'state': 'Maharashtra',
                'pincode': '415001'
            },
            'delivery': {'type': 'standard', 'fee': 0},
            'payment': {'method': 'cod'},
            'items': [{'product_id': 'satara-kandi-pedha', 'name': 'Satara Kandi Pedha', 'weight': '500g', 'quantity': 1}]
        }

        with patch('shiprocket_service.is_configured', return_value=False):
            resp = self.client.post('/api/orders',
                data=json.dumps(order_payload),
                content_type='application/json')
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.get_json()['success'])

    def test_25_admin_shipping_details_endpoint(self):
        # 1. Verify unauthorized access without admin login
        unauth_client = app.test_client()
        unauth_resp = unauth_client.get('/api/admin/orders/TEST-ORD-1/shipping/details')
        self.assertEqual(unauth_resp.status_code, 401)

        # Create an order
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO orders (
                id, customer_name, customer_phone, customer_email, address_line1,
                city, state, pincode, delivery_type, delivery_date, delivery_slot,
                payment_method, payment_status, subtotal, delivery_fee, discount,
                total_amount, status, shiprocket_order_id, shiprocket_shipment_id,
                awb_code, courier_name, shipment_status, label_url, invoice_url
            ) VALUES (
                'MP-TEST-DETAILS-1', 'Sunita Joshi', '9822334455', 'sunita@example.com', 'Koregaon Park',
                'Pune', 'Maharashtra', '411001', 'standard', '2026-10-10', 'Standard',
                'upi', 'Paid', 720, 0, 0, 720, 'Confirmed', 'SR-ORD-777', 'SR-SHIP-777',
                'AWB-777888', 'Blue Dart Express', 'AWB Assigned', 'https://sr.co/label.pdf', 'https://sr.co/inv.pdf'
            )
        """)
        conn.commit()
        conn.close()

        # 2. Authenticate as admin
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        resp = self.client.get('/api/admin/orders/MP-TEST-DETAILS-1/shipping/details')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['order_id'], 'MP-TEST-DETAILS-1')
        self.assertEqual(data['shiprocket_order_id'], 'SR-ORD-777')
        self.assertEqual(data['shiprocket_shipment_id'], 'SR-SHIP-777')
        self.assertEqual(data['awb_code'], 'AWB-777888')
        self.assertEqual(data['courier_name'], 'Blue Dart Express')
        self.assertEqual(data['shipment_status'], 'AWB Assigned')
        self.assertEqual(data['label_url'], 'https://sr.co/label.pdf')
        self.assertEqual(data['invoice_url'], 'https://sr.co/inv.pdf')
        self.assertEqual(data['payment_status'], 'Paid')
        self.assertEqual(data['payment_method'], 'upi')

    def test_26_customer_public_track_enhanced(self):
        resp = self.client.get('/api/shipping/track/MP-TEST-DETAILS-1')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['order_id'], 'MP-TEST-DETAILS-1')
        self.assertEqual(data['payment_status'], 'Paid')
        self.assertEqual(data['payment_method'], 'upi')
        self.assertEqual(data['awb_code'], 'AWB-777888')
        self.assertEqual(data['courier_name'], 'Blue Dart Express')
        self.assertTrue(data['has_shipment'])
        self.assertEqual(data['city'], 'Pune')
        self.assertEqual(data['pincode'], '411001')
        # Ensure credentials / sensitive tokens are not exposed
        self.assertNotIn('token', data)
        self.assertNotIn('password', data)
        self.assertNotIn('email', data)

    def test_27_track_order_ui_and_order_success_ui(self):
        # 1. Track Order Page renders 7-stage shipping timeline and shipment summary
        resp = self.client.get('/track-order?order_id=MP-TEST-DETAILS-1')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('Shipment Summary &amp; Courier Details', html)
        self.assertIn('Order Confirmed', html)
        self.assertIn('Payment Confirmed', html)
        self.assertIn('Shipment Created', html)
        self.assertIn('Picked Up', html)
        self.assertIn('In Transit', html)
        self.assertIn('Out for Delivery', html)
        self.assertIn('Delivered', html)
        self.assertIn('Refresh Live Status', html)

        # 2. Order Success Page renders payment vs shipping summary card
        success_resp = self.client.get('/order-success/MP-TEST-DETAILS-1')
        self.assertEqual(success_resp.status_code, 200)
        success_html = success_resp.data.decode('utf-8')
        self.assertIn('Order Reference', success_html)
        self.assertIn('Payment', success_html)
        self.assertIn('Shipping', success_html)
        self.assertIn('Track Order &rarr;', success_html)

    def test_28_shiprocket_pickup_location_validation(self):
        import shiprocket_service
        from shiprocket_service import ShiprocketConfigError

        order_dict = {
            'id': 'MP-SR-VALIDATE-001',
            'customer_name': 'Validation User',
            'customer_phone': '9822112233',
            'customer_email': 'val@example.com',
            'address_line1': '101 Station Road',
            'city': 'Satara',
            'state': 'Maharashtra',
            'pincode': '415001',
            'payment_method': 'cod',
            'total_amount': 500
        }
        items = [{'product_name': 'Satara Pedha', 'weight_selected': '500g', 'quantity': 1, 'unit_price': 500}]

        # Without SHIPROCKET_PICKUP_LOCATION set, create_shiprocket_order MUST raise ShiprocketConfigError
        with patch.dict('os.environ', {'SHIPROCKET_PICKUP_LOCATION': ''}):
            with self.assertRaises(ShiprocketConfigError):
                shiprocket_service.create_shiprocket_order(order_dict, items)

    def test_29_shiprocket_webhook_security_and_rejections(self):
        wh_payload = {
            'order_id': 'MP-TEST-DETAILS-1',
            'current_status': 'IN TRANSIT'
        }

        # 1. Secret not configured on server -> 401
        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_SECRET': ''}):
            resp = self.client.post('/api/shipping/webhook',
                data=json.dumps(wh_payload),
                headers={'x-api-key': 'some_key'},
                content_type='application/json')
            self.assertEqual(resp.status_code, 401)
            self.assertIn('Webhook secret not configured', resp.get_json()['error'])

        # 2. Missing x-api-key header when secret is configured -> 401
        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_SECRET': 'my_prod_secret'}):
            resp = self.client.post('/api/shipping/webhook',
                data=json.dumps(wh_payload),
                content_type='application/json')
            self.assertEqual(resp.status_code, 401)
            self.assertIn('Unauthorized', resp.get_json()['error'])

            # 3. Wrong x-api-key header -> 401
            resp_wrong = self.client.post('/api/shipping/webhook',
                data=json.dumps(wh_payload),
                headers={'x-api-key': 'wrong_secret_123'},
                content_type='application/json')
            self.assertEqual(resp_wrong.status_code, 401)

            # 4. Valid x-api-key header -> 200
            resp_ok = self.client.post('/api/shipping/webhook',
                data=json.dumps(wh_payload),
                headers={'x-api-key': 'my_prod_secret'},
                content_type='application/json')
            self.assertEqual(resp_ok.status_code, 200)

    def test_30_no_fake_courier_fallbacks(self):
        import shiprocket_service

        # 1. assign_courier returns None for courier_name if API response doesn't provide one
        mock_awb_resp = {'awb_assign_status': 1, 'response': {'data': {'awb_code': 'AWB-TEST-REAL'}}}
        with patch('shiprocket_service.get_shiprocket_token', return_value='fake_jwt'), \
             patch('shiprocket_service.shiprocket_request', return_value=mock_awb_resp):
            res = shiprocket_service.assign_courier('12345')
            self.assertIsNone(res['courier_name'])
            self.assertNotEqual(res.get('courier_name'), 'Shiprocket Express Partner')

        # 2. track_shipment returns None for courier_name if unassigned
        mock_track_resp = {'tracking_data': {'track_status': 1, 'shipment_status': 'In Transit'}}
        with patch('shiprocket_service.get_shiprocket_token', return_value='fake_jwt'), \
             patch('shiprocket_service.shiprocket_request', return_value=mock_track_resp):
            t_res = shiprocket_service.track_shipment('12345')
            self.assertIsNone(t_res['courier_name'])
            self.assertNotEqual(t_res.get('courier_name'), 'Shiprocket Express')

        # 3. Newly created order has NULL courier_name, not 'Mama Fresh Express'
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = 'TEST-COURIER-NULL'")
        cursor.execute("""
            INSERT INTO orders (id, customer_name, customer_phone, address_line1, city, state, pincode, payment_method, total_amount, subtotal, delivery_fee)
            VALUES ('TEST-COURIER-NULL', 'User', '9999999999', 'Road', 'Satara', 'MH', '415001', 'cod', 300, 300, 0)
        """)
        conn.commit()
        ord_row = cursor.execute("SELECT courier_name FROM orders WHERE id = 'TEST-COURIER-NULL'").fetchone()
        self.assertIsNone(ord_row['courier_name'])
        conn.close()

    def test_31_package_weight_and_dimension_calculation(self):
        import shiprocket_service

        # Verify package dimensions constants
        self.assertEqual(shiprocket_service.DEFAULT_PACKAGE_LENGTH, 15.0)
        self.assertEqual(shiprocket_service.DEFAULT_PACKAGE_BREADTH, 15.0)
        self.assertEqual(shiprocket_service.DEFAULT_PACKAGE_HEIGHT, 10.0)
        self.assertEqual(shiprocket_service.MIN_WEIGHT_KG, 0.5)

        # 1kg item + 0.1kg tare = 1.1kg dead weight
        items_1kg = [{'product_name': 'Satara Pedha', 'weight_selected': '1kg', 'quantity': 1}]
        self.assertEqual(shiprocket_service.calculate_order_weight(items_1kg), 1.1)

        # 250g item (0.25kg) + 0.1kg tare = 0.35kg -> rounded up to MIN_WEIGHT_KG (0.5kg)
        items_small = [{'product_name': 'Satara Pedha', 'weight_selected': '250g', 'quantity': 1}]
        self.assertEqual(shiprocket_service.calculate_order_weight(items_small), 0.5)

    def test_32_end_to_end_razorpay_to_shiprocket_and_awb(self):
        # 1. Create a pending Razorpay order in DB
        conn = get_db()
        cursor = conn.cursor()
        order_id = 'MP-E2E-TEST-001'
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                delivery_date, delivery_slot, payment_method, payment_status,
                subtotal, delivery_fee, discount, total_amount, status, razorpay_order_id
            )
            VALUES (?, 'Mahesh Shinde', '9822001122', 'mahesh@example.com',
                '505 Bhavani Peth', 'Pune', 'Maharashtra', '411042', 'standard',
                '2026-10-15', 'Standard', 'razorpay', 'Payment Initiated',
                750, 0, 0, 750, 'Pending', 'order_e2e_rzp_123')
        """, (order_id,))
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, weight_selected, quantity, unit_price, item_total)
            VALUES (?, 'satara-kandi-pedha', 'Satara Kandi Pedha', '500g', 1, 750, 750)
        """, (order_id,))
        conn.commit()
        conn.close()

        test_secret = 'rzp_sec_e2e_7788'
        valid_payload = "order_e2e_rzp_123|pay_e2e_999"
        valid_sig = hmac.new(test_secret.encode('utf-8'), valid_payload.encode('utf-8'), hashlib.sha256).hexdigest()

        mock_sr_create = {
            'success': True,
            'shiprocket_order_id': 'SR-E2E-ORD-1',
            'shiprocket_shipment_id': 'SR-E2E-SHIP-1',
            'status': 'NEW'
        }
        mock_sr_awb = {
            'success': True,
            'awb_code': 'AWB-E2E-99999',
            'courier_name': 'Delhivery Surface',
            'courier_company_id': '20',
            'tracking_url': 'https://shiprocket.co/tracking/AWB-E2E-99999'
        }

        with patch('app.RAZORPAY_KEY_SECRET', test_secret), \
             patch('app.get_razorpay_client', return_value=None), \
             patch('shiprocket_service.is_configured', return_value=True), \
             patch('shiprocket_service.create_shiprocket_order', return_value=mock_sr_create) as mock_create_call, \
             patch('shiprocket_service.assign_courier', return_value=mock_sr_awb) as mock_assign_call:

            verify_resp = self.client.post('/api/payments/razorpay/verify',
                data=json.dumps({
                    'order_id': order_id,
                    'razorpay_payment_id': 'pay_e2e_999',
                    'razorpay_order_id': 'order_e2e_rzp_123',
                    'razorpay_signature': valid_sig
                }),
                content_type='application/json'
            )
            self.assertEqual(verify_resp.status_code, 200)
            self.assertTrue(verify_resp.get_json()['success'])
            self.assertEqual(mock_create_call.call_count, 1)
            self.assertEqual(mock_assign_call.call_count, 1)

        # Verify DB is updated with payment status Paid AND Shiprocket order + AWB details
        conn = get_db()
        ord_db = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        self.assertEqual(ord_db['payment_status'], 'Paid')
        self.assertEqual(ord_db['status'], 'Confirmed')
        self.assertEqual(ord_db['shiprocket_order_id'], 'SR-E2E-ORD-1')
        self.assertEqual(ord_db['shiprocket_shipment_id'], 'SR-E2E-SHIP-1')
        self.assertEqual(ord_db['awb_code'], 'AWB-E2E-99999')
        self.assertEqual(ord_db['courier_name'], 'Delhivery Surface')
        self.assertEqual(ord_db['courier_company_id'], '20')
        self.assertEqual(ord_db['shipment_status'], 'AWB Assigned')
        self.assertIsNotNone(ord_db['awb_assigned_at'])
        conn.close()

    def test_33_shiprocket_idempotency_and_safe_fallback(self):
        # 1. Fallback Test: If Shiprocket API raises an exception during payment verification,
        # payment verification MUST succeed, order MUST remain 'Paid', and shipment_status must be 'Shipment Pending'
        conn = get_db()
        cursor = conn.cursor()
        order_id = 'MP-FALLBACK-TEST-001'
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                delivery_date, delivery_slot, payment_method, payment_status,
                subtotal, delivery_fee, discount, total_amount, status, razorpay_order_id
            )
            VALUES (?, 'Suresh Deshmukh', '9822003344', 'suresh@example.com',
                '22 Karve Road', 'Pune', 'Maharashtra', '411004', 'standard',
                '2026-10-16', 'Standard', 'razorpay', 'Payment Initiated',
                500, 0, 0, 500, 'Pending', 'order_fb_rzp_456')
        """, (order_id,))
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, weight_selected, quantity, unit_price, item_total)
            VALUES (?, 'satara-kandi-pedha', 'Satara Kandi Pedha', '500g', 1, 500, 500)
        """, (order_id,))
        conn.commit()
        conn.close()

        test_secret = 'rzp_sec_fb_9900'
        valid_payload = "order_fb_rzp_456|pay_fb_111"
        valid_sig = hmac.new(test_secret.encode('utf-8'), valid_payload.encode('utf-8'), hashlib.sha256).hexdigest()

        with patch('app.RAZORPAY_KEY_SECRET', test_secret), \
             patch('app.get_razorpay_client', return_value=None), \
             patch('shiprocket_service.is_configured', return_value=True), \
             patch('shiprocket_service.create_shiprocket_order', side_effect=Exception("Shiprocket network timeout")):

            verify_resp = self.client.post('/api/payments/razorpay/verify',
                data=json.dumps({
                    'order_id': order_id,
                    'razorpay_payment_id': 'pay_fb_111',
                    'razorpay_order_id': 'order_fb_rzp_456',
                    'razorpay_signature': valid_sig
                }),
                content_type='application/json'
            )
            # Payment verification must NOT crash or fail
            self.assertEqual(verify_resp.status_code, 200)
            self.assertTrue(verify_resp.get_json()['success'])

        # Verify DB: Payment is Paid, order is Confirmed, shipment_status is Shipment Pending
        conn = get_db()
        ord_db = conn.execute("SELECT payment_status, status, shipment_status FROM orders WHERE id = ?", (order_id,)).fetchone()
        self.assertEqual(ord_db['payment_status'], 'Paid')
        self.assertEqual(ord_db['status'], 'Confirmed')
        self.assertEqual(ord_db['shipment_status'], 'Shipment Pending')
        conn.close()

        # 2. Idempotency Test: If order already has shiprocket_order_id and awb_code,
        # calling trigger_shiprocket_order_creation_safe again does NOT re-call Shiprocket APIs
        conn = get_db()
        conn.execute("""
            UPDATE orders 
            SET shiprocket_order_id = 'SR-EXISTING-1',
                shiprocket_shipment_id = 'SR-EXISTING-SHIP-1',
                awb_code = 'AWB-EXISTING-1',
                shipment_status = 'AWB Assigned'
            WHERE id = ?
        """, (order_id,))
        conn.commit()
        conn.close()

        with patch('shiprocket_service.is_configured', return_value=True), \
             patch('shiprocket_service.create_shiprocket_order') as mock_create, \
             patch('shiprocket_service.assign_courier') as mock_assign:
            from app import trigger_shiprocket_order_creation_safe
            result = trigger_shiprocket_order_creation_safe(order_id)
            self.assertIsNotNone(result)
            self.assertEqual(result['shiprocket_order_id'], 'SR-EXISTING-1')
            self.assertEqual(result['awb_code'], 'AWB-EXISTING-1')
            self.assertEqual(mock_create.call_count, 0)
            self.assertEqual(mock_assign.call_count, 0)

    def test_34_shiprocket_webhook_timestamps_and_isolation(self):
        conn = get_db()
        cursor = conn.cursor()
        order_id = 'ORD-SR-WH-TIME-001'
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, address_line1, city, state, pincode,
                payment_method, payment_status, subtotal, delivery_fee, total_amount,
                status, shiprocket_shipment_id
            )
            VALUES (?, 'Timestamp Test', '9876543210', 'Camp', 'Satara', 'Maharashtra', '415001',
                'razorpay', 'Paid', 450, 0, 450, 'Confirmed', 'SR-SHIP-TIME-1')
        """, (order_id,))
        conn.commit()
        conn.close()

        wh_secret = 'whsec_timestamp_secret'

        # 1. Shipped webhook
        payload_shipped = {
            'order_id': order_id,
            'shipment_id': 'SR-SHIP-TIME-1',
            'awb': 'AWB-TIME-1',
            'courier_name': 'Delhivery',
            'courier_company_id': '20',
            'current_status': 'SHIPPED'
        }

        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_SECRET': wh_secret}):
            resp = self.client.post('/api/shipping/webhook',
                data=json.dumps(payload_shipped),
                headers={'x-api-key': wh_secret},
                content_type='application/json')
            self.assertEqual(resp.status_code, 200)

            conn = get_db()
            ord_row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            self.assertEqual(ord_row['shipment_status'], 'In Transit')
            self.assertEqual(ord_row['status'], 'Dispatched')
            self.assertEqual(ord_row['courier_company_id'], '20')
            self.assertIsNotNone(ord_row['awb_assigned_at'])
            self.assertIsNotNone(ord_row['shipped_at'])
            self.assertEqual(ord_row['payment_status'], 'Paid')
            conn.close()

            # 2. Delivered webhook
            payload_delivered = {
                'order_id': order_id,
                'current_status': 'DELIVERED'
            }
            resp_deliv = self.client.post('/api/shipping/webhook',
                data=json.dumps(payload_delivered),
                headers={'x-api-key': wh_secret},
                content_type='application/json')
            self.assertEqual(resp_deliv.status_code, 200)

            conn = get_db()
            ord_deliv = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            self.assertEqual(ord_deliv['shipment_status'], 'Delivered')
            self.assertEqual(ord_deliv['status'], 'Delivered')
            self.assertIsNotNone(ord_deliv['delivered_at'])
            self.assertEqual(ord_deliv['payment_status'], 'Paid')
            conn.close()

    def test_35_neutral_webhook_route_and_root_delegation(self):
        # 1. Test clean neutral route /api/webhooks/shipping with GET health check
        health_resp = self.client.get('/api/webhooks/shipping')
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.get_json()['status'], 'active')

        # 2. Test setup placeholder token 'SHIPROCKET_WEBHOOK_TOKEN' when env vars are unconfigured
        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_SECRET': '', 'SHIPROCKET_WEBHOOK_TOKEN': ''}):
            setup_resp = self.client.post('/api/webhooks/shipping',
                data=json.dumps({'test': True}),
                headers={'x-api-key': 'SHIPROCKET_WEBHOOK_TOKEN'},
                content_type='application/json')
            self.assertEqual(setup_resp.status_code, 200)
            self.assertEqual(setup_resp.get_json()['status'], 'ok')

        # 3. Test POST to root route '/' with x-api-key delegates safely to webhook
        with patch.dict('os.environ', {'SHIPROCKET_WEBHOOK_TOKEN': 'prod_token_8899'}):
            root_webhook_resp = self.client.post('/',
                data=json.dumps({'test': True}),
                headers={'x-api-key': 'prod_token_8899'},
                content_type='application/json')
            self.assertEqual(root_webhook_resp.status_code, 200)
            self.assertEqual(root_webhook_resp.get_json()['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
