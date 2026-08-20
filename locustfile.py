# locustfile.py
from locust import HttpUser, task, between, SequentialTaskSet


class UserJourney(SequentialTaskSet):
    """
    Simulasi sequential user journey:
    1. GET all products
    2. GET a single product by ID
    3. POST a new order
    4. GET the created order
    """

    def on_start(self):
        """Register a test user for order creation."""
        import time
        self.email = f"locust_{time.time()}@test.com"
        res = self.client.post('/users', json={
            'username': 'locust_user',
            'email': self.email,
            'password': 'testpass123'
        })
        if res.status_code == 201:
            self.user_id = res.json()['id']
        else:
            self.user_id = 1

    @task
    def get_all_products(self):
        """Step 1: Browse all products"""
        self.client.get('/products', name='/products [GET all]')

    @task
    def get_single_product(self):
        """Step 2: View a single product"""
        self.client.get('/products/1', name='/products/<id> [GET one]')

    @task
    def create_order(self):
        """Step 3: Place an order"""
        res = self.client.post('/orders', json={
            'user_id': self.user_id,
            'items': [
                {'product_id': 1, 'quantity': 1},
                {'product_id': 2, 'quantity': 2}
            ]
        }, name='/orders [POST]')
        if res.status_code == 201:
            self.order_id = res.json()['id']
        else:
            self.order_id = 1

    @task
    def get_created_order(self):
        """Step 4: View the order just created"""
        self.client.get(f'/orders/{self.order_id}', name='/orders/<id> [GET one]')

    @task
    def stop(self):
        """End the journey and restart"""
        self.interrupt()


class RevoShopUser(HttpUser):
    """Simulated user with sequential journey."""
    tasks = [UserJourney]
    wait_time = between(1, 3)
    host = "http://localhost:5000"
