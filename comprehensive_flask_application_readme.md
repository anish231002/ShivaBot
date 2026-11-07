<div align="center">

```
  ____  _     _             ____        _   
 / ___|| |__ (_)_   ____ _ | __ )  ___ | |_ 
 \___ \| '_ \| \ \ / / _` ||  _ \ / _ \| __|
  ___) | | | | |\ V / (_| || |_) | (_) | |_ 
 |____/|_| |_|_| \_/ \__,_||____/ \___/ \__|
```

### ⚡ *A lightweight, extensible Python web application powered by Flask*

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=flat-square)](https://github.com/anish231002/ShivaBot)

[Overview](#-overview) • [Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Directory Breakdown](#-directory-structure) • [Installation & Setup](#-installation--local-setup) • [Configuration](#-configuration--environment) • [Production Deployment](#-production-deployment) • [Troubleshooting](#-troubleshooting--faq)

---

</div>

## 📖 Overview

**ShivaBot** is a minimalist, production-ready web application built around the **Python Flask** microframework. It demonstrates clean structural separation between business routing (`app6.py`), dynamic presentation layers (Jinja2 templates), and static asset delivery (`style.css`).

Whether used as an educational foundation, a microservice dashboard, or a starting template for scalable web utilities, this repository provides zero-overhead execution and straightforward configurability.

---

## ✨ Key Features

- **🚀 Minimal Overhead**: Instant boot times using Flask's lightweight WSGI design.
- **🎨 Responsive UI**: Custom CSS styling out of the box, optimized for desktop and mobile viewports.
- **🧱 Server-Side Rendering**: Jinja2 templating allows seamless interpolation of dynamic data and template inheritance.
- **🔌 Pluggable Architecture**: Easily extendable with blueprint routing, relational databases (SQLAlchemy), and RESTful APIs.
- **🛡️ Secure Baseline**: Separation of client assets prevents source code exposure.

---

## 🏗️ System Architecture

The following diagram illustrates how incoming client HTTP requests are received, processed by the WSGI application, merged with template engines, and returned to the browser:

```
+-------------------------------------------------------------+
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
```

---

## 📁 Directory Structure

```
flask-app/
├── app6.py               # Main application entry point and routing declarations
├── requirements.txt      # Project dependencies (Flask, Werkzeug, Jinja2, etc.)
├── README.md             # Repository documentation
├── templates/            # Dynamic Jinja2 markup templates
│   └── index.html        # Primary landing page view
└── static/               # Client-facing static assets
    └── style.css         # Custom layout, color scheme, and typography rules
```

### Detailed Component Roles:
- **`app6.py`**: Initializes the `Flask(__name__)` instance, registers endpoints (e.g., `@app.route('/')`), manages request/response lifecycles, and executes the development server.
- **`templates/index.html`**: The HTML markup rendered on request. Utilizes Jinja2 delimiters (`{{ ... }}`, `{% ... %}`) for dynamic variable binding.
- **`static/style.css`**: Served directly via Flask's `/static/` routing helper (`url_for('static', filename='style.css')`) to control layout presentation.
- **`requirements.txt`**: Pins exact library versions to ensure reproducible environments across operating systems.

---

## ⚡ Installation & Local Setup

### Prerequisites

Ensure you have the following installed on your host system:
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **pip** (usually bundled with Python)

### Step-by-Step Guide

#### 1. Clone the Repository
```bash
git clone https://github.com/anish231002/ShivaBot.git
cd ShivaBot
```

#### 2. Set Up a Virtual Environment
Isolate dependencies from your system-wide Python installation:

<details open>
<summary><b>macOS / Linux</b></summary>

```bash
python3 -m venv venv
source venv/bin/activate
```
</details>

<details>
<summary><b>Windows (Command Prompt / PowerShell)</b></summary>

```cmd
:: Command Prompt
python -m venv venv
venv\Scripts\activate.bat

:: PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
</details>

#### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Launch the Application
Run the script using Python directly:
```bash
python app6.py
```

Or via the native Flask CLI:
```bash
export FLASK_APP=app6.py
export FLASK_ENV=development
flask run --port=5000
```

#### 5. Verify the Server
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## ⚙️ Configuration & Environment

You can configure Flask execution using standard environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FLASK_APP` | `app6.py` | Identifies the entry point module for the Flask runner. |
| `FLASK_ENV` | `production` | Set to `development` to enable automatic reload and debug views. |
| `FLASK_DEBUG` | `0` | Set to `1` during local dev. **Never enable in production.** |
| `PORT` | `5000` | Port bound by the HTTP listener. |
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` to expose to the local network). |

---

## 🚀 Production Deployment

The built-in development server (`python app6.py`) is single-threaded and not designed for high-traffic environments. Use an enterprise-grade WSGI server such as **Gunicorn** or **Waitress** for production.

### Option A: Running with Gunicorn (Linux / macOS)

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Run with multiple workers (recommended: $2 \times \text{CPU cores} + 1$):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app6:app
   ```

### Option B: Docker Containerization

Create a `Dockerfile` in the root directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app6:app"]
```

Build and run the container:
```bash
docker build -t shivabot-flask .
docker run -d -p 5000:5000 --name shivabot-app shivabot-flask
```

---

## 🔧 Troubleshooting & FAQ

<details>
<summary><b>Q: CSS styles are not loading or showing updates.</b></summary>

- Check that your template references the asset using Flask's `url_for`:
  ```html
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  ```
- If recent changes are not visible, hard refresh your browser cache using `Ctrl + F5` (Windows/Linux) or `Cmd + Shift + R` (macOS).
</details>

<details>
<summary><b>Q: "Address already in use" error when starting the server.</b></summary>

Another process is using port `5000`. You can launch the server on an alternate port:
```bash
flask run --port=5001
```
Or find and terminate the occupying process:
```bash
# Linux / macOS
lsof -ti:5000 | xargs kill -9
```
</details>

<details>
<summary><b>Q: How do I add new pages/routes?</b></summary>

Add a new decorator function inside `app6.py`:
```python
@app.route('/about')
def about():
    return render_template('about.html')
```
Place your corresponding `about.html` file into the `templates/` folder.
</details>

---

## 🗺️ Future Improvements

- [ ] Add JSON REST API endpoints (`/api/v1/...`).
- [ ] Implement database connectivity with SQLAlchemy (`SQLite`/`PostgreSQL`).
- [ ] Add User Authentication (Login, Register, Session Cookies).
- [ ] Include automated test suites using `pytest` and `coverage`.
- [ ] Setup GitHub Actions CI/CD pipeline for automated testing and linting.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.