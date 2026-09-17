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
        seed_database()
        cls.client = app.test_client()

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

if __name__ == '__main__':
    unittest.main()
