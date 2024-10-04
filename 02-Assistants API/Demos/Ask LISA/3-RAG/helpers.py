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

# Helper method for retrieving an existing vector store or creating a new one
def get_or_create_vector_store(name, client):
    for vector_store in client.beta.vector_stores.list():
        if vector_store.name == name:
            return vector_store

    print(f'Creating "{name}" vector store and uploading files')
    vector_store = client.beta.vector_stores.create(name=name)

    file_paths = [
        'documents/electric_vehicles.pdf',
        'documents/pev_consumer_handbook.pdf',
        'documents/department-for-transport-ev-guide.pdf'
    ]

    file_streams = [open(path, 'rb') for path in file_paths]

    client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    return vector_store
