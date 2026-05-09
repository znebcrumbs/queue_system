# Repository Guidelines

## Project Structure & Module Organization
This project is a Django 5.x application organized into a modular structure under the `apps/` directory to separate concerns and support scalability.

- **`apps/`**: Contains core application logic.
  - `accounts`: Custom `User` model with role-based access control (ADMIN, REGISTRAR, MIS).
  - `queues`: Core queuing logic, including `ServiceType`, `Department`, `QueueEntry`, and the unified `Ticket` model.
  - `audit`: Comprehensive audit logging system for tracking compliance and changes.
  - `survey`: Feedback and rating system for served entries.
- **`config/`**: Project-wide configuration.
  - `settings/`: Split settings into `base.py`, `dev.py`, and `prod.py` for environment-specific configurations.
- **`templates/`**: Centralized HTML templates, organized by app.
- **`static/`**: Static assets (CSS, JS) including Bootstrap 5 and custom AJAX logic for dashboard polling.

## Build, Test, and Development Commands
The project uses `python-decouple` for environment management. Ensure a `.env` file exists based on `.env.example`.

### Development
- **Install dependencies**: `pip install -r requirements.txt`
- **Apply migrations**: `python manage.py migrate`
- **Run server**: `python manage.py runserver`
- **Create superuser**: `python manage.py createsuperuser`

### Verification & Security
- **Security check**: `python manage.py check --deploy`
- **Run tests**: `python manage.py test`
- **Run specific test**: `python manage.py test apps.queues.tests`

## Coding Style & Naming Conventions
- **Imports**: Always use the `apps.<app_name>` convention (e.g., `from apps.accounts.models import User`).
- **Configuration**: Use `decouple.config` for all environment-sensitive settings.
- **Security**: Kiosk endpoints must use `@api_key_required` and `@throttle_kiosk` decorators.
- **Frontend**: Use Bootstrap 5 JS API for modals; avoid legacy jQuery modal plugins.

## Testing Guidelines
- **Framework**: Django's built-in testing framework (`django.test`).
- **Location**: Place unit tests in `apps/<app_name>/tests.py`.
- **Integration**: Integration tests for cross-app functionality (e.g., RBAC) are located in the project root (e.g., `test_phase4_integration.py`).

## Commit & Pull Request Guidelines
- **Commit Messages**: Follow the convention `type(scope): description`.
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`.
  - Example: `feat(rbac): implement cache invalidation for permissions`
- **Pull Requests**: Ensure all security checks pass (`check --deploy`) and migrations are included before merging.
