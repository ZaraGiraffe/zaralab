document.addEventListener('DOMContentLoaded', function() {
    const databaseSelect = document.getElementById('databaseSelect');
    const loadDatabaseButton = document.getElementById('loadDatabase');
    const createDatabaseButton = document.getElementById('createDatabase');
    const newDatabaseNameInput = document.getElementById('newDatabaseName');
    const tableSection = document.getElementById('tableSection');
    const tableNameInput = document.getElementById('tableName');
    const tableSchemaInput = document.getElementById('tableSchema');
    const addTableButton = document.getElementById('addTable');
    const tableList = document.getElementById('tableList');
    const rowSection = document.getElementById('rowSection');
    const currentTableNameSpan = document.getElementById('currentTableName');
    const rowFormContainer = document.getElementById('rowFormContainer');
    const addRowButton = document.getElementById('addRow');
    const dataTable = document.getElementById('dataTable');

    let currentDatabase = '';
    let currentTable = '';
    let currentSchema = {};

    async function loadDatabases() {
        const response = await fetch('/databases');
        const databases = await response.json();
        databaseSelect.innerHTML = '';
        databases.forEach(db => {
            const option = document.createElement('option');
            option.value = db;
            option.textContent = db;
            databaseSelect.appendChild(option);
        });
    }

    loadDatabaseButton.addEventListener('click', () => {
        currentDatabase = databaseSelect.value;
        if (currentDatabase) {
            tableSection.style.display = 'block';
            loadTables();
        }
    });

    createDatabaseButton.addEventListener('click', async () => {
        const dbName = newDatabaseNameInput.value.trim();
        if (dbName) {
            await fetch(`/create_database/${dbName}`, { method: 'POST' });
            await loadDatabases();
            newDatabaseNameInput.value = '';
        }
    });

    async function loadTables() {
        const response = await fetch(`/${currentDatabase}/tables_list`);
        const tables = await response.json();
        tableList.innerHTML = '';
        tables.forEach(table => {
            const li = document.createElement('li');
            li.textContent = table;
            li.addEventListener('click', () => {
                currentTable = table;
                currentTableNameSpan.textContent = currentTable;
                rowSection.style.display = 'block';
                loadSchema();
                loadTableData();
            });
            tableList.appendChild(li);
        });
    }

    addTableButton.addEventListener('click', async () => {
        const tableName = tableNameInput.value.trim();
        const schemaText = tableSchemaInput.value.trim();
        if (tableName && schemaText) {
            try {
                const schema = JSON.parse(schemaText);
                const response = await fetch(`/${currentDatabase}/tables`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ table_name: tableName, schema })
                });
                const result = await response.json();
                if (response.ok) {
                    alert(result.message);
                    tableNameInput.value = '';
                    tableSchemaInput.value = '';
                    loadTables();
                } else {
                    alert(result.error);
                }
            } catch (e) {
                alert('Invalid schema JSON format.');
            }
        }
    });

    async function loadSchema() {
        const response = await fetch(`/${currentDatabase}/tables/${currentTable}/schema`);
        currentSchema = await response.json();
        generateRowForm();
    }

    function generateRowForm() {
        rowFormContainer.innerHTML = '';
        for (let field in currentSchema) {
            const label = document.createElement('label');
            label.textContent = `${field} (${currentSchema[field]}):`;
            const input = document.createElement('input');
            input.name = field;
            input.dataset.type = currentSchema[field];
            input.required = true;
            rowFormContainer.appendChild(label);
            rowFormContainer.appendChild(input);
        }
    }

    addRowButton.addEventListener('click', async () => {
        const inputs = rowFormContainer.querySelectorAll('input');
        const rowData = {};
        let isValid = true;
        inputs.forEach(input => {
            const value = input.value.trim();
            const type = input.dataset.type;
            if (!validateField(value, type)) {
                isValid = false;
                alert(`Invalid value for field ${input.name} (expected ${type}).`);
            } else {
                rowData[input.name] = value;
            }
        });
        if (isValid) {
            const response = await fetch(`/${currentDatabase}/tables/${currentTable}/rows`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rowData)
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                loadTableData();
            } else {
                alert(result.error);
            }
        }
    });

    async function loadTableData() {
        const response = await fetch(`/${currentDatabase}/tables/${currentTable}/rows`);
        const data = await response.json();
        dataTable.innerHTML = '';
        if (data.length > 0) {
            const headerRow = document.createElement('tr');
            for (let field in data[0]) {
                const th = document.createElement('th');
                th.textContent = field;
                headerRow.appendChild(th);
            }
            const actionTh = document.createElement('th');
            actionTh.textContent = 'Actions';
            headerRow.appendChild(actionTh);
            dataTable.appendChild(headerRow);

            data.forEach((row, index) => {
                const tr = document.createElement('tr');
                for (let field in row) {
                    const td = document.createElement('td');
                    td.textContent = row[field];
                    tr.appendChild(td);
                }
                const actionTd = document.createElement('td');
                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.addEventListener('click', async () => {
                    const response = await fetch(`/${currentDatabase}/tables/${currentTable}/rows/${index}`, { method: 'DELETE' });
                    const result = await response.json();
                    if (response.ok) {
                        alert(result.message);
                        loadTableData();
                    } else {
                        alert(result.error);
                    }
                });
                actionTd.appendChild(deleteButton);
                tr.appendChild(actionTd);

                dataTable.appendChild(tr);
            });
        } else {
            dataTable.innerHTML = '<tr><td>No data available.</td></tr>';
        }
    }

    function validateField(value, type) {
        switch (type) {
            case 'integer':
                return /^\d+$/.test(value);
            case 'real':
                return /^\d+(\.\d+)?$/.test(value);
            case 'char':
                return value.length === 1;
            case 'string':
                return true;
            case 'date':
                return /^\d{4}-\d{2}-\d{2}$/.test(value);
            case 'date_interval':
                return /^\d{4}-\d{2}-\d{2}\/\d{4}-\d{2}-\d{2}$/.test(value);
            default:
                return false;
        }
    }

    loadDatabases();
});
