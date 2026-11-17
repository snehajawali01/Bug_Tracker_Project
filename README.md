# Bug Tracker Project

A full-stack Bug Tracking Application built using FastAPI, PostgreSQL, React, and Vite.

## Features

- User registration and login
- JWT-based authentication
- Role-based permissions
- Create, view, update, and delete bugs
- Assign bugs to users
- Bug priorities and statuses
- Add and view comments
- Dashboard with bug statistics
- PostgreSQL database integration
- Alembic database migrations
- Automated backend tests

## Technology Stack

**Backend**
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg
- Alembic
- Pytest
- JWT authentication

**Frontend**
- React 19
- Vite
- JavaScript
- CSS

## Project Structure

```text
Bug_Tracker_Project/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── schemas/
│   ├── tests/
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## Requirements

- Python
- Node.js and npm
- PostgreSQL

## Backend Setup

Open PowerShell:

```powershell
cd C:\Users\DELL\Desktop\Bug_Tracker_Project\backend
```

Create and activate the virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file inside the backend folder:

```env
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5433
DB_NAME=bug_tracker_db

JWT_SECRET_KEY=your_secure_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Replace the placeholders with your own values. Generate a secure JWT secret using:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never publish your actual `.env` file or credentials.

### Database Setup

Make sure PostgreSQL is running on port 5433.

Create the database if it does not already exist:

```powershell
psql -h localhost -p 5433 -U your_postgres_username -c "CREATE DATABASE bug_tracker_db;"
```

Apply database migrations:

```powershell
alembic upgrade head
```

### Start the Backend

```powershell
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

Health check: http://127.0.0.1:8000/health

## Frontend Setup

Open a second PowerShell window:

```powershell
cd C:\Users\DELL\Desktop\Bug_Tracker_Project\frontend
```

Install dependencies:

```powershell
npm install
```

The frontend defaults to the backend address `http://127.0.0.1:8000`.

To override it, create a frontend `.env` file:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev
```

Open http://localhost:5173 in your browser.

Keep both servers running while using the application.

## Backend Testing

From the backend folder:

```powershell
python -m pytest -v
```

## Frontend Checks

From the frontend folder:

Check code quality:

```powershell
npm run lint
```

Create a production build:

```powershell
npm run build
```

Preview the production build:

```powershell
npm run preview
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a user |
| POST | `/api/auth/login` | User login |
| GET | `/api/auth/me` | Current user |
| POST | `/api/bugs/` | Create a bug |
| GET | `/api/bugs/` | List bugs |
| GET | `/api/bugs/{bug_id}` | Get bug details |
| PUT | `/api/bugs/{bug_id}` | Update a bug |
| DELETE | `/api/bugs/{bug_id}` | Delete a bug |
| POST | `/api/bugs/{bug_id}/assign` | Assign a bug |
| POST | `/api/bugs/{bug_id}/comments` | Add a comment |
| GET | `/api/bugs/{bug_id}/comments` | View comments |

Visit `/docs` on the running backend for complete interactive API documentation.

## Security

- Store credentials in the backend `.env` file.
- Use a strong, unique JWT secret.
- Never commit passwords, tokens, or secret keys.
- Configure production CORS and HTTPS before deployment.

## Project Status

The project includes a React dashboard, FastAPI backend, PostgreSQL integration, authentication, bug management, comments, and automated tests.

Frontend linting and production build checks have passed during development.
