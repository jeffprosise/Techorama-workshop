import os, chromadb
from openai import OpenAI
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)

# TODO: Load the vector database

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/answer', methods=['GET'])
def answer_question():
    question = request.args.get('query')

    if question is not None and len(question) > 0:
        return "I don't know."
