# Dear Memory

Dear Memory is a cloud-based, voice-activated mobile application designed to help users effortlessly track and locate their personal or work-related belongings. Acting as a smart personal assistant, Dear Memory simplifies item management through an intuitive and user-friendly interface. Users can log and retrieve stored locations using voice commands, ensuring a fast and convenient way to keep track of important items. By leveraging advanced search capabilities and a cloud-powered database, Dear Memory offers a seamless experience for organizing and locating belongings with ease.

---

## Project Setup

Follow these steps to get started with the Dear Memory application:

### Prerequisites

- Python 3.10
- pip (Python package installer)

### Installation

1. Clone the repository:
   ```bash
   git clone {https://github.com/dear-memory.git}
   cd dear_memory
   ```

2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate   # For Linux/Mac
   env\Scripts\activate      # For Windows
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the FastAPI application:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
   - **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---