# AI-Photo-Gallery
Photo Gallery Web App with AI powered Image Search

# Features

- User can upload image
- Images will be automatically indexed in background
- User can search relevant images using text


# Tech Stack

## Backend
- Flask - Python (For serving APIs)
- Milvus Vector Database - (For stroing image metadata, vector embeddings and vector similarity search)
- RabbitMQ (For adding async tasks to be performed by indexing workers)
- OLLAMA (For running AI models locally)

## Frontend
- Next JS
- Tailwind CSS

## AI Models
- Mistra 7B (For generating vector embeddings)
- LLAVA (For generating image description)


# How to run the project?

## Set up Infra
- Run Milvus vector Database as standalone with Docker ( https://milvus.io/docs/install_standalone-docker.md )
- Run RabbitMQ with Docker ( https://www.rabbitmq.com/docs/download )
- Install OLLAMA locally and run 2 models - Mistral and Llava ( https://ollama.com/ )

## Set up backend and fronend
- Run python backend/setup_milvus.py to create a collection in Milvus vector databse (Run only once)
- Navigate to backend directory and run `python app.py` to start serving APIs
- In another terminal, navigate to backend directory and run `python indexing_workers.py` to start indexing workers scripts
- In another terminal, navigate to fronend directory and run `npm run dev` to start next js fronend app


# How it works under the hood?
- User can upload image from the UI
- UI internally backend API to upload the image
- Backend server uploads the image, adds an indexing task in RabbitMQ and returns response to Frontend
- Indexing workers script keep reading data form RabbitMQ. Whenever a new task is added, it performs indexing tasks.
- As part of indexing, following tasks are performed
  1) Call LLAVA model using OLLAMA APIs to get text description from image
  2) Call Mistral model using OLLAMA APIs to get vector embeddings for the image description text
  3) Store image metadata (path, description and vector embeddings) in milvus database
- Whenever user provides search text in UI, an API call is made to backend server
- Backend server performs image similarity search and returns response to frontend
- As part of image similarity search, following tasks are performed
  1) Call Mistral model using OLLAM APIs to get vector embeddings for search text
  2) Call Milvus APIs to find vectors with maximum similarity (k nearest neighbours)
  3) Return image paths for matching similar images









