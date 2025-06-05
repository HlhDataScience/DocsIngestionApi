# Ingesta Documental BC

## Ingesta Documental BC

Este proyecto implementa una API desarrollada con FastAPI que permite la carga de documentos Word (`.docx`), su procesamiento a través de la API de OpenAI para generar pares de preguntas y respuestas (Q\&A), y su posterior almacenamiento en una base de vectores mediante Qdrant. Está diseñado para facilitar la ingesta y estructuración semántica de contenidos desde documentos sin estructurar. El resto del código sigue los estándares de estilo y comentarios en inglés.

### Índice

##### - [Tecnologías empleadas](#tecnologías-empleadas)

##### - [Contenidos](#contenidos)

##### - [Modo de uso](#modo-de-uso)

##### - [Hecho](#hecho)

##### - [Por hacer](#por-hacer)

### Tecnologías empleadas

* `uv`: Gestor de ambientes virtuales moderno y ultrarrápido, ideal para gestionar dependencias en entornos reproducibles.
* `FastAPI`: Framework web asíncrono de alto rendimiento para construir APIs robustas y rápidas.
* `python-docx`: Librería para analizar y extraer contenido de archivos `.docx`.
* `OpenAI`: Cliente oficial para interactuar con modelos de lenguaje GPT de OpenAI.
* `Qdrant`: Base de datos de vectores utilizada para almacenar representaciones semánticas de los contenidos extraídos.
* `pytest`: Framework de testing para garantizar la estabilidad del sistema mediante pruebas automatizadas.

### Contenidos

* **app/main.py:** Archivo principal que ejecuta la API de FastAPI.
* **app/routes.py:** Define los endpoints para subir documentos y consultar el estado del procesamiento.
* **app/services.py:** Contiene la lógica de negocio para extraer contenido, generar pares Q\&A y realizar inserciones en Qdrant.
* **app/parsers.py:** Encapsula funciones para la lectura y conversión de documentos Word.
* **tests/**: Carpeta con tests automatizados para asegurar la correcta funcionalidad de cada componente (parsers, lógica OpenAI, endpoints).
* **pyproject.toml:** Archivo de configuración con dependencias fijas y estructura basada en `uv`.

### Modo de uso

1. **Requisitos**

   * Python 3.12.\* (estrictamente para esta versión)
   * Dependencias:

     ```bash
     uv sync
     ```

2. **Configuración**

   Configurar tu clave y endpoint de OpenAI en variables de entorno o mediante un archivo `.env`. El cliente se inicializa en `services.py`:

   ```python
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   ```

   También puedes configurar tu host de Qdrant:

   ```python
   qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"))
   ```

3. **Ejecución**

   Ejecutar el servidor local:

   ```bash
   uvicorn app_framework.main:app_framework --reload
   ```

   Enviar un documento Word:

   ```bash
   curl -X POST "http://localhost:8000/upload" -F "file=@test.docx"
   ```

4. **Testing**

   Ejecutar la suite de pruebas:

   ```bash
   pytest --cov=app_framework tests/
   ```

### Hecho

* Subida de archivos `.docx` a través de un endpoint REST.
* Conversión de contenido de documentos en texto plano.
* Generación de pares Q\&A mediante OpenAI con mocking para testeo.
* Inserción de resultados en una colección de Qdrant.
* Separación modular entre rutas, servicios, parsing y almacenamiento.
* Implementación de pruebas unitarias con `pytest` y `pytest-mock`.
* Configuración reproducible de entorno con `uv` y `pyproject.toml`.

### Por hacer

* Mejorar manejo de errores y validación de archivos inválidos.
* ~~Integración con entorno CI/CD para despliegues automáticos.~~
* Agregar autenticación básica al endpoint de subida.
* Incluir ejemplos de uso desde interfaz web o cliente Python.
* Documentación Swagger más detallada para cada endpoint.
