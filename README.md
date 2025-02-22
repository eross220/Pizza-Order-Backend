# Pizza Ordering System Backend

This is the backend for the Pizza Ordering System project, a FastAPI-based application designed to handle pizza orders, customization, and delivery management.

## Project Setup

### Prerequisites
- **Python 3.11+**
- **Pipenv** or **Virtualenv**
- **PostgreSQL**
  
### Clone the repository

```bash
git clone https://github.com/eross220/Pizza-Order-Backend.git
cd pizza-ordering-system-backend
```

### Install dependencies

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

```bash
alembic upgrade head
```

### Create a .env file
Create a .env file in the root directory with the following variables:

```bash
SQLALCHEMY_DATABASE_URI="postgresql+psycopg://postgres:postgres@localhost/pizza"
API_V1_STR="/api/v1"
PROJECT_NAME="Pizza Ordering System"
```

### Run the application
```bash
uvicorn app.main:app --reload
```

