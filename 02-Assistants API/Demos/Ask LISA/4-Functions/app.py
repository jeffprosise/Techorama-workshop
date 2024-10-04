from openai import OpenAI
from flask import Flask, render_template, request, stream_with_context, make_response
from helpers import *

client = OpenAI()

assistant = get_or_create_assistant(
    client,
    'LISA-functions',
    instructions='''
        You are a helpful assistant named LISA who can answer questions from users,
        including questions about current weather conditions.
        ''',
    tools=[weather_tool]
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

                    if function_name == 'get_current_weather':
                        print('Calling get_current_weather()')
                        location = json.loads(tool_call.function.arguments)['location']
                        output = get_current_weather(location)
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

                # Return the new stream to the client
                response = make_response(stream_with_context(generate(tool_stream)))
                response.headers['X-Thread-ID'] = thread.id
                return response

        # Return an error message if the stream ends unexpectedly
        response = make_response(stream_with_context('Oops! Can you try that again?'))
        response.headers['X-Thread-ID'] = thread.id
        return response   

    except Exception as e:
        # Return an error message if something goes wrong
        response = make_response(stream_with_context("I'm sorry, but something went wrong."))
        response.headers['X-Thread-ID'] = thread.id
        return response

# Generator for streaming output
def generate(stream):
    for event in stream:
        if event.event == 'thread.message.delta':
            for content in event.data.delta.content or []:
                if content.type == 'text' and content.text and content.text.value:
                    yield content.text.value
