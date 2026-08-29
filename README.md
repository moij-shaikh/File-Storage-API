# File Storage API

A backend API for Storing File like Images , Text file , Videos etc Online , Build with Python , Fastapi and supabase.

### Features

- User registration and login
- JWT authentication
- Email verification
- Database migrations
- Antivirus support
- file CRUD operation
- File type and size validation

### Tech Stack

- Python
- Fastapi
- Postgresql
- Sqlalchemy
- Alembic
- Supabase
- Redis
- JWT

## Setup

#### 1. Clone the repository

git clone  https://github.com/moij-shaikh/File-Storage-API.git
cd File-Storage-API

#### 2. Create virtual environment

python -m venv .venv

activate it :
.venv\Scripts\activate

#### 3. Install required python modules

pip install -r requirements.txt

#### 4. Configure environment variables

Create .env file containing the required environment variables.
The project uses config.py to load configuration values from the .env file.

###### Example:

- SUPABASE_SECRET_KEY= "your values"
- SUPABASE_URL="your values"

- DATABASE_URL= "your values"
- SESSION_SECRET_KEY= "your values"
- JWT_SECRET_KEY= "your values"
- JWT_ALGORITHM="your values"

- Email_name= "your values"
- Email_pass= "your values"

#### 5. Run database migrations

alembic upgrade head

#### 6. Start Redis

redis-cli

#### 7. Start the API
Run the create_admin.py to make an admin user.


#### 8. Start the API

uvicorn main:app --reload

The APi will be available at:
http://127.0.0.1:8000

API Testing:
http://127.0.0.1:8000/docs

