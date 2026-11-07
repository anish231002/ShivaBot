  ____  _     _             ____        _   
 / ___|| |__ (_)_   ____ _ | __ )  ___ | |_ 
 \___ \| '_ \| \ \ / / _` ||  _ \ / _ \| __|
  ___) | | | | |\ V / (_| || |_) | (_) | |_ 
 |____/|_| |_|_| \_/ \__,_||____/ \___/ \__|
⚡ A lightweight, extensible Python web application powered by FlaskOverview • Key Features • System Architecture • Directory Breakdown • Installation & Setup • Configuration • Production Deployment • Troubleshooting📖 OverviewShivaBot is a minimalist, production-ready web application built around the Python Flask microframework. It demonstrates clean structural separation between business routing (app6.py), dynamic presentation layers (Jinja2 templates), and static asset delivery (style.css).Whether used as an educational foundation, a microservice dashboard, or a starting template for scalable web utilities, this repository provides zero-overhead execution and straightforward configurability.✨ Key Features🚀 Minimal Overhead: Instant boot times using Flask's lightweight WSGI design.🎨 Responsive UI: Custom CSS styling out of the box, optimized for desktop and mobile viewports.🧱 Server-Side Rendering: Jinja2 templating allows seamless interpolation of dynamic data and template inheritance.🔌 Pluggable Architecture: Easily extendable with blueprint routing, relational databases (SQLAlchemy), and RESTful APIs.🛡️ Secure Baseline: Separation of client assets prevents source code exposure.🏗️ System ArchitectureThe following diagram illustrates how incoming client HTTP requests are received, processed by the WSGI application, merged with template engines, and returned to the browser:+-------------------------------------------------------------+
|                        Client Browser                       |
+-------------------------------------------------------------+
                               |
                        HTTP GET / POST
                               v
+-------------------------------------------------------------+
|               Flask WSGI Application (app6.py)              |
|                                                             |
|   1. Parse Request Context                                  |
|   2. Execute Route Handler                                  |
|   3. Call render_template()                                 |
+-------------------------------------------------------------+
             |                                    |
             v                                    v
+------------------------+           +------------------------+
|   templates/index.html |           |   static/style.css     |
|   (Jinja2 Engine)      |           |   (Direct Asset Serve) |
+------------------------+           +------------------------+
             |                                    |
             +-----------------+------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 Compiled HTTP 200 Response                  |
|                 (HTML + CSS Delivery)                       |
+-------------------------------------------------------------+
📁 Directory Structureflask-app/
├── app6.py               # Main application entry point and routing declarations
├── requirements.txt      # Project dependencies (Flask, Werkzeug, Jinja2, etc.)
├── README.md             # Repository documentation
├── templates/            # Dynamic Jinja2 markup templates
│   └── index.html        # Primary landing page view
└── static/               # Client-facing static assets
    └── style.css         # Custom layout, color scheme, and typography rules
Detailed Component Roles:app6.py: Initializes the Flask(__name__) instance, registers endpoints (e.g., @app.route('/')), manages request/response lifecycles, and executes the development server.templates/index.html: The HTML markup rendered on request. Utilizes Jinja2 delimiters ({{ ... }}, {% ... %}) for dynamic variable binding.static/style.css: Served directly via Flask's /static/ routing helper (url_for('static', filename='style.css')) to control layout presentation.requirements.txt: Pins exact library versions to ensure reproducible environments across operating systems.⚡ Installation & Local SetupPrerequisitesEnsure you have the following installed on your host system:Python 3.9+ (Download)Git (Download)pip (usually bundled with Python)Step-by-Step Guide1. Clone the Repositorygit clone https://github.com/anish231002/ShivaBot.git
cd ShivaBot
2. Set Up a Virtual EnvironmentIsolate dependencies from your system-wide Python installation:python3 -m venv venv
source venv/bin/activate
:: Command Prompt
python -m venv venv
venv\Scripts\activate.bat

:: PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
3. Install Dependenciespython -m pip install --upgrade pip
pip install -r requirements.txt
4. Launch the ApplicationRun the script using Python directly:python app6.py
Or via the native Flask CLI:export FLASK_APP=app6.py
export FLASK_ENV=development
flask run --port=5000
5. Verify the ServerOpen your browser and navigate to:http://127.0.0.1:5000/
⚙️ Configuration & EnvironmentYou can configure Flask execution using standard environment variables:VariableDefault ValueDescriptionFLASK_APPapp6.pyIdentifies the entry point module for the Flask runner.FLASK_ENVproductionSet to development to enable automatic reload and debug views.FLASK_DEBUG0Set to 1 during local dev. Never enable in production.PORT5000Port bound by the HTTP listener.HOST127.0.0.1Bind address (0.0.0.0 to expose to the local network).🚀 Production DeploymentThe built-in development server (python app6.py) is single-threaded and not designed for high-traffic environments. Use an enterprise-grade WSGI server such as Gunicorn or Waitress for production.Option A: Running with Gunicorn (Linux / macOS)Install Gunicorn:pip install gunicorn
Run with multiple workers (recommended: $2 \times \text{CPU cores} + 1$):gunicorn -w 4 -b 0.0.0.0:8000 app6:app
Option B: Docker ContainerizationCreate a Dockerfile in the root directory:FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app6:app"]
Build and run the container:docker build -t shivabot-flask .
docker run -d -p 5000:5000 --name shivabot-app shivabot-flask
🔧 Troubleshooting & FAQCheck that your template references the asset using Flask's url_for:<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
If recent changes are not visible, hard refresh your browser cache using Ctrl + F5 (Windows/Linux) or Cmd + Shift + R (macOS).Another process is using port 5000. You can launch the server on an alternate port:flask run --port=5001
Or find and terminate the occupying process:# Linux / macOS
lsof -ti:5000 | xargs kill -9
Add a new decorator function inside app6.py:@app.route('/about')
def about():
    return render_template('about.html')
Place your corresponding about.html file into the templates/ folder.🗺️ Future Improvements[ ] Add JSON REST API endpoints (/api/v1/...).[ ] Implement database connectivity with SQLAlchemy (SQLite/PostgreSQL).[ ] Add User Authentication (Login, Register, Session Cookies).[ ] Include automated test suites using pytest and coverage.[ ] Setup GitHub Actions CI/CD pipeline for automated testing and linting.🤝 ContributingContributions, issues, and feature requests are welcome!Fork the ProjectCreate your Feature Branch (git checkout -b feature/AmazingFeature)Commit your Changes (git commit -m 'Add some AmazingFeature')Push to the Branch (git push origin feature/AmazingFeature)Open a Pull Request📜 LicenseThis project is licensed under the MIT License — see the LICENSE file for details.
