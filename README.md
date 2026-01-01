# Acad AI Backend Test

<img src="https://github.com/Benji918/Acad-Assessment-Test/blob/main/assets/img/Exam%20Submission%20and%20Grading-2026-01-01-013337.png" title="ERD project diagram"/>

A robust Django REST Framework application for managing academic assessments with automated grading.

## Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Student, Teacher, and Admin roles
- **Course Management**: Create and manage courses with enrollments
- **Exam System**: Timed exams with multiple question types
- **Secure Submissions**: Students can only view and submit their own answers
- **Automated Grading**: Keyword-based grading with optional AI analysis
- **AI-Powered Insights**: Optional Gemini integration for performance analysis
- **RESTful API**: Clean, well-documented API with Swagger/ReDoc

## Architecture

The project follows SOLID principles and clean architecture:

- **Single Responsibility**: Each service has one clear purpose
- **Open/Closed**: Services are extensible via interfaces
- **Liskov Substitution**: Grading services are interchangeable
- **Interface Segregation**: Minimal, focused interfaces
- **Dependency Inversion**: Services depend on abstractions

## Project Structure

```
assessment_engine/
├── apps/
│   ├── users/          # User management and authentication
│   ├── courses/        # Course and enrollment management
│   ├── exams/          # Exam and question management
│   ├── submissions/    # Submission handling
│   └── grading/        # Grading services (keyword & AI)
├── core/               # Shared utilities, permissions, validators
└── config/             # Django configuration
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd assessment_engine
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Setup database**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

## API Documentation

Access the interactive API documentation:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Key Endpoints

### Authentication
- `POST /api/v1/users/register/` - User registration
- `POST /api/v1/users/login/` - Login (get JWT tokens)
- `POST /api/v1/users/token/refresh/` - Refresh access token

### Courses
- `GET /api/v1/courses/` - List all courses
- `POST /api/v1/courses/` - Create course (teachers only)
- `POST /api/v1/courses/{id}/enroll/` - Enroll in course (students)

### Exams
- `GET /api/v1/exams/` - List exams
- `POST /api/v1/exams/` - Create exam (teachers only)
- `GET /api/v1/exams/{id}/start/` - Start exam (students)

### Submissions
- `POST /api/v1/submissions/submit_exam/` - Submit exam answers
- `GET /api/v1/submissions/{id}/results/` - View graded results

## Grading System

### Keyword-Based Grading
The primary grading method uses:
- Keyword matching against expected answers
- Content density analysis
- Automatic feedback generation

### AI-Powered Analysis (Optional)
When enabled, Gemini AI provides:
- Performance summary
- Strengths identification
- Areas for improvement
- Specific learning suggestions

To enable:
```env
ENABLE_GEMINI_GRADING=True
GEMINI_API_KEY=your-api-key-here
```

## Security Features

- JWT authentication with secure token handling
- Role-based access control
- Input validation and sanitization (XSS prevention)
- SQL injection protection (ORM-based queries)
- Rate limiting on API endpoints
- CORS configuration
- Secure password hashing

## Database Optimization

- Proper indexing on frequently queried fields
- `select_related()` and `prefetch_related()` for query optimization
- Database constraints and unique together fields

## Testing

```bash
python manage.py test
```
