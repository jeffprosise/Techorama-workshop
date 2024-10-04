import json, sqlite3, re
from openai import OpenAI

# Helper method for retrieving an existing assistant or creating a new one
def get_or_create_assistant(client, name, instructions, tools=None, tool_resources=None):
    for assistant in client.beta.assistants.list():
        if assistant.name == name:
            return assistant

    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model='gpt-4o',
        tools=tools,
        tool_resources=tool_resources
    )

    return assistant

# Tool function
def query_database(input):
    sql = text2sql(input)
    print(sql) # Show the query in the host window
    result = execute_sql(sql)
    return json.dumps(result)

# Tool description
database_tool = {
    'type': 'function',
    'function': {
        'name': 'query_database',
        'description': '''
            Queries the Northwind database to answer a question or respond
            to a command. Northwind contains information about sales, products,
            orders, and employees of a fictitious company named Northwind Traders.
            The database contains the following tables:

            Categories - Information about product categories
            Customers - Information about customers who purchase Northwind products
            Employees - Information about employees of Northwind Traders
            Shippers - Information about companies that ship Northwind products
            Suppliers - Information about suppliers of Northwind products
            Products - Information about the products that Northwind sells
            Orders - Information about orders placed by Northwind customers
            OrderDetails - Information abour order details such as products and quantities
            ''',
        'parameters': {
            'type': 'object',
            'properties': {
                'input': {
                    'type': 'string',
                    'description': 'Input from the user'
                },
            },
            'required': ['input']
        }
    }
}

# Helper function for generating SQL queries
def text2sql(text):
    prompt = f'''
        Generate a well-formed SQLite query from the prompt below. Return
        the SQL only. Do not include a description or markdown characters, and
        do not use SELECT *. Be specific about fields in SELECT statements.

        PROMPT: {text}
    
        The database targeted by the query contains the following tables:

        CREATE TABLE [Categories]
        (
            [CategoryID] INTEGER PRIMARY KEY AUTOINCREMENT,
            [CategoryName] TEXT,
            [Description] TEXT
        )

        CREATE TABLE [Customers]
        (
            [CustomerID] TEXT,
            [CompanyName] TEXT,
            [ContactName] TEXT,
            [ContactTitle] TEXT,
            [Address] TEXT,
            [City] TEXT,
            [Region] TEXT,
            [PostalCode] TEXT,
            [Country] TEXT,
            [Phone] TEXT,
            [Fax] TEXT,
            PRIMARY KEY (`CustomerID`)
        )

        CREATE TABLE [Employees]
        (
            [EmployeeID] INTEGER PRIMARY KEY AUTOINCREMENT,
            [LastName] TEXT,
            [FirstName] TEXT,
            [Title] TEXT,
            [TitleOfCourtesy] TEXT,
            [BirthDate] DATE,
            [HireDate] DATE,
            [Address] TEXT,
            [City] TEXT,
            [Region] TEXT,
            [PostalCode] TEXT,
            [Country] TEXT,
            [HomePhone] TEXT,
            [Extension] TEXT,
            [Notes] TEXT,
            [ReportsTo] INTEGER,
            FOREIGN KEY ([ReportsTo]) REFERENCES [Employees] ([EmployeeID]) 
            ON DELETE NO ACTION ON UPDATE NO ACTION
        )

        CREATE TABLE [Shippers]
        (
            [ShipperID] INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            [CompanyName] TEXT NOT NULL,
            [Phone] TEXT
        )

        CREATE TABLE [Suppliers]
        (
            [SupplierID] INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            [CompanyName] TEXT NOT NULL,
            [ContactName] TEXT,
            [ContactTitle] TEXT,
            [Address] TEXT,
            [City] TEXT,
            [Region] TEXT,
            [PostalCode] TEXT,
            [Country] TEXT,
            [Phone] TEXT,
            [Fax] TEXT,
            [HomePage] TEXT
        )

        CREATE TABLE [Products]
        (
            [ProductID] INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            [ProductName] TEXT NOT NULL,
            [SupplierID] INTEGER,
            [CategoryID] INTEGER,
            [QuantityPerUnit] TEXT,
            [UnitPrice] NUMERIC DEFAULT 0,
            [UnitsInStock] INTEGER DEFAULT 0,
            [UnitsOnOrder] INTEGER DEFAULT 0,
            [ReorderLevel] INTEGER DEFAULT 0,
            [Discontinued] TEXT NOT NULL DEFAULT '0',
            FOREIGN KEY ([CategoryID]) REFERENCES [Categories] ([CategoryID]),
            FOREIGN KEY ([SupplierID]) REFERENCES [Suppliers] ([SupplierID])
        )

        CREATE TABLE Orders
        (
            [OrderID] INTEGER PRIMARY KEY AUTOINCREMENT,
            [CustomerID] INTEGER,
            [EmployeeID] INTEGER,
            [OrderDate] DATETIME,
            [ShipperID] INTEGER,
            FOREIGN KEY (EmployeeID) REFERENCES Employees (EmployeeID),
            FOREIGN KEY (CustomerID) REFERENCES Customers (CustomerID),
            FOREIGN KEY (ShipperID) REFERENCES Shippers (ShipperID)
        );

        CREATE TABLE [Order Details]
        (
            [OrderID] INTEGER NOT NULL,
            [ProductID] INTEGER NOT NULL,
            [UnitPrice] NUMERIC NOT NULL DEFAULT 0,
            [Quantity] INTEGER NOT NULL DEFAULT 1,
            [Discount] REAL NOT NULL DEFAULT 0,
            PRIMARY KEY ("OrderID", "ProductID"),
            FOREIGN KEY ([OrderID]) REFERENCES [Orders] ([OrderID]),
            FOREIGN KEY ([ProductID]) REFERENCES [Products] ([ProductID]) 
        )
        '''

    messages = [
        {
            'role': 'system',
            'content': 'You are a database expert who can convert natural-language questions and commands into SQL queries'
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]

    client = OpenAI()
    
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages
    )

    sql = response.choices[0].message.content

    # Strip markdown characters from the SQL if present
    pattern = r'^```[\w]*\n|\n```$'
    return re.sub(pattern, '', sql, flags=re.MULTILINE)

# Helper function for executing SQL queries
def execute_sql(sql):
    connection = sqlite3.connect('data/northwind.db')
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows
