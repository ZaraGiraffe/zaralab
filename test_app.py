import os
import pytest
import json
from app import app, DATABASE_DIR


@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    if os.path.exists(DATABASE_DIR):
        for filename in os.listdir(DATABASE_DIR):
            file_path = os.path.join(DATABASE_DIR, filename)
            os.remove(file_path)
    else:
        os.makedirs(DATABASE_DIR)

    yield client

    for filename in os.listdir(DATABASE_DIR):
        file_path = os.path.join(DATABASE_DIR, filename)
        os.remove(file_path)


def test_list_databases_empty(client):
    response = client.get('/databases')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_list_databases(client):
    client.post('/create_database/testdb')
    response = client.get('/databases')
    assert response.status_code == 200
    assert 'testdb' in response.get_json()


def test_create_database(client):
    response = client.post('/create_database/testdb')
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Database testdb created successfully'


def test_create_existing_database(client):
    client.post('/create_database/testdb')
    response = client.post('/create_database/testdb')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Database already exists'


def test_list_tables_empty(client):
    client.post('/create_database/testdb')
    response = client.get('/testdb/tables_list')
    assert response.status_code == 200
    assert response.get_json() == []


def test_add_table(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    response = client.post('/testdb/tables', json=data)
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Table users added successfully'


def test_add_existing_table(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    response = client.post('/testdb/tables', json=data)
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Table already exists'


def test_get_table_schema(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    response = client.get('/testdb/tables/users/schema')
    assert response.status_code == 200
    assert response.get_json() == data['schema']


def test_get_schema_nonexistent_table(client):
    client.post('/create_database/testdb')
    response = client.get('/testdb/tables/users/schema')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Table does not exist'


def test_add_row(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    row_data = {
        'id': '1',
        'name': 'Alice'
    }
    response = client.post('/testdb/tables/users/rows', json=row_data)
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Row added successfully'


def test_add_row_invalid_data(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    row_data = {
        'id': 'abc',
        'name': 'Alice'
    }
    response = client.post('/testdb/tables/users/rows', json=row_data)
    assert response.status_code == 400
    assert 'Invalid value for field id' in response.get_json()['error']


def test_delete_row(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    row_data = {
        'id': '1',
        'name': 'Alice'
    }
    client.post('/testdb/tables/users/rows', json=row_data)
    response = client.delete('/testdb/tables/users/rows/0')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Row deleted successfully'


def test_delete_nonexistent_row(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    response = client.delete('/testdb/tables/users/rows/0')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Row ID out of range'


def test_get_all_rows(client):
    client.post('/create_database/testdb')
    data = {
        'table_name': 'users',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data)
    row_data1 = {'id': '1', 'name': 'Alice'}
    row_data2 = {'id': '2', 'name': 'Bob'}
    client.post('/testdb/tables/users/rows', json=row_data1)
    client.post('/testdb/tables/users/rows', json=row_data2)
    response = client.get('/testdb/tables/users/rows')
    assert response.status_code == 200
    assert response.get_json() == [row_data1, row_data2]


def test_intersect_tables(client):
    client.post('/create_database/testdb')

    data1 = {
        'table_name': 'table1',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data1)
    row_data1 = {'id': '1', 'name': 'Alice'}
    row_data2 = {'id': '2', 'name': 'Bob'}
    client.post('/testdb/tables/table1/rows', json=row_data1)
    client.post('/testdb/tables/table1/rows', json=row_data2)

    data2 = {
        'table_name': 'table2',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data2)
    row_data3 = {'id': '2', 'name': 'Bob'}
    row_data4 = {'id': '3', 'name': 'Charlie'}
    client.post('/testdb/tables/table2/rows', json=row_data3)
    client.post('/testdb/tables/table2/rows', json=row_data4)

    response = client.get('/testdb/tables/table1/intersect/table2')
    assert response.status_code == 200
    assert response.get_json() == [row_data2]  # Only Bob is common


def test_intersect_tables_different_schemas(client):
    client.post('/create_database/testdb')

    data1 = {
        'table_name': 'table1',
        'schema': {
            'id': 'integer',
            'name': 'string'
        }
    }
    client.post('/testdb/tables', json=data1)

    data2 = {
        'table_name': 'table2',
        'schema': {
            'id': 'integer',
            'email': 'string'
        }
    }
    client.post('/testdb/tables', json=data2)

    response = client.get('/testdb/tables/table1/intersect/table2')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Table schemas are not equal'
