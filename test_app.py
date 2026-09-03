import unittest
import json
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

if __name__ == '__main__':
    unittest.main()
