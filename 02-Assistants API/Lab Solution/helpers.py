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
            Queries the NASDAQ database to answer a question or respond
            to a command. The database contains information about selected
            NASDAQ stocks from January 1, 2020 through August 9, 2024. It
            contains a table named Stocks that has the following schema:

            CREATE TABLE Stocks (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Symbol TEXT NOT NULL,   -- Stock symbol (for example, "MSFT")
                Date DATE NOT NULL,     -- Date
                Open NUMERIC NOT NULL,  -- Opening price of the stock on that date
                Low NUMERIC NOT NULL,   -- Lowest price of the stock on that date
                High NUMERIC NOT NULL,  -- Highest price of the stock on that date
                Close NUMERIC NOT NULL, -- Closing price of the stock on that date
                Volume INT NOT NULL     -- Number of shares traded on that date
            )
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
        the SQL only. Do not include a description or markdown characters.

        PROMPT: {text}

        The database has a table named Stocks that is defined as follows:

        CREATE TABLE Stocks (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Symbol TEXT NOT NULL,   -- Stock symbol (for example, "MSFT")
            Date DATE NOT NULL,     -- Date
            Open NUMERIC NOT NULL,  -- Opening price of the stock on that date
            Low NUMERIC NOT NULL,   -- Lowest price of the stock on that date
            High NUMERIC NOT NULL,  -- Highest price of the stock on that date
            Close NUMERIC NOT NULL, -- Closing price of the stock on that date
            Volume INT NOT NULL     -- Number of shares traded on that date
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
    connection = sqlite3.connect('data/nasdaq.db')
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows
