# tests/test_products.py
"""
Test suite untuk Product CRUD endpoints.
Fokus pada aturan validasi (400 untuk bentuk salah, 422 untuk nilai negatif)
sesuai contoh assignment, plus happy path tiap operasi.
"""


def _make_category(client, name='Elektronik'):
    """Helper: buat satu category dan kembalikan id-nya (produk butuh category_id)."""
    res = client.post('/categories', json={'name': name, 'description': 'seed'})
    return res.get_json()['id']


class TestGetProducts:
    """GET /products dan /products/<id>"""

    def test_get_products_empty(self, client):
        res = client.get('/products')
        assert res.status_code == 200
        assert res.get_json() == []

    def test_get_product_not_found_returns_404(self, client):
        res = client.get('/products/999')
        assert res.status_code == 404
        assert 'not found' in res.get_json()['error'].lower()

    def test_get_product_by_id_success(self, client):
        cid = _make_category(client)
        created = client.post('/products', json={
            'name': 'Laptop', 'price': 15000000, 'category_id': cid
        }).get_json()

        res = client.get(f"/products/{created['id']}")
        assert res.status_code == 200
        assert res.get_json()['name'] == 'Laptop'


class TestCreateProduct:
    """POST /products"""

    def test_create_product_success(self, client):
        cid = _make_category(client)
        res = client.post('/products', json={
            'name': 'Mouse', 'price': 150000, 'category_id': cid, 'stock_quantity': 10
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['name'] == 'Mouse'
        assert data['price'] == 150000.0
        assert 'id' in data

    def test_create_product_missing_price_returns_400(self, client):
        cid = _make_category(client)
        res = client.post('/products', json={'name': 'NoPrice', 'category_id': cid})
        assert res.status_code == 400
        assert 'price' in res.get_json()['error'].lower()

    def test_create_product_empty_name_returns_400(self, client):
        cid = _make_category(client)
        res = client.post('/products', json={
            'name': '   ', 'price': 1000, 'category_id': cid
        })
        assert res.status_code == 400

    def test_create_product_negative_price_returns_422(self, client):
        cid = _make_category(client)
        res = client.post('/products', json={
            'name': 'Neg', 'price': -500, 'category_id': cid
        })
        assert res.status_code == 422
        assert '0 or greater' in res.get_json()['error']

    def test_create_product_negative_stock_returns_422(self, client):
        cid = _make_category(client)
        res = client.post('/products', json={
            'name': 'NegStock', 'price': 1000, 'category_id': cid, 'stock_quantity': -3
        })
        assert res.status_code == 422

    def test_create_product_price_zero_allowed(self, client):
        """Contoh mengizinkan price = 0 (bukan error)."""
        cid = _make_category(client)
        res = client.post('/products', json={
            'name': 'Gratis', 'price': 0, 'category_id': cid
        })
        assert res.status_code == 201
        assert res.get_json()['price'] == 0.0


class TestUpdateProduct:
    """PUT /products/<id>"""

    def _seed_product(self, client):
        cid = _make_category(client)
        return client.post('/products', json={
            'name': 'Wireless Mouse', 'price': 150000, 'category_id': cid, 'stock_quantity': 50
        }).get_json()['id']

    def test_update_product_success(self, client):
        pid = self._seed_product(client)
        res = client.put(f'/products/{pid}', json={'price': 125000})
        assert res.status_code == 200
        data = res.get_json()
        assert data['price'] == 125000.0
        assert data['name'] == 'Wireless Mouse'  # partial update, name tetap

    def test_update_product_not_found_returns_404(self, client):
        res = client.put('/products/9999', json={'price': 100})
        assert res.status_code == 404

    def test_update_product_negative_price_returns_422(self, client):
        pid = self._seed_product(client)
        res = client.put(f'/products/{pid}', json={'price': -500})
        assert res.status_code == 422

    def test_update_product_empty_name_returns_400(self, client):
        pid = self._seed_product(client)
        res = client.put(f'/products/{pid}', json={'name': ''})
        assert res.status_code == 400

    def test_update_product_no_body_returns_400(self, client):
        pid = self._seed_product(client)
        res = client.put(f'/products/{pid}', content_type='application/json', data='')
        assert res.status_code == 400


class TestDeleteProduct:
    """DELETE /products/<id>"""

    def test_delete_product_success(self, client):
        cid = _make_category(client)
        pid = client.post('/products', json={
            'name': 'ToDelete', 'price': 1000, 'category_id': cid
        }).get_json()['id']

        res = client.delete(f'/products/{pid}')
        assert res.status_code == 200
        assert 'deleted' in res.get_json()['message'].lower()

        # pastikan sudah hilang
        assert client.get(f'/products/{pid}').status_code == 404

    def test_delete_product_not_found_returns_404(self, client):
        res = client.delete('/products/9999')
        assert res.status_code == 404

    def test_delete_product_blocked_when_active_order(self, client):
        """Deletion guard: produk dengan order aktif tidak boleh dihapus (409)."""
        cid = _make_category(client)
        pid = client.post('/products', json={
            'name': 'InOrder', 'price': 1000, 'category_id': cid
        }).get_json()['id']

        # buat user + order yang memakai produk ini
        uid = client.post('/users', json={
            'username': 'buyer', 'email': 'buyer@test.com', 'password': 'pass123'
        }).get_json()['id']
        client.post('/orders', json={
            'user_id': uid, 'items': [{'product_id': pid, 'quantity': 1}]
        })

        res = client.delete(f'/products/{pid}')
        assert res.status_code == 409
        assert 'active order' in res.get_json()['error'].lower()
