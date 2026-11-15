# 🏥 Pharmacy Management Platform

A high-performance, auditable FastAPI backend service for pharmacy inventory management, batch tracking, FEFO (First-Expired, First-Out) stock movements, and compliance reporting.

---

## 🚀 How to Run on Windows

You have two simple ways to run this platform on your Windows machine:

---

### Method 1: Using Docker (Recommended — Full Production Setup)

This starts the entire stack with one command:
- **FastAPI Backend** (`pharmacy-api`) on port `8000`
- **PostgreSQL 16 Database** (`pharmacy-db`) on port `5432`
- **Nginx Reverse Proxy with TLS/SSL** (`pharmacy-nginx`) on ports `8080` (HTTP) and `8443` (HTTPS)

#### Steps:
1. **Start Docker Desktop**:
   - Open **Docker Desktop** from your Windows Start Menu.
   - Wait until the bottom-left indicator shows **Engine running** (green).

2. **Open PowerShell in the Project Folder**:
   - Right-click inside the `Pharmacy Management Platform` folder and choose **Open in Terminal** (or open PowerShell and run):
     ```powershell
     cd "C:\Users\HP\OneDrive\Desktop\Pharmacy Management Platform"
     ```

3. **Start the containers**:
   ```powershell
   docker compose up --build
   ```

4. **Access the application in your browser**:
   - 🖥️ **Pharmacy Web Dashboard UI**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
   - 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - 🔒 **Secure HTTPS Proxy**: [https://localhost:8443/dashboard](https://localhost:8443/dashboard)
   - 📑 **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - 🩺 **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

To stop the containers, press `Ctrl + C` in PowerShell or run:
```powershell
docker compose down
```

---

### Method 2: Running Locally with Python (Fast Development Mode)

You can run the API directly on Windows using Python 3.11 with SQLite (no Docker or PostgreSQL installation required).

#### Steps:

1. **Open PowerShell in the project directory**:
   ```powershell
   cd "C:\Users\HP\OneDrive\Desktop\Pharmacy Management Platform"
   ```

2. **Allow script execution (if prompted by PowerShell)**:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. **Create and activate a virtual environment**:
   ```powershell
   & "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure SQLite database**:
   ```powershell
   $env:DATABASE_URL="sqlite:///./pharmacy.db"
   ```

6. **Start the Uvicorn server**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

7. **Open in your browser**:
   - 🖥️ **Pharmacy Web Dashboard UI**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
   - 📖 **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

*(The database tables and sample pharmacy data will automatically initialize on the first launch!)*

---

## 🧪 Running Automated Tests

To run the unit and integration test suite:

```powershell
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server liveness check |
| `GET` | `/ready` | Database readiness check |
| `GET` | `/api/v1/medicines` | List all medicines |
| `POST` | `/api/v1/medicines` | Add a new medicine |
| `GET` | `/api/v1/batches` | View medicine batches with expiry dates |
| `POST` | `/api/v1/stock/dispense` | Dispense stock (enforces FEFO rules) |
| `GET` | `/api/v1/reports/expiring-soon` | Batches expiring within specified days |

