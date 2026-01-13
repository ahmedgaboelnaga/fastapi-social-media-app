# FastAPI Social Media API

A high-performance, production-ready social media REST API built with **FastAPI**. It includes comprehensive features for user management, posting, and voting, designed for scalability and modern best practices.

## 🌐 Live API & Documentation

- **API Documentation (Swagger UI)**: http://172.161.93.35/api/docs
- **Alternative Docs (ReDoc)**: http://172.161.93.35/api/redoc
- **Web Interface**: http://172.161.93.35/

## 🚀 Key Features

- **User Authentication & Security**
  - Secure registration and login flows.
  - OAuth2 with JWT (JSON Web Tokens) for stateless authentication.
  - Industry-standard password hashing with Bcrypt.
  - Role-based permissions (ownership checks).

- **Post Management**
  - Full CRUD capabilities (Create, Read, Update, Delete).
  - Advanced querying with pagination (limit/offset) and search filters.
  - Optimized database queries using SQLAlchemy relationships.

- **Voting System**
  - Reddit-style upvote/downvote logic.
  - Real-time vote aggregation and consistency checks.
  - Prevention of duplicate voting.

- **Frontend Interface (Bonus)**
  - A clean, Jinja2-based web interface is included to demonstrate API consumption.
  - Features a modern, responsive design for testing the backend logic visually.

## 🛠️ Tech Stack

- **Core Framework**: FastAPI 0.116.1 (Python 3.11+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Validation**: Pydantic
- **Testing**: Pytest & Docker

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 16+
- UV package manager (or pip)

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/ahmedgaboelnaga/fastapi-social-media-app.git
cd fastapi-social-media-app
```

### 2. Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Install dependencies

```bash
uv sync --locked --all-extras --dev
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```env
DATABASE_USERNAME=your_db_username
DATABASE_PASSWORD=your_secure_password
DATABASE_HOSTNAME=localhost              # Use "localhost" for local dev, "postgres" for Docker Compose
DATABASE_PORT=5432
DATABASE_NAME=your_database_name
SECRET_KEY=generate_using_command_below
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Important**: 
> - For **local development**: Use `DATABASE_HOSTNAME=localhost`
> - For **Docker Compose**: Use `DATABASE_HOSTNAME=postgres` (the service name)
> - For **GitHub Actions testing**: Use `DATABASE_HOSTNAME=localhost`

**Generate a secure SECRET_KEY:**

```bash
openssl rand -hex 32
```

### 5. Set up the database

```bash
# Create the database
createdb fastapi_db

# Run migrations
uv run alembic upgrade head
```

## 🚀 Running the Application

### Development Server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Server

```bash
uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## 🐳 Docker

### Using Docker Compose

> **Important**: When using Docker Compose, set `DATABASE_HOSTNAME=postgres` in your `.env` file (the postgres service name). For local development outside Docker, use `DATABASE_HOSTNAME=localhost`.

**Development:**
```bash
# Make sure .env has DATABASE_HOSTNAME=postgres
docker-compose -f docker-compose-dev.yml up
```

**Production:**
```bash
# Make sure .env has DATABASE_HOSTNAME=postgres
docker-compose -f docker-compose-prod.yml up
```

### Build and run with Docker (standalone)

```bash
# Build the image
docker build -t fastapi-social-media .

# Run the container (requires external PostgreSQL)
docker run -p 8000:8000 --env-file .env fastapi-social-media
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_posts.py
```

The test suite uses a separate test database (`fastapi_db_test`) that is automatically created and torn down for each test session.

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Main Endpoints

#### Authentication
- `POST /auth` - Login and get access token

#### Users
- `POST /users` - Register a new user
- `GET /users/{id}` - Get user by ID

#### Posts
- `GET /posts` - Get all posts (with pagination and search)
- `POST /posts` - Create a new post
- `GET /posts/{id}` - Get a specific post
- `PUT /posts/{id}` - Update a post
- `DELETE /posts/{id}` - Delete a post

#### Voting
- `POST /vote` - Vote on a post (upvote/downvote)

### Example Usage

**Register a user:**
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```

**Create a post (authenticated):**
```bash
curl -X POST "http://localhost:8000/posts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Post", "content": "Hello, World!"}'
```

## 🗄️ Database Migrations

### Create a new migration

```bash
uv run alembic revision --autogenerate -m "description of changes"
```

### Apply migrations

```bash
uv run alembic upgrade head
```

### Rollback migration

```bash
uv run alembic downgrade -1
```

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration & db setup
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic schemas
│   └── utils/               # Utility functions
├── static/                  # Static assets
│   ├── css/
│   │   └── style.css        # Main stylesheet (Variables, Theming)
│   └── js/
│       └── main.js          # Frontend logic (Auth, API calls, DOM)
├── templates/               # Jinja2 HTML Templates
│   ├── base.html            # Layout template
│   ├── home.html            # Feed & Index
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   └── my_posts.html
├── alembic/                 # Database migrations
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_posts.py
│   ├── test_users.py
│   └── test_votes.py
├── .github/
│   └── workflows/
│       └── build-deploy.yml # CI/CD pipeline
├── Dockerfile
├── docker-compose-dev.yml
├── docker-compose-prod.yml
├── pyproject.toml           # Project dependencies
└── alembic.ini              # Alembic configuration
```

## 🔄 CI/CD

This project uses GitHub Actions for continuous integration and deployment. The pipeline:

1. Sets up Python 3.11
2. Installs UV and project dependencies
3. Spins up a PostgreSQL service container
4. Creates the test database
5. Runs the complete test suite

The workflow runs on every push and pull request to ensure code quality.

### Required GitHub Secrets

Configure these secrets in your repository settings:

```
DATABASE_USERNAME=postgres          # PostgreSQL default user for GitHub Actions
DATABASE_PASSWORD=<your-password>   # Match the password in services.postgres
DATABASE_HOSTNAME=localhost         # Must be localhost for GitHub Actions services
DATABASE_PORT=5432                  # Must match the port mapping in services
DATABASE_NAME=<your-db-name>        # Base name (test DB will be <name>_test)
SECRET_KEY=<generate-secure-key>    # Use: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Note**: For GitHub Actions CI/CD, the values must match the PostgreSQL service configuration in the workflow file.

## 🔒 Security

- Passwords are hashed using bcrypt
- JWT tokens for stateless authentication
- Pydantic validation for all inputs
- SQL injection protection via SQLAlchemy ORM
- CORS middleware configured
- Environment variables for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Ahmed Gabo Elnaga**
- GitHub: [@ahmedgaboelnaga](https://github.com/ahmedgaboelnaga)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- The Python community for excellent tooling
- UV for modern Python package management

---

⭐ If you found this project helpful, please give it a star!
