import chromadb, uuid
from pypdf import PdfReader
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Create a persistent ChromaDB database in the "chroma" subdirectory
client = chromadb.PersistentClient('chroma')
collection = client.create_collection(name='Electric_Vehicles')

# Extract text from the PDFs and add them to the database
file_names = [
    'electric_vehicles.pdf',
    'pev_consumer_handbook.pdf',
    'department-for-transport-ev-guide.pdf'
]

for file in file_names:
    print(f'Processing {file}')
    reader = PdfReader(file)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        collection.add(
            documents=[text],
            metadatas=[{ 'file': file, 'page': i }],
            ids=[uuid.uuid4().hex]
        )