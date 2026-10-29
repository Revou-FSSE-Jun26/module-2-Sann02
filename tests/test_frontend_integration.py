# tests/test_frontend_integration.py
# Perilaku API yang dibutuhkan frontend Next.js (Module 3 Checkpoint 3).


def _register(client, email='cust@test.com'):
    return client.post('/users', json={
        'username': 'cust', 'email': email, 'password': 'password123'
    })


def test_register_assigns_customer_role(client):
    res = _register(client)
    assert res.status_code == 201
    assert res.get_json()['role'] == 'customer'


def test_cors_preflight_allows_browser_calls(client):
    res = client.options('/auth/login', headers={
        'Origin': 'https://revoshop.example.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization',
    })
    # flask-cors echoes the request origin back when origins="*"
    assert res.headers.get('Access-Control-Allow-Origin') in ('*', 'https://revoshop.example.com')
    allowed = res.headers.get('Access-Control-Allow-Headers', '').lower()
    assert 'authorization' in allowed and 'content-type' in allowed


def test_orders_list_includes_items(client):
    cid = client.post('/categories', json={'name': 'Cat'}).get_json()['id']
    pid = client.post('/products', json={
        'name': 'Thing', 'price': 1000, 'category_id': cid
    }).get_json()['id']
    uid = _register(client).get_json()['id']
    client.post('/orders', json={'user_id': uid, 'items': [{'product_id': pid, 'quantity': 3}]})

    orders = client.get('/orders').get_json()
    assert len(orders) == 1
    assert orders[0]['items'][0]['product_name'] == 'Thing'
    assert orders[0]['items'][0]['quantity'] == 3


def test_delete_category_with_products_is_blocked(client):
    cid = client.post('/categories', json={'name': 'Busy'}).get_json()['id']
    client.post('/products', json={'name': 'P', 'price': 1, 'category_id': cid})

    res = client.delete(f'/categories/{cid}')
    assert res.status_code == 409


def test_admin_cannot_place_order(client):
    from extensions import db
    from models import User

    cid = client.post('/categories', json={'name': 'AdminBlock'}).get_json()['id']
    pid = client.post('/products', json={
        'name': 'Item', 'price': 1000, 'category_id': cid
    }).get_json()['id']
    uid = _register(client, 'admin@test.com').get_json()['id']

    admin = User.query.get(uid)
    admin.role = 'admin'
    db.session.commit()

    res = client.post('/orders', json={
        'user_id': uid, 'items': [{'product_id': pid, 'quantity': 1}]
    })
    assert res.status_code == 403
