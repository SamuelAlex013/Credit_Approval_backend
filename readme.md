# Credit Approval System

## Overview
This project is a Credit Approval System built with Django and Django REST Framework. It provides APIs for customer registration, loan eligibility checking, loan creation, and loan viewing. The system supports background data ingestion from Excel files using Celery and is fully containerized with Docker Compose.

## Features
- Customer registration and management
- Loan creation, eligibility check, and management
- Background data ingestion from Excel files (customers and loans)
- RESTful API endpoints
- Robust business logic and error handling
- Dockerized deployment (Postgres, Redis, Celery, Django)
- Automated tests

## Project Structure
```
credit_system/         # Django project settings
loans/                # App with models, views, tasks, helpers, tests
management/commands/   # Custom Django management commands
data/                  # Excel files for data ingestion
docker-compose.yml     # Docker Compose stack
Dockerfile             # Django app Dockerfile
requirements.txt       # Python dependencies
wait-for-it.sh         # Startup script for service orchestration
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.10+ and pip (for local development)

### Quick Start (Docker)
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd Credit_Approval_System
   ```
2. **Build and start the stack:**
   ```sh
   docker-compose up --build
   ```
3. **Run migrations:**
   ```sh
   docker-compose run web python manage.py migrate
   ```
4. **Load data from Excel:**
   ```sh
   docker-compose run web python manage.py load_excel_data
   ```
5. **Run tests:**
   ```sh
   python manage.py test loans.tests
   ```
6. **Access the API:**
   - By default, the API is available at: `http://localhost:8000/`

### Local Development (without Docker)
1. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Set up PostgreSQL and Redis locally, update `credit_system/settings.py` if needed.
3. Run migrations and load data as above.
4. Start the Django server:
   ```sh
   python manage.py runserver
   ```

## API Endpoints

| Endpoint                                 | Method | Description                       |
|------------------------------------------|--------|-----------------------------------|
| `/register/`                             | POST   | Register a new customer           |
| `/check-eligibility/`                    | POST   | Check loan eligibility            |
| `/create-loan/`                          | POST   | Create a new loan                 |
| `/view-loan/<loan_id>/`                  | GET    | View details of a specific loan   |
| `/view-loans/<customer_id>/`             | GET    | View all loans for a customer     |

## Data Ingestion

- Place your Excel files (`customer_data.xlsx`, `loan_data.xlsx`) in the `data/` directory.
- Use the management command to load data:
  ```sh
  python manage.py load_excel_data
  # or with Docker:
  docker-compose run web python manage.py load_excel_data
  ```

## Background Tasks (Celery)
- Celery is used for background data ingestion.
- Redis is used as the message broker.
- The Celery worker is started automatically with Docker Compose.


## Docker Compose Services
- **web**: Django app
- **db**: PostgreSQL database
- **redis**: Redis for Celery
- **worker**: Celery worker for background tasks