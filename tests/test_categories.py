# tests/test_categories.py
"""
Test suite for Category CRUD endpoints.
Covers happy path and error cases for: GET all, GET by id, POST, PUT, DELETE.
"""


class TestGetCategories:
    """GET /categories"""

    def test_get_categories_empty(self, client):
        """Happy: returns empty list when no categories exist"""
        res = client.get('/categories')
        assert res.status_code == 200
        assert res.get_json() == []

    def test_get_categories_with_data(self, client):
        """Happy: returns list of categories"""
        # Seed 2 categories
        client.post('/categories', json={'name': 'Elektronik', 'description': 'Gadget'})
        client.post('/categories', json={'name': 'Pakaian', 'description': 'Fashion'})

        res = client.get('/categories')
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 2
        assert data[0]['name'] == 'Elektronik'
        assert data[1]['name'] == 'Pakaian'


class TestGetCategoryById:
    """GET /categories/<id>"""

    def test_get_category_by_id_success(self, client):
        """Happy: returns category with products list"""
        client.post('/categories', json={'name': 'Elektronik', 'description': 'Gadget'})

        res = client.get('/categories/1')
        assert res.status_code == 200
        data = res.get_json()
        assert data['name'] == 'Elektronik'
        assert 'products' in data  # includes products array

    def test_get_category_not_found(self, client):
        """Error: returns 404 for non-existent category"""
        res = client.get('/categories/999')
        assert res.status_code == 404
        assert 'not found' in res.get_json()['error']


class TestCreateCategory:
    """POST /categories"""

    def test_create_category_success(self, client):
        """Happy: creates category and returns 201"""
        res = client.post('/categories', json={
            'name': 'Makanan',
            'description': 'Aneka makanan'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['name'] == 'Makanan'
        assert data['description'] == 'Aneka makanan'
        assert 'id' in data

    def test_create_category_without_name(self, client):
        """Error: returns 400 when name is missing"""
        res = client.post('/categories', json={'description': 'No name'})
        assert res.status_code == 400
        assert 'required' in res.get_json()['error'].lower() or 'name' in res.get_json()['error'].lower()

    def test_create_category_empty_name(self, client):
        """Error: returns 400 when name is empty string"""
        res = client.post('/categories', json={'name': '   ', 'description': 'Blank'})
        assert res.status_code == 400

    def test_create_category_no_body(self, client):
        """Error: returns 400 when no JSON body sent"""
        res = client.post('/categories', content_type='application/json', data='')
        assert res.status_code == 400


class TestUpdateCategory:
    """PUT /categories/<id>"""

    def test_update_category_success(self, client):
        """Happy: updates name and returns 200"""
        client.post('/categories', json={'name': 'Old Name'})

        res = client.put('/categories/1', json={'name': 'New Name'})
        assert res.status_code == 200
        assert res.get_json()['name'] == 'New Name'

    def test_update_category_partial(self, client):
        """Happy: partial update only changes description"""
        client.post('/categories', json={'name': 'Tech', 'description': 'Old desc'})

        res = client.put('/categories/1', json={'description': 'Updated desc'})
        assert res.status_code == 200
        data = res.get_json()
        assert data['name'] == 'Tech'  # unchanged
        assert data['description'] == 'Updated desc'

    def test_update_category_not_found(self, client):
        """Error: returns 404 for non-existent category"""
        res = client.put('/categories/999', json={'name': 'Nope'})
        assert res.status_code == 404

    def test_update_category_empty_name(self, client):
        """Error: returns 400 when updating with empty name"""
        client.post('/categories', json={'name': 'Valid'})

        res = client.put('/categories/1', json={'name': ''})
        assert res.status_code == 400

    def test_update_category_no_body(self, client):
        """Error: returns 400 when no JSON body"""
        client.post('/categories', json={'name': 'Valid'})

        res = client.put('/categories/1', content_type='application/json', data='')
        assert res.status_code == 400


class TestDeleteCategory:
    """DELETE /categories/<id>"""

    def test_delete_category_success(self, client):
        """Happy: deletes category and returns 200"""
        client.post('/categories', json={'name': 'To Delete'})

        res = client.delete('/categories/1')
        assert res.status_code == 200
        assert 'deleted' in res.get_json()['message'].lower()

        # Verify it's gone
        res = client.get('/categories/1')
        assert res.status_code == 404

    def test_delete_category_not_found(self, client):
        """Error: returns 404 for non-existent category"""
        res = client.delete('/categories/999')
        assert res.status_code == 404
