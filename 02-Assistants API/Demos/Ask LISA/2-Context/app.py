from openai import OpenAI
from flask import Flask, render_template, request, stream_with_context, make_response
from helpers import *

client = OpenAI()

assistant = get_or_create_assistant(
    client,
    'LISA-context',
    instructions='You are a helpful assistant named LISA who can answer questions from users.'
)

app = Flask(__name__)

# Home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# REST method for invoking the Assistants API
@app.route('/assistant', methods=['get'])
def ask_assistant():
    try:
        # If the request contains a thread ID, retrieve the thread.
        # Otherwise, create a new thread.
        thread_id = request.headers.get('X-Thread-ID')

        if thread_id is None or len(thread_id) == 0:
            thread = client.beta.threads.create()
        else:
            thread = client.beta.threads.retrieve(thread_id)

        # Add a message to the thread
        input = request.args.get('input')

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=input
        )

        # Submit input to the Assistants API and stream the response
        response = make_response(stream_with_context(generate(client, thread.id, assistant.id)))
        response.headers['X-Thread-ID'] = thread.id
        return response

    except Exception as e:
        # Return an error message if something goes wrong
        response = make_response(stream_with_context("I'm sorry, but something went wrong."))
        response.headers['X-Thread-ID'] = thread.id
        return response
    
# Generator for streaming output
def generate(client, thread_id, assistant_id):
    with client.beta.threads.runs.stream(thread_id=thread_id, assistant_id=assistant_id) as stream:
        for text in stream.text_deltas:
            yield text
