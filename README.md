# Notisense

Notisense is a Notification Service built with **FastAPI** and deployed
on **AWS Lambda** via **GitHub Actions**.\
It is designed to provide scalable, event-driven notifications with
email support.

------------------------------------------------------------------------

## 🚀 Features

-   FastAPI-based RESTful notification service.
-   Email support with **FastAPI-Mail**.
-   AWS Lambda + API Gateway deployment.
-   CI/CD with GitHub Actions using Poetry.
-   Database support with SQLAlchemy & Alembic migrations.

------------------------------------------------------------------------

## 🛠️ Tech Stack

-   **Backend**: FastAPI, SQLAlchemy, Pydantic
-   **Email**: FastAPI-Mail, SMTP
-   **Database**: PostgreSQL (asyncpg)
-   **Serverless**: AWS Lambda, AWS S3
-   **CI/CD**: GitHub Actions
-   **Dependency Management**: Poetry

------------------------------------------------------------------------

## 📦 Installation

Clone the repo and install dependencies with Poetry:

``` bash
git clone https://github.com/your-username/notisense.git
cd notisense
poetry install
```

To run locally:

``` bash
poetry run uvicorn NotificationService.main:app --reload
```

------------------------------------------------------------------------

## ⚡ Environment Variables

Create a `.env` file with the following values:

``` env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
SECRET_KEY=your-secret-key
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
MAIL_FROM=your-email
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

------------------------------------------------------------------------

## 🚀 Deployment (AWS Lambda)

This project is configured with **GitHub Actions** to automatically
deploy to AWS Lambda.

### CI/CD Flow

1.  On push to `prod` branch, GitHub Actions:
    -   Installs dependencies with Poetry.
    -   Builds a deployment zip with app code & dependencies.
    -   Uploads zip to AWS S3.
    -   Updates AWS Lambda function.

To trigger deployment:

``` bash
git push origin prod
```

------------------------------------------------------------------------

## 📂 Project Structure

    notisense/
    │── src/                          # Main FastAPI app
    │── tests/                        # Test suite
    │── pyproject.toml                # Poetry dependencies
    │── poetry.lock                   # Locked dependencies
    │── .github/workflows/dev.yml     # CI/CD workflow
    │── README.md

------------------------------------------------------------------------

## 🧪 Running Tests

``` bash
poetry run pytest -q
```

------------------------------------------------------------------------

## 📌 Roadmap

-   [x] Setup FastAPI project structure
-   [x] Add email notifications
-   [x] Setup AWS Lambda deployment
-   [ ] Add SMS/Push notifications
-   [ ] Add monitoring & logging

------------------------------------------------------------------------

## 🤝 Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/YourFeature`).
3.  Commit changes (`git commit -m 'Add some feature'`).
4.  Push branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

------------------------------------------------------------------------

## 📜 License

MIT License © 2025 Notisense
