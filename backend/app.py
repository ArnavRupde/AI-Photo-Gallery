import json
import os
from flask import Flask, request, jsonify, send_from_directory
import pika
import requests
from werkzeug.utils import secure_filename
import signal
import sys

app= Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB
app.config['UPLOAD_EXTENSIONS'] = ['jpg', 'jpeg', 'png']
app.config['UPLOAD_PATH'] = 'uploads' # Replace with absolute path
HOST = 'localhost'
PORT = 5000

# Milvus configurations
MILVUS_SEARCH_ENDPOINT = "http://localhost:19530/v1/vector/search"
MILVUS_COLLECTION_NAME = "intelligent_image_search"
MILVUS_DEFAULT_SEARCH_LIMIT = 1
MILVUS_DEFAULT_OFFSET = 0
MILVUS_OUTPUT_FIELDS = ["image_id", "image_path", "image_description"]

# OLLAMA configurations
OLLAMA_EMBEDDINGS_ENDPOINT = "http://localhost:11434/api/embeddings"
OLLAMA_EMBEDDINGS_MODEL = "mistral"

# Embeddings dimensions
EMBEDDINGS_DIMENSIONS = 4096

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='image_uploads')


@app.route("/", methods=["GET"])
def home():
    resp = {
        "message": "Hello World"
    }
    return resp

def is_valid_file_type(filename):
    if '.' in filename:
        ext = filename.split('.')[-1]
        if ext in app.config['UPLOAD_EXTENSIONS']:
            return True
    return False

@app.route("/upload", methods=["POST"])
def upload():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename == '':
        return {"error": "Invalid file name"}, 400
    if uploaded_file and is_valid_file_type(filename):
        filepath = os.path.join(app.config['UPLOAD_PATH'], filename)
        uploaded_file.save(
            filepath
        )
        absolute_filepath = os.path.abspath(filepath)
        # After uploading file, push the file path to RabbitMQ
        message = {
            "image_path": absolute_filepath
        }
        channel.basic_publish(exchange='', routing_key='image_uploads', body=json.dumps(message))
        print("Pushed file path to RabbitMQ")
        return {"message": "File uploaded successfully"}
    else:
        return {"error": "Invalid file type"}, 400

@app.route("/images", methods=["GET"])
def images():
    image_url_prefix = "http://" + HOST + ":" + str(PORT) + "/image/"
    all_images = [
        (image_url_prefix + f) for f in os.listdir(app.config['UPLOAD_PATH'])
    ]
    return {"data": all_images}

@app.route("/image/<image_name>", methods=["GET"])
def serve_image(image_name):
    if not os.path.exists(os.path.join(app.config['UPLOAD_PATH'], image_name)):
        return {"error": "Image not found"}, 404
    return send_from_directory(app.config['UPLOAD_PATH'], image_name)

@app.route("/search", methods=["POST"])
def search():
    data = json.loads(request.data)
    print(data)
    if 'search_text' not in data:
        return {"error": "Invalid request"}, 400
    search_text = data['search_text']

    # Get vector embedding for search text
    resp = requests.post(
        OLLAMA_EMBEDDINGS_ENDPOINT,
        json = {
            "model": OLLAMA_EMBEDDINGS_MODEL,
            "prompt": search_text
        }
    )
    resp = resp.json()
    if 'embedding' not in resp:
        print("Error getting embeddings for image Error: ")
        print(resp)
        return
    embeddings = resp['embedding']
    if len(embeddings) != EMBEDDINGS_DIMENSIONS:
        print(
            "Invalid embedding dimensions" +
            " Expected: " + str(EMBEDDINGS_DIMENSIONS) +
            " Got: " + str(len(embeddings))
        )
        return
    print("Embeddings for search_text: " + search_text + ":")
    print(embeddings)

    num_entries = data.get('num_entries', MILVUS_DEFAULT_SEARCH_LIMIT)
    resp = requests.post(
        MILVUS_SEARCH_ENDPOINT,
        json = {
            "collectionName": MILVUS_COLLECTION_NAME,
            "outputFields": MILVUS_OUTPUT_FIELDS,
            "limit": num_entries,
            "offset": MILVUS_DEFAULT_OFFSET,
            "metric_type": "COSINE",
            "vector": embeddings
        }
    )
    resp = resp.json()
    if 'data' not in resp:
        print("Error searching for image resp: ")
        print(resp)
        return
    if resp['data'] == []:
        return {"message": "No results found"}
    for entry in resp['data']:
        image_name = entry['image_path'].split('/')[-1]
        entry['image_path'] = "http://" + HOST + ":" + str(PORT) + "/image/" + image_name 
    return {"data": resp['data']}



# Register signal handler to gracefully shutdown the application
def signal_handler(signal, frame):
    connection.close() # Close RabbitMQ connection
    print("\nReceived keyboard interrupt, shutting down...")
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    app.run(debug=True, host=HOST, port=PORT)
