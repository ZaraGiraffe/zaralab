from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
from flask import send_from_directory

app = Flask(__name__)

DATABASE_DIR = 'databases'

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)


class DatabaseManager:
    """Manages databases: loading, saving, creating, and listing."""

    def __init__(self, db_dir='databases'):
        self.db_dir = db_dir
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

    def load_database(self, db_name):
        db_path = os.path.join(self.db_dir, f"{db_name}.json")
        if os.path.exists(db_path):
            with open(db_path, 'r') as f:
                data = json.load(f)
                return Database(db_name, data)
        else:
            return Database(db_name)

    def save_database(self, database):
        db_path = os.path.join(self.db_dir, f"{database.name}.json")
        with open(db_path, 'w') as f:
            json.dump(database.to_dict(), f, indent=4)

    def database_exists(self, db_name):
        db_path = os.path.join(self.db_dir, f"{db_name}.json")
        return os.path.exists(db_path)

    def create_database(self, db_name):
        if self.database_exists(db_name):
            return False
        else:
            db = Database(db_name)
            self.save_database(db)
            return True

    def list_databases(self):
        db_files = [f[:-5] for f in os.listdir(self.db_dir) if f.endswith('.json')]
        return db_files


class Database:
    """Represents a database containing multiple tables."""

    def __init__(self, name, data=None):
        self.name = name
        if data is None:
            self.tables = {}
        else:
            self.tables = {table_name: Table(table_name, table_data['schema'], table_data['rows'])
                           for table_name, table_data in data.get('tables', {}).items()}

    def to_dict(self):
        return {
            "tables": {table_name: table.to_dict() for table_name, table in self.tables.items()}
        }

    def add_table(self, table_name, schema):
        if table_name in self.tables:
            return False
        else:
            self.tables[table_name] = Table(table_name, schema)
            return True

    def delete_table(self, table_name):
        if table_name in self.tables:
            del self.tables[table_name]
            return True
        else:
            return False

    def get_table(self, table_name):
        return self.tables.get(table_name)

    def list_tables(self):
        return list(self.tables.keys())


class Table:
    """Represents a table within a database, including its schema and rows."""

    def __init__(self, name, schema, rows=None):
        self.name = name
        self.schema = schema
        self.rows = rows or []

    def to_dict(self):
        return {
            "schema": self.schema,
            "rows": self.rows
        }

    def add_row(self, row_data):
        row = {}
        for field in self.schema:
            if field not in row_data:
                return False, f"Field {field} is missing"
            if not self.validate_value(row_data[field], self.schema[field]):
                return False, f"Invalid value for field {field}"
            row[field] = row_data[field]
        self.rows.append(row)
        return True, "Row added successfully"

    def delete_row(self, row_id):
        if 0 <= row_id < len(self.rows):
            self.rows.pop(row_id)
            return True
        else:
            return False

    def get_all_rows(self):
        return self.rows

    def validate_value(self, value, value_type):
        try:
            if value_type == "integer":
                int(value)
            elif value_type == "real":
                float(value)
            elif value_type == "char":
                if len(value) != 1:
                    return False
            elif value_type == "string":
                str(value)
            elif value_type == "date":
                datetime.strptime(value, "%Y-%m-%d")
            elif value_type == "date_interval":
                start, end = value.split('/')
                datetime.strptime(start, "%Y-%m-%d")
                datetime.strptime(end, "%Y-%m-%d")
            else:
                return False
            return True
        except:
            return False

    def schema_equals(self, other_schema):
        return self.schema == other_schema


db_manager = DatabaseManager(DATABASE_DIR)


@app.route('/<db_name>/tables', methods=['POST'])
def add_table(db_name):
    data = request.get_json()
    table_name = data.get('table_name')
    schema = data.get('schema')
    if not table_name or not schema:
        return jsonify({"error": "table_name and schema are required"}), 400
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    if not db.add_table(table_name, schema):
        return jsonify({"error": "Table already exists"}), 400
    db_manager.save_database(db)
    return jsonify({"message": f"Table {table_name} added successfully"}), 201


@app.route('/<db_name>/tables/<table_name>', methods=['DELETE'])
def delete_table(db_name, table_name):
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    if not db.delete_table(table_name):
        return jsonify({"error": "Table does not exist"}), 404
    db_manager.save_database(db)
    return jsonify({"message": f"Table {table_name} deleted successfully"}), 200


@app.route('/<db_name>/tables/<table_name>/rows', methods=['POST'])
def add_row(db_name, table_name):
    data = request.get_json()
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table does not exist"}), 404
    success, message = table.add_row(data)
    if not success:
        return jsonify({"error": message}), 400
    db_manager.save_database(db)
    return jsonify({"message": message}), 201


@app.route('/<db_name>/tables/<table_name>/rows/<int:row_id>', methods=['DELETE'])
def delete_row(db_name, table_name, row_id):
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table does not exist"}), 404
    if not table.delete_row(row_id):
        return jsonify({"error": "Row ID out of range"}), 404
    db_manager.save_database(db)
    return jsonify({"message": "Row deleted successfully"}), 200


@app.route('/<db_name>/tables/<table_name>/rows', methods=['GET'])
def get_all_rows(db_name, table_name):
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table does not exist"}), 404
    rows = table.get_all_rows()
    return jsonify(rows), 200


@app.route('/<db_name>/tables/<table1_name>/intersect/<table2_name>', methods=['GET'])
def intersect_tables(db_name, table1_name, table2_name):
    db = db_manager.load_database(db_name)
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    table1 = db.get_table(table1_name)
    table2 = db.get_table(table2_name)
    if not table1 or not table2:
        return jsonify({"error": "One or both tables do not exist"}), 404
    if not table1.schema_equals(table2.schema):
        return jsonify({"error": "Table schemas are not equal"}), 400
    rows1 = table1.get_all_rows()
    rows2 = table2.get_all_rows()
    intersection_rows = [row for row in rows1 if row in rows2]
    return jsonify(intersection_rows), 200


@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/databases', methods=['GET'])
def list_databases():
    dbs = db_manager.list_databases()
    return jsonify(dbs), 200


@app.route('/create_database/<db_name>', methods=['POST'])
def create_database(db_name):
    if not db_manager.create_database(db_name):
        return jsonify({"error": "Database already exists"}), 400
    return jsonify({"message": f"Database {db_name} created successfully"}), 201


@app.route('/<db_name>/tables_list', methods=['GET'])
def list_tables(db_name):
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    db = db_manager.load_database(db_name)
    tables = db.list_tables()
    return jsonify(tables), 200


@app.route('/<db_name>/tables/<table_name>/schema', methods=['GET'])
def get_table_schema(db_name, table_name):
    if not db_manager.database_exists(db_name):
        return jsonify({"error": "Database does not exist"}), 404
    db = db_manager.load_database(db_name)
    table = db.get_table(table_name)
    if not table:
        return jsonify({"error": "Table does not exist"}), 404
    schema = table.schema
    return jsonify(schema), 200


if __name__ == '__main__':
    app.run(debug=True)
