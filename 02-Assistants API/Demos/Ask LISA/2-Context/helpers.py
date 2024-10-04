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
