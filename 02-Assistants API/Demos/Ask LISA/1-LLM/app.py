from openai import OpenAI
from flask import Flask, render_template, request, Response, stream_with_context

client = OpenAI()
app = Flask(__name__)

# Home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# REST method for invoking an LLM
@app.route('/assistant', methods=['get'])
def ask_assistant():
    try:
        input = request.args.get('input')

        messages = [
            {
                'role': 'system',
                'content': 'You are a friendly assistant named LISA who can answer questions from users',
            },
            {
                'role': 'user',
                'content': input
            }
        ]

        chunks = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            stream=True
        )

        return Response(stream_with_context(generate(chunks)))

    except Exception as e:
        return Response(stream_with_context("I'm sorry, but something went wrong."))

# Generator for streaming output
def generate(chunks):
    for chunk in chunks:
        text = chunk.choices[0].delta.content
        if text is not None:
            yield text
