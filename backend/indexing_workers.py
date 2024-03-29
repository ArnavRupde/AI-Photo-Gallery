from pymilvus import MilvusClient, DataType
import random
import json
import requests
import pika
import sys
import os
import time
import base64 

# Milvus connection parameters
CLUSTER_ENDPOINT = "http://localhost:19530/"
TOKEN = "root:Milvus"
MILVUS_COLLECTION_NAME = "intelligent_image_search"

# OLLAMA connection parameters
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_CHAT_GENERATE_ENDPOINT = OLLAMA_BASE_URL + "/generate"
OLLAMA_EMBEDDINGS_ENDPOINT = OLLAMA_BASE_URL + "/embeddings"
OLLAMA_VISION_MODEL = "llava"
OLLAMA_EMBEDDINGS_MODEL = "mistral"

# Embeddings dimensions
EMBEDDINGS_DIMENSIONS = 4096


def main():
    # Set up a Milvus client
    client = MilvusClient(
        uri=CLUSTER_ENDPOINT,
        token=TOKEN 
    )

    # Set up RabbitMQ consumer with callback function
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='image_uploads')

    def callback(ch, method, properties, body):
        message = json.loads(body)
        # Get image path from RabbitMQ
        if 'image_path' not in message:
            print("Invalid message received: " + message)
            return
        
        image_path = message['image_path']
        print(image_path)
        print(f" [x] Received {body}")

        # Encode image to base 64
        base64_encoded_image = None
        with open(image_path, "rb") as image_file:
            base64_encoded_image = base64.b64encode(image_file.read())
        if base64_encoded_image is None:
            print("Error encoding image: " + image_path)
            return
        print("Base64 Encoded image for image: " + image_path)
        print(base64_encoded_image)
        base64_encoded_image_str = base64_encoded_image.decode('ascii')
        
        # Get image description from LLAVA model
        resp = requests.post(
            OLLAMA_CHAT_GENERATE_ENDPOINT,
            json={
                "model": OLLAMA_VISION_MODEL,
                "prompt":"Describe the image in less than 100 characters",
                "stream": False,
                "images": [
                    base64_encoded_image_str
                ]
            }
        )
        if resp.status_code != 200:
            print("Error getting description for image: " + image_path)
            return
        resp = resp.json()
        if 'response' not in resp:
            print("Error getting description for image Error:")
            print(resp)
            return
        image_description = resp['response']
        print("Description for image: " + image_path + ":\n" + image_description)

        # Get vector embedding for image
        resp = requests.post(
            OLLAMA_EMBEDDINGS_ENDPOINT,
            json = {
                "model": OLLAMA_EMBEDDINGS_MODEL,
                "prompt": image_description
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
                " Expected: " + EMBEDDINGS_DIMENSIONS +
                " Got: " + len(embeddings)
            )
            return
        print("Embeddings for image: " + image_path + ":")
        print(embeddings)

        # Insert image description and vector embedding into Milvus
        data = [
            {
                "image_vector": embeddings,
                "image_path": image_path,
                "image_description": image_description
            }
        ]
        res = client.insert(
            collection_name=MILVUS_COLLECTION_NAME,
            data=data
        )
        print("Inserted data into Milvus for image: " + image_path + ":")
        print(res)


    channel.basic_consume(queue='image_uploads', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)