# Flask Application

This is a simple Flask application that serves a static HTML page with some styling.

## Project Structure

```
flask-app
├── app.py
├── requirements.txt
├── templates
│   └── index.html
├── static
│   └── style.css
└── README.md
```

## Setup Instructions

1. Clone the repository or download the project files.
2. Navigate to the project directory.

   ```bash
   cd flask-app
   ```

3. It is recommended to create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the Flask application, execute the following command:

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000/`. Open this URL in your web browser to view the application.

## License

This project is open source and available under the MIT License.