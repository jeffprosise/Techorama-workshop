import os, chromadb
from openai import OpenAI
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)

# Load the vector database
client = chromadb.PersistentClient('chroma')
collection = client.get_collection(name='Electric_Vehicles')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/answer', methods=['GET'])
def answer_question():
    question = request.args.get('query')

    if question is not None and len(question) > 0:
        # Query the vector store
        results = collection.query(
            query_texts=[question],
            n_results=3
        )
		
        # Concatenate the results to form context
        context = ''
        documents = results['documents'][0]

        for document in documents:
            context += document
            context += '\n\n'
		
        # Submit the question and the context to an LLM
        client = OpenAI()
		
        content = f'''
            Answer the following question using the provided context, and if the
            answer is not contained within the context, say "I don't know." Explain
            your answer if possible.
			
            Question:
            {question}

            Context:
            {context}
            '''
		
        messages = [{ 'role': 'user', 'content': content }]

        # Get the response
        chunks = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            stream=True
        )

        return Response(stream_with_context(generate(chunks)))

def generate(chunks):
    for chunk in chunks:
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content
