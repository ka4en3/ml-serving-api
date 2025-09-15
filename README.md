# ML Model Serving API

REST API for serving ML models using FastAPI with JWT authentication and role-based access control (RBAC).

## Features

- **FastAPI-based REST API** with automatic OpenAPI documentation
- **Sentiment analysis** using Hugging Face transformers
- **JWT authentication** for secure access
- **Role-based access control (RBAC)** with three roles: Admin, User, Guest
- **User management** system with registration and profile management
- **Automatic model loading** and caching
- **Input validation** with Pydantic
- **Comprehensive error handling**
- **Health check endpoints**

## Quick Start

### Prerequisites

- Python 3.9+
- UV package manager
- Windows/Linux/macOS

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ka4en3/ml-serving-api.git
cd ml-serving-api
```

2Create virtual environment and install dependencies:
```bash
uv venv
uv sync
```

### Running the Application

1. Activate the virtual environment.

2. Start the server:
```bash
uv run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints, you need to:

1. Register a user account or use default accounts
2. Login to receive a JWT token
3. Include the token in the Authorization header: `Bearer <token>`

### Default Users

The system comes with two pre-configured users:

| Username | Password   | Role  | Description |
|----------|-----------|-------|-------------|
| admin    | Admin123!  | Admin | Full access |
| testuser | User123!   | User  | Limited access |

## API Endpoints

### Public Endpoints (No Authentication Required)

#### System Information
- `GET /` - API information and status
- `GET /health` - Service health check

#### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Protected Endpoints (Authentication Required)

#### User Management
- `GET /users/me` - Get current user information
- `PUT /users/me/password` - Change current user password

#### ML Model
- `GET /model/info` - Get model information (any authenticated user)
- `POST /predict` - Make prediction (requires User or Admin role)

### Admin Endpoints (Admin Role Required)

- `GET /admin/users` - List all users
- `POST /admin/users` - Create user with any role
- `DELETE /admin/users/{user_id}` - Delete a user

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "full_name": "New User"
  }'
```

PowerShell:
```powershell
$body = @{
    username = "newuser"
    email = "newuser@example.com"
    password = "SecurePass123!"
    full_name = "New User"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method Post -ContentType "application/json" -Body $body
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=User123!"
```

PowerShell:
```powershell
$form = @{
    username = "testuser"
    password = "User123!"
}

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post -Body $form

$token = $response.access_token
Write-Host "Token: $token"
```

### 3. Make a Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is absolutely amazing!"
  }'
```

PowerShell:
```powershell
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{ text = "This product is absolutely amazing!" } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/predict" `
  -Method Post -Headers $headers -Body $body
```

### 4. Get Current User Info

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 5. Admin: List All Users

```bash
# Login as admin first
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=admin&password=Admin123!"

# Use admin token to list users
curl -X GET "http://localhost:8000/admin/users" \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE"
```

## Role-Based Access Control (RBAC)

The system implements three user roles with different permission levels:

### Roles and Permissions

| Role  | Description | Permissions |
|-------|-------------|-------------|
| **Guest** | Limited access | - View public endpoints<br>- Register account<br>- Login |
| **User** | Standard user | - All Guest permissions<br>- Make predictions<br>- Manage own profile |
| **Admin** | Administrator | - All User permissions<br>- Manage all users<br>- Create users with any role<br>- Delete users |

### Endpoint Access Matrix

| Endpoint | Guest | User | Admin |
|----------|-------|------|-------|
| `GET /` | ✅ | ✅ | ✅ |
| `GET /health` | ✅ | ✅ | ✅ |
| `POST /auth/register` | ✅ | ✅ | ✅ |
| `POST /auth/login` | ✅ | ✅ | ✅ |
| `GET /users/me` | ❌ | ✅ | ✅ |
| `PUT /users/me/password` | ❌ | ✅ | ✅ |
| `GET /model/info` | ❌ | ✅ | ✅ |
| `POST /predict` | ❌ | ✅ | ✅ |
| `GET /admin/users` | ❌ | ❌ | ✅ |
| `POST /admin/users` | ❌ | ❌ | ✅ |
| `DELETE /admin/users/{id}` | ❌ | ❌ | ✅ |

## Security Features

### JWT Token Management
- Tokens expire after 30 minutes (configurable)
- Tokens include user ID, username, and role
- Tokens are signed with a secret key (must be changed in production)

### Password Security
- Passwords are hashed using bcrypt
- Minimum password requirements:
  - At least 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit

### Best Practices
1. **Change the SECRET_KEY** in production (`.env` file)
2. **Use HTTPS** in production environments
3. **Configure CORS** appropriately for your frontend
4. **Implement rate limiting** to prevent brute force attacks
5. **Regular security audits** of dependencies

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
ml-serving-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── ml_service.py        # ML model service
│   ├── config.py            # Configuration
│   ├── auth/                # Authentication module
│   │   ├── __init__.py
│   │   ├── security.py      # JWT and password utils
│   │   ├── dependencies.py  # Auth dependencies
│   │   └── models.py        # Auth models
│   └── database/            # User management
│       ├── __init__.py
│       └── users.py         # User database operations
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API tests
│   └── test_auth.py         # Authentication tests
├── model_cache/             # ML model cache directory
├── .env                     # Environment variables
├── .gitignore
├── pyproject.toml           # Project configuration
└── README.md
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Application settings
APP_NAME="ML Model Serving API"
VERSION="0.2.0"
DEBUG=false

# Model settings
MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english"
MODEL_CACHE_DIR="./model_cache"

# API settings
API_HOST="0.0.0.0"
API_PORT=8000

# CORS settings
ALLOW_ORIGINS=["*"]

# Security settings (CHANGE IN PRODUCTION!)
SECRET_KEY="your-super-secret-key-change-this-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (MUST change in production) | Random string |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |
| `MODEL_NAME` | Hugging Face model name | distilbert-base-uncased-finetuned-sst-2-english |
| `API_PORT` | API server port | 8000 |
| `DEBUG` | Debug mode | false |

## Production Deployment

### Using Docker

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies
RUN uv venv && uv sync --no-dev

# Expose port
EXPOSE 8000

# Run the application
CMD [".venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Build and run:
```bash
docker build -t ml-api .
docker run -p 8000:8000 --env-file .env ml-api
```

### Security Checklist for Production

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use HTTPS with valid SSL certificates
- [ ] Configure CORS for specific domains only
- [ ] Use a production database (PostgreSQL, MySQL)
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Regular security updates
- [ ] Implement backup strategies

## Troubleshooting

### Common Issues

1. **Model download fails**
   - Check internet connection
   - Verify Hugging Face is accessible
   - Check disk space for model cache

2. **JWT token expired**
   - Login again to get a new token
   - Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` if needed

3. **Permission denied errors**
   - Verify user has correct role
   - Check token is included in request
   - Ensure token is valid and not expired

4. **High memory usage**
   - ML models can be memory intensive
   - Consider using smaller models
   - Implement model unloading strategies

## License

MIT License © ka4en3

---

**Version**: 0.2.0  
**Last Updated**: September 2025