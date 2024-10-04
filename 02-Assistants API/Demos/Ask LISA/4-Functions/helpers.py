import os, json, requests

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
def get_current_weather(location):
    api_key = os.environ['OPENWEATHER_API_KEY']
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial'
    response = requests.get(url)
    return json.dumps(response.json())

# Tool description
weather_tool = {
    'type': 'function',
    'function': {
        'name': 'get_current_weather',
        'description': """
            Retrieves the current weather at the specified location.
            Also returns the location's latitude and longitude and the country it's in.
            """,
        'parameters': {
            'type': 'object',
            'properties': {
                'location': {
                    'type': 'string',
                    'description': 'The location whose weather is to be retrieved.'
                }
            },
            'required': ['location']
        }
    }
}
