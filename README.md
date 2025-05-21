# Multi-Agent Backend System

This project is a simplified backend system using a single model approach to reduce costs. It leverages ChromaDB for document and template storage and OpenAI's API for generating workflows. The backend is implemented using FastAPI.

## Features

- **Single Model Approach**: Utilizes a single model to handle requests, reducing complexity and cost.
- **ChromaDB Integration**: Stores and retrieves documentation and templates.
- **OpenAI API**: Generates workflows based on retrieved data.
- **FastAPI**: Provides a robust and scalable server framework.

## Prerequisites

- Python 3.8+
- FastAPI
- ChromaDB
- OpenAI API Key

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory and add your OpenAI API key:

```plaintext
OPENAI_API_KEY=your_openai_api_key
```

### 5. Start ChromaDB

ChromaDB runs as a server that your application connects to. Follow these steps to set it up:

1. **Install ChromaDB**:
   ```bash
   pip install chromadb
   ```

2. **Set Environment Variables**:
   Create or update your `.env` file with these ChromaDB-specific variables:
   ```plaintext
   CHROMA_HOST=localhost
   CHROMA_PORT=8000
   CHROMA_COLLECTION=architect-docs
   COMPONENT_DOCS_DIR=docs
   COMPONENT_TEMPLATES_DIR=component_categories
   ```

3. **Start ChromaDB Server**:
   ```bash
   chroma run --host localhost --port 8000
   ```

4. **Verify ChromaDB is Running**:
   In a new terminal window, you can test if the server is running:
   ```bash
   curl http://localhost:8000/api/v1/heartbeat
   ```
   You should receive a response indicating the server is alive.

### 6. Seed the Database

Once ChromaDB is running, seed it with documentation and templates:

1. **Ensure Directory Structure**:
   Make sure you have the following directories with their respective files:
   - `docs/` - Contains markdown (.md) documentation files
   - `component_categories/` - Contains JSON template files

2. **Run the Seeding Script**:
   ```bash
   python3 Scripts.seed_component_docs
   ```
   This script will:
   - Initialize connection to ChromaDB
   - Seed component documentation from markdown files
   - Seed component templates from JSON files
   - Log the progress in the console

You can verify the seeding was successful by checking the logs output. Each successful document and template addition will be logged with a unique ID.

If you need to check what's in the database after seeding, you can run:
```bash
python3 Scripts.whatsinthedb
```

### 7. Run the Backend Server

Start the FastAPI server:

```bash
uvicorn singleModel:app --reload
```

The server will be available at `http://localhost:8000`.

## Usage

### Endpoint: `/design`

- **Method**: POST
- **Request Body**: JSON object with a `prompt` field.
- **Response**: JSON object containing the generated workflow.

Example request:

```json
{
  "prompt": "Create a document Q&A system"
}
```

### Logging

The system logs detailed information about the retrieval and processing of documents and templates. Logs are stored in `logs/` directory.

## Code Overview

### `singleModel.py`

This file contains the main logic for generating workflows using the RAG pattern. It retrieves relevant documentation and templates from ChromaDB and uses OpenAI's API to generate a workflow.

### `server.py`

This file sets up the FastAPI server and defines the API endpoints. It handles incoming requests and returns the generated workflows.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## License

This project is licensed under the MIT License.