import base64
from openai import OpenAI
from flask import Flask, render_template, request, Response, stream_with_context, make_response
from helpers import *

client = OpenAI()

assistant = get_or_create_assistant(
    client,
    'LISA-chart',
    instructions='''
        You are a friendly assistant named LISA who can answer questions about Northwind and
        can illustrate your answers by generating charts and graphs. Assume that monetary amounts
        are in dollars. Round such amounts to the nearest dollar in your output, and use commas
        as separators for amounts greater than $999. Use a black background with light text and
        graphics for any images you produce. Do not return any markdown in your text responses.
        ''',
    tools=[database_tool, { 'type': 'code_interpreter' }]
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

        # Create a streaming run
        main_stream = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            stream=True
        )

        for event in main_stream:
            # If text is starting to stream back, wrap the stream
            # in a generator and return the generator to the client
            if event.event == 'thread.message.created':
                response = make_response(stream_with_context(generate(main_stream)))
                response.headers['X-Thread-ID'] = thread.id
                return response

            # If one or more function calls are required, execute the calls
            # and submit the output to the Assistants API. Then take the NEW
            # stream that's created, wrap it in a generator, and return the
            # generator to the client.
            if event.event == 'thread.run.requires_action':
                tool_outputs = []

                for tool_call in event.data.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name

                    if function_name == 'query_database':
                        print('Calling query_database()')
                        input = json.loads(tool_call.function.arguments)['input']
                        output = query_database(input)
                    else:
                        raise Exception('Invalid function name')

                    tool_output = {
                        'tool_call_id': tool_call.id,
                        'output': output
                    }

                    tool_outputs.append(tool_output)

                # Pass the tool output(s) to the Assistants API
                tool_stream = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=event.data.id,
                    tool_outputs=tool_outputs,
                    stream=True
                )

                # Return the new stream to the client and include the thread ID
                response = make_response(stream_with_context(generate(tool_stream)))
                response.headers['X-Thread-ID'] = thread.id
                return response

        # Return an error message if the stream ends unexpectedly
        response = make_response(stream_with_context('Oops! Can you try that again?'))
        response.headers['X-Thread-ID'] = thread.id
        return response      

    except Exception as e:
        # Return an error message if something goes wrong
        if "Can't add messages to thread" in str(e):
            response = make_response(stream_with_context("Give me a moment. I'm still working on your previous request."))
        else:
            response = make_response(stream_with_context("I'm sorry, but something went wrong."))

        response.headers['X-Thread-ID'] = thread.id
        return response

# REST method for downloading images
@app.route('/image', methods=['get'])
def get_image():
    file_id = request.args.get('id')
    image_file = client.files.content(file_id)
    image_bytes = image_file.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    src = f'data:image/png;base64,{base64_image}'
    return Response(src)

def generate(stream):
    for event in stream:
        if event.event == 'thread.message.created':
            for content in event.data.content or []:
                if content.type == 'text' and content.text and content.text.value:
                   # Output the latest chunk of text
                    yield content.text.value
                elif content.type == 'image_file' and content.image_file and content.image_file.file_id:
                    # Output an image file ID
                    yield f'[[[IMAGEID]]]{content.image_file.file_id}'

        elif event.event == 'thread.message.delta':
            for content in event.data.delta.content or []:
                if content.type == 'text' and content.text and content.text.value:
                   # Output the latest chunk of text
                    yield content.text.value
                elif content.type == 'image_file' and content.image_file and content.image_file.file_id:
                    # Output an image file ID
                    yield f'[[[IMAGEID]]]{content.image_file.file_id}'
