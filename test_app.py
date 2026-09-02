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

        # Verify admin status update
        update_resp = self.client.post(f'/api/admin/order/{order_id}/status',
            data=json.dumps({'status': 'Packed'}),
            content_type='application/json'
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertTrue(update_resp.get_json()['success'])

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

    def test_09_admin_toggle_stock(self):
        response = self.client.post('/api/admin/product/satara-kandi-pedha/toggle-stock')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

        # Toggle back
        response2 = self.client.post('/api/admin/product/satara-kandi-pedha/toggle-stock')
        self.assertTrue(response2.get_json()['in_stock'])

    def test_10_admin_page(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mama Pedhewale Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()
