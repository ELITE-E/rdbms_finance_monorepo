
# Simple Finance Tracker (Powered by Custom RDBMS)

This project is a full-stack personal finance application built to demonstrate the implementation of a **Relational Database Management System (RDBMS)** from the ground up. 

Unlike typical web applications that use SQLite or PostgreSQL, this app is powered by **SimpleDB**, a custom-built database engine included in this repository.

## 🚀 Live Demo
**[NONE FOR NOW ]**

---

## 🏗️ Architecture Overview

The project is organized as a **Mono-repo** containing two primary components:

1.  **SimpleDB (RDBMS Engine):** A custom-built library that handles data storage, indexing, and SQL-like query execution using a JSONL (JSON Lines) heap-file architecture.
2.  **Finance Tracker (Web App):** A FastAPI-based application that utilizes SimpleDB as its primary persistence layer for managing users, categories, and transactions.

---

## 🛠️ System Requirements & Tech Stack

### **Prerequisites**
- **Python:** 3.10 or higher
- **Virtual Environment:** Recommended (venv)

### **Core Dependencies**
The following libraries are utilized in this project:
- **FastAPI:** Web framework for the backend.
- **Uvicorn:** ASGI server to run the application.
- **Jinja2:** Template engine for server-side HTML rendering.
- **PyJWT:** JSON Web Token implementation for secure authentication.
- **Passlib [Bcrypt]:** Industry-standard password hashing.
- **Python-Multipart:** Required by FastAPI to handle form data.
- **Chart.js (via CDN):** For financial data visualization.
- **Tailwind CSS (via CDN):** For modern, responsive styling.

---

## 💻 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install the Custom RDBMS Library
From the root directory, install the engine in **editable mode** so the app can access it as a package:
```bash
pip install -e ./simple_rdbms
```

### 4. Install Web Application Dependencies
```bash
pip install -r finance_tracker/requirements.txt
```

### 5. Run the Application
```bash
uvicorn finance_tracker.app.main:app --reload --workers 1
```
*Note: We use `--workers 1` because the custom RDBMS utilizes a Global Thread Lock to manage file-system I/O safely across the web server.*

---

## 📊 RDBMS Specifications (SimpleDB)

SimpleDB was implemented to support the core requirements of relational data management:

- **Storage:** Append-only JSONL heap files with logical deletion (Tombstones).
- **Indexing:** Persisted Hash Indexes for O(1) equality lookups on Primary and Unique keys.
- **Querying:** Supports a subset of SQL including `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, and `INNER JOIN`.
- **Integrity:** Enforces `NOT NULL`, `UNIQUE`, and `PRIMARY KEY` constraints.
- **Random Access:** Uses an RID (Record ID) Directory to map logical records to physical file offsets.

---

## 📁 Project Structure

```text
├── simple_rdbms/           # THE DATABASE ENGINE
│   ├── simpledb/           # Core library code
│   │   ├── storage/        # Heap files & RID management
│   │   ├── index/          # Hash Index implementation
│   │   ├── exec/           # SQL execution & Join logic
│   │   ├── parser.py       # SQL-to-AST parsing
│   │   └── lexer.py        # Tokenization
│   └── pyproject.toml      # Library metadata
│
├── finance_tracker/        # THE WEB APPLICATION
│   ├── app/                # Business logic & Routes
│   │   ├── sql_utils.py    # SQL Safety & Injection Protection
│   │   ├── db_session.py   # DB Singleton & Thread Mutex
│   │   └── services/       # Python-side data aggregation (Analytics)
│   ├── templates/          # Jinja2 HTML views
│   └── requirements.txt    # Fastapi, Jinja2, PyJWT, Passlib, etc.
│
└── Dockerfile              # Deployment configuration for Cloud/Railway
```

---

## 🔒 Security Implementation
- **SQL Injection Protection:** Since SimpleDB is a raw-string-based engine, a dedicated `sql_utils` layer was implemented to sanitize and quote all user inputs before query construction.
- **Session Security:** JWT tokens are stored in `HttpOnly` cookies, preventing client-side script access and mitigating XSS risks.
- **Password Safety:** All user passwords are salted and hashed using the Bcrypt algorithm before storage.

---

## 📝 Academic Notes
- **Aggregation Logic:** Since the RDBMS does not currently support SQL-level aggregates (e.g., `SUM()`), all financial calculations (balance, monthly totals, category breakdowns) are performed in the Application Service layer using Python's list processing.
- **Data Persistence:** In a deployed environment, a persistent volume must be mounted to the `/app/db_data` directory to ensure the JSONL database files survive container restarts.
```

---

### Final Check:
Ensure your `finance_tracker/requirements.txt` file contains exactly this:
```text
fastapi
uvicorn
jinja2
python-multipart
passlib[bcrypt]
pyjwt
```
---

## ⚠️ Important Note

This project was built for educational purposes to demonstrate RDBMS implementation concepts. It is primarily intended for academic evaluation and may have limitations in production environments. If you encounter any issues during setup, please refer to the installation instructions above or open an issue in the repository.
