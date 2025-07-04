# Document Ingestion BC

## Document Ingestion BC

This project implements a micro-service API developed with FastAPI. It allows uploading Word documents (`.docx`), processing them through an LLM-powered graph to generate question and answer pairs (Q&A), and subsequently storing them in a vector database using Qdrant. It's designed to facilitate the ingestion and semantic structuring of content from unstructured documents. The rest of the code follows English style standards and comments.

### Index

##### - [Technologies Used](#technologies-used)

##### - [Contents](#contents)

##### - [Application Logic](#application-logic)

##### - [Usage](#usage)

##### - [Done](#done)

##### - [To Do](#to-do)

### Technologies Used

* `uv`: Modern and ultra-fast virtual environment manager, ideal for managing dependencies in reproducible environments. Written in Rust
* `langchain and langgraph`: Frameworks for developing LLM-powered applications.
* `FastAPI`: High-performance asynchronous web framework for building robust and fast APIs.
* `unstructured`: Library for parsing and extracting content from `.docx` files.
* `OpenAI`: Official client for interacting with OpenAI's GPT language models.
* `Qdrant`: Vector database used to store semantic representations of extracted content.
* `specialist`: Bytecode analyzer to improve code in situations requiring optimization.
* `pytest`: Testing framework to ensure system stability through automated tests.

### Contents

* **main.py:** Main file that runs the FastAPI API through the implementation of an interface for changes and testing with other frameworks.
* **src:** Program execution directory. It's divided as follows:
    *  **src/abstractions:** This directory contains the interfaces for the FastAPI framework, the asynchronous Qdrant client, as well as the protocols that API endpoints must follow. This allows us to efficiently mix inheritance and duck typing, maintaining a coherent structure.
    *  **src/application:** The application's business logic. Structured to follow a functional programming style, the directory contains the instantiation of AI engines, the graph flow construction function, graph nodes, the application orchestrator, and node construction instances.
    *  **src/client:** The directory contains the implementation of the asynchronous Qdrant client, based on `aiohttp` and inheriting from the asynchronous client interface created in src/abstractions.
    *  **src/controllers:** This directory contains the API endpoint functions, the FastAPI-specific framework implementation, and the specs that endpoints must follow to be loaded into the framework. The specs pass a check to verify they conform to the protocol established in src/abstractions.
    *  **src/models:** The directory contains all data processing and structuring models based on `pydantic` for the proper functioning of the application.
    *  **src/security:** This directory contains the security layer for accessing the API. It's not implemented in Staging or Development, but should be once it moves to Production.
    *  **src/utils:** The directory contains essential functions and utilities for program operation. Notable are the customizable logs and lazy-type loading and saving functions based on generators.
* **tests/**: Folder with automated tests to ensure correct functionality of each component (parsers, OpenAI logic, endpoints).
* **pyproject.toml:** Configuration file with fixed dependencies and structure based on `uv`.

### Usage

1. **Requirements**

    * Python 3.12.* (strictly for this version)
    * Dependencies:

      ```bash
      uv sync --all-groups
      ```

2. **Configuration**

   All configuration is distributed across several .env files with their corresponding information. It's important to remember that this functionality is set up for development and pre-production testing, having to substitute this logic with Azure Secrets usage in Production.

3. **Execution**

   Run the local server:

   ```bash
   fastapi dev main.py
   ```

   Send a Word document via curl (the example is valid for when it's in an Azure app service):

   ```bash
   curl -X 'POST' \
   'http://127.0.0.1:8000/uploadocs?input_docs_path=assets%2Ftest_doc.docx&upload_author=firstname%20lastname1%20lastname2%20%3Cfirstname%40email.com%3E&doc_name=test_doc.docx&collection=Coll1&update_collection=false' \
   -H 'accept: application/json' \
   -d ''
   ```
   Or via URL request:
   ````bash
   http://127.0.0.1:8000/uploadocs?input_docs_path=assets%2Ftest_doc.docx&upload_author=firstname%20lastname1%20lastname2%20%3Cfirstname%40email.com%3E&doc_name=test_doc.docx&collection=Coll1&update_collection=false
   
   ````
   Query processed and uploaded files with curl:

   ````bash
   curl -X 'GET' \
   'http://127.0.0.1:8000/search?upload_author=firstname%20lastname1%20lastname2%20%3Cfirstname%40email.com%3E&doc_name=test_docs.docx&index=1&order_by=index_id' \
   -H 'accept: application/json'
   ````
   Or via HTTPS request:
   ````bash
   http://127.0.0.1:8000/search?upload_author=firstname%20lastname1%20lastname2%20%3Cfirstname%40email.com%3E&doc_name=test_docs.docx&index=1&order_by=index_id
   ````

4. **Testing**

   Run the test suite:

   ```bash
   pytest  tests
   ```
## Application Logic

![alt text](assets/graph_workflow/graph_workflow.png)

### Done

* Upload of `.docx` files through a REST endpoint.
* Conversion of document content to plain text.
* Generation of Q&A pairs using OpenAI with mocking for testing.
* Insertion of results into a Qdrant collection.
* Modular separation between routes, services, parsing, and storage.
* Implementation of unit tests with `pytest` and `pytest-mock`.
* Reproducible environment configuration with `uv` and `pyproject.toml`.
* Implemented endpoint to facilitate all document searches easily.
* Implemented security and secret securization through API key and hashing.
* Fixed bug in try-except of Qdrant client.
* Improved error information within the microservice.
* Solved RuntimeError of Qdrant client session.
* Improved final result presentation and enriched information given to users in endpoints.
* Enhanced the '/search' endpoint with much more flexible search functionality.
* Updated deprecated typing imports.

### To Do

* ~~Improve error handling and validation of invalid files~~.
* ~~Integration with CI/CD environment for automatic deployments.~~
* ~~Add basic authentication to upload endpoint.~~
* ~~Include usage examples from web interface or Python client.~~
* ~~More detailed Swagger documentation for each endpoint.~~
* ~~Implement an endpoint with indices, titles, and names of those who have used the app to make the `search` endpoint easier to use.~~
* ~~Implement security through Azure secrets.~~
* ~~Fix the bug in the try-except of Qdrant client.~~
* ~~Improve microservice error information by adding more informative Exceptions.~~
* ~~Solve runtime errors found in PRE~~
* ~~Improve final information presentation~~
* ~~Change the '/search' endpoint since with current functionality it throws an Index Out of Range Error when index is entered.~~
* ~~Update deprecated typing imports from Python 3.9 and use built-in types as recommended.~~
* Improve the logging system so that business logic logs and API logs have their own files.
* Implement a lifespan in the application so that a new graph isn't built every time the `uploadocs` POST method is used.