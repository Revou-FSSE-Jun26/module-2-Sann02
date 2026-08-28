# locustfile.py
import time
from locust import HttpUser, task, between, SequentialTaskSet


class UserJourney(SequentialTaskSet):
    """
    Simulasi sequential user journey (sesuai rubrik):
      1. GET all products
      2. GET a single product by ID
      3. POST a new order
      4. GET the created order

    Catatan desain: kita TIDAK meng-hardcode product_id. ID diambil
    secara dinamis dari respons GET /products supaya journey tetap valid
    walau data seed berubah — sesuai best practice load testing.
    """

    def on_start(self):
        """Setiap virtual user register akun sendiri untuk membuat order."""
        self.user_id = None
        self.product_id = None
        self.order_id = None

        email = f"locust_{time.time()}_{id(self)}@test.com"
        res = self.client.post('/users', json={
            'username': 'locust_user',
            'email': email,
            'password': 'testpass123'
        }, name='/users [POST register]')
        if res.status_code == 201:
            self.user_id = res.json().get('id')

    @task
    def get_all_products(self):
        """Step 1: Browse semua produk, simpan satu product_id yang valid."""
        with self.client.get('/products', name='/products [GET all]',
                             catch_response=True) as res:
            if res.status_code == 200:
                products = res.json()
                if products:
                    self.product_id = products[0]['id']
                    res.success()
                else:
                    res.failure('Product list kosong')
            else:
                res.failure(f'Expected 200, got {res.status_code}')

    @task
    def get_single_product(self):
        """Step 2: Lihat detail satu produk berdasarkan ID yang valid."""
        if self.product_id is None:
            return
        self.client.get(f'/products/{self.product_id}',
                        name='/products/<id> [GET one]')

    @task
    def create_order(self):
        """Step 3: Buat order untuk produk yang benar-benar ada."""
        if self.user_id is None or self.product_id is None:
            return
        with self.client.post('/orders', json={
            'user_id': self.user_id,
            'items': [{'product_id': self.product_id, 'quantity': 1}]
        }, name='/orders [POST]', catch_response=True) as res:
            if res.status_code == 201:
                self.order_id = res.json().get('id')
                res.success()
            else:
                res.failure(f'Expected 201, got {res.status_code}')

    @task
    def get_created_order(self):
        """Step 4: Lihat order yang baru dibuat (guard di balik POST sukses)."""
        if self.order_id is None:
            return
        self.client.get(f'/orders/{self.order_id}',
                        name='/orders/<id> [GET one]')

    @task
    def stop(self):
        """Akhiri journey lalu ulang dari awal."""
        self.interrupt()


class RevoShopUser(HttpUser):
    """Simulated user dengan sequential journey."""
    tasks = [UserJourney]
    wait_time = between(1, 3)
    host = "http://localhost:5000"
