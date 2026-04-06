# 📦 FastAPI Template

A RESTful API service built with FastAPI that follows Clean Architecture principles.

---

## ✨ Features

- ✅ Clean architecture with clearly separated interfaces, layers, and entities
- 🧩 Dependency Injection using [Dishka](https://github.com/reagento/dishka)
- 🧪 Automatic testing via [pytest](https://docs.pytest.org/en/stable/)
- 🧹 Formatting and static analysis with [ruff](https://github.com/astral-sh/ruff) and [mypy](https://github.com/python/mypy)
- 🐳 Dockerfile following best practices
- 🔁 CI/CD pipeline powered by GitHub Workflows with modular jobs
- 🧷 Integrated [pre-commit](https://github.com/pre-commit/pre-commit) support

---

## ⚙️ Development Setup

### 📥 Install Dependencies

Use `uv` to create a virtual environment and install dependencies:

```bash
make develop
```

### 🐳 Start Local Dev Containers

To launch the PostgreSQL container for local development using Docker Compose:

```bash
make local
```

### 🧪 Run Tests

Make sure containers are running (make local), then execute:

```bash
make test
```

For a manual parallel run:

```bash
.venv/bin/pytest -vx ./tests -vv -n 8
```

### 📈 Apply Database Migrations

Ensure the APP_DB_DSN environment variable is configured correctly, then run:

```bash
make local-apply-migrations
```

### 🏗️ Create a New Database Migration

Before creating a new migration, make sure all existing migrations have been applied:

```bash (at server)
python -m app.adapters.database revision --autogenerate -m "Your message"
```

```bash (locally)
make local-create-migrations
```

### 🔁 Run CI Steps Locally

Use these Makefile commands that mimic the CI process:

```bash
make develop  # Install dependencies
make lint-ci  # Run ruff and mypy (CI lint stage)
make test-ci  # Run tests with coverage + junit report (CI test stage)
```

## 🚦 CI

- GitHub Actions workflow: `.github/workflows/checks.yml`
- Trigger: Pull Request into `dev`
- Stages:
  - `lint` -> `make lint-ci`
  - `test` -> `make test-ci`
- Test artifacts uploaded by CI:
  - `coverage.xml`
  - `junit.xml`

## ⚡ Parallel Tests

- Default local test command (`make test`) runs pytest with xdist: `-n 8`
- CI test command (`make test-ci`) uses coverage + junit output; with current config it also runs tests in parallel (`[tool.coverage.run] command_line = "-m pytest -n auto"`)
- Recommended: avoid running multiple independent pytest sessions against the same DB at the same time

## 📚 API Endpoints

### 👤 Users

```api
GET     /api/v1/users/             Fetch Users
POST    /api/v1/users/             Create User
GET     /api/v1/users/{user_id}/   Fetch User by ID
PATCH   /api/v1/users/{user_id}/   Update User by ID
DELETE  /api/v1/users/{user_id}/   Delete User by ID
```

### 🎬 Movies

```api
GET     /api/v1/movies/            Fetch Movies
POST    /api/v1/movies/            Create Movie
GET     /api/v1/movies/{movie_id}/  Fetch Movie by ID
PATCH   /api/v1/movies/{movie_id}/  Update Movie by ID
DELETE  /api/v1/movies/{movie_id}/  Delete Movie by ID
```
