# 天天好學 (FirstToBuzz) - Django Wordle & Quiz Platform

> 📊 **NEW:** [Comprehensive Project Analysis Available](ANALYSIS_SUMMARY.md) - See detailed technical analysis, code quality report, and recommendations.

An educational gaming platform featuring Wordle-style word puzzles and technical knowledge quizzes
focused on Python, Django, HTML, CSS, and JavaScript. Built with Django 5.2 and designed for
progressive enhancement across three development phases.

## Project Overview

**天天好學** (literally "Study Well Every Day") is an interactive learning platform combining word
games with programming knowledge quizzes. The project emphasizes bilingual support
(English/Traditional Chinese), gamification, and community engagement through leaderboards and
multiplayer features.

## Current Status

🚧 **Phase I: In Development** - Backend implementation in progress

- ✅ Project structure scaffolded
- ✅ Internationalization (i18n) configured
- ✅ Base template system established
- ✅ Development environment set up
- 🚧 User authentication system (pending)
- 🚧 Wordle game logic (pending)
- 🚧 Quiz system (pending)

## Tech Stack

### Core
- **Backend**: Django 5.2.8
- **Python**: 3.11
- **Database**: SQLite (development), PostgreSQL (production)
- **Dependency Management**: Poetry

### Frontend
- **HTML5/CSS3**: Semantic markup with modern CSS
- **Bootstrap 5**: Responsive UI framework
- **HTMX**: Dynamic interactions without heavy JavaScript
- **Vanilla JavaScript**: Minimal JS for game mechanics

### Development Tools
- **Testing**: pytest, pytest-django, coverage, factory-boy
- **Code Quality**: ruff, pre-commit, pydocstringformatter
- **Type Checking**: mypy (via django-stubs, django-types)
- **Template Linting**: djlint
- **Documentation**: Sphinx
- **Debug Tools**: django-debug-toolbar, django-extensions

### Deployment
- **Static Files**: whitenoise
- **Environment Config**: django-environ
- **Database Utilities**: django-model-utils

## Project Structure

```
django-wordle/
├── christmax/                 # Django project root
│   ├── christmax/             # Project settings
│   │   ├── settings.py        # Configuration
│   │   ├── urls.py            # URL routing
│   │   └── wsgi.py/asgi.py    # WSGI/ASGI applications
│   ├── base/                  # Base template hierarchy
│   │   ├── templates/         # Shared templates
│   │   │   ├── base.html      # Base template
│   │   │   ├── includes/      # Reusable components
│   │   │   └── _dev/          # Development pages
│   │   ├── static/            # Shared static assets
│   │   │   ├── css/           # Stylesheets
│   │   │   └── js/            # JavaScript
│   │   ├── locale/            # Translation files
│   │   │   ├── en/            # English translations
│   │   │   └── zh/            # Traditional Chinese
│   │   ├── tests/             # i18n tests
│   │   └── views.py           # Base views
│   └── manage.py              # Django CLI
├── pyproject.toml             # Poetry dependencies
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Features by Phase

### Phase I: Single Player (Current)
**Target**: Core single-player experience with user authentication

- **Landing Page**: Marketing content, feature highlights, call-to-action
- **User System**: Registration, login, profile management
  * To setup SSO via Google/GitHub. Social apps need to be created in social app table
- **Wordle Game**:
  - 5-letter word guessing (6 attempts)
  - Color-coded feedback (green/yellow/gray)
  - Daily challenges
  - Score tracking and streaks
- **Quiz System**:
  - Multiple choice questions
  - 5 categories: Python, Django, HTML, CSS, JavaScript
  - 3 difficulty levels: Easy, Medium, Hard
  - Timer functionality
- **Leaderboard**: Rankings, stats, filtering (daily/weekly/all-time)
- **Internationalization**: English and Traditional Chinese support

## Installation

### Prerequisites
- Python 3.11
- Poetry (dependency management)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django-wordle
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Activate virtual environment**
   ```bash
   poetry shell
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file (use .env.dev as template)
   cp .env.dev .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   cd christmax
   python manage.py migrate
   ```

6. **Compile translation files**
   ```bash
   python manage.py compilemessages
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - English: http://localhost:8000/
   - Traditional Chinese: http://localhost:8000/zh-hant/

## Development Workflow

### Code Quality
```bash
ruff check          # Lint code
ruff format         # Format code
mypy .              # Type checking
djlint .            # Template linting
```

### Testing
```bash
pytest              # Run all tests
coverage run -m pytest    # Run with coverage
coverage report     # View coverage report
```

### Internationalization

The project uses a **modular translation system** to separate concerns and simplify maintenance. See [`docs/translation-system.md`](docs/translation-system.md) for detailed documentation.

```bash
# Quick Start (from christmax/ directory)
make compile         # Merge & compile translations
make update          # Extract new strings to app.po
make stats           # Show translation statistics

# Or use management command directly
python manage.py compile_translations --locale zh
```

**Translation Files** (`christmax/base/locale/zh/LC_MESSAGES/`):
- `manual.po` - Manual overrides (highest priority)
- `app.po` - Custom project strings
- `allauth.po` - Django-allauth translations
- `django-core.po` - Django core translations
- `djangojs.po` - JavaScript translations (separate domain)

Files are automatically merged in priority order (manual → app → allauth → django-core) and compiled to `django.mo` and `djangojs.mo`.

### Pre-commit Hooks
```bash
pre-commit install          # Set up hooks
pre-commit run --all-files  # Run manually
```

## Configuration

### Key Settings

**Internationalization** (christmax/settings.py):
```python
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('zh-hant', 'Traditional Chinese'),
]
USE_I18N = True
LOCALE_PATHS = [BASE_DIR / 'base' / 'locale']
```

**URL Structure**:
- `/` - English (default, no prefix)
- `/zh-hant/` - Traditional Chinese
- Uses `i18n_patterns()` with `prefix_default_language=False`

**Static Files**:
- Development: Django's staticfiles app
- Production: WhiteNoise for efficient serving

## Design Principles

### Color Scheme
- **Primary**: Indigo (#6366f1)
- **Secondary**: Purple (#8b5cf6)
- **Wordle Feedback**:
  - Hit: Green (#10b981)
  - Present: Orange (#f59e0b)
  - Miss: Gray (#6b7280)

### Category Colors
- Python: Blue (#3776ab)
- Django: Dark Green (#092e20)
- HTML: Orange (#e34c26)
- CSS: Blue (#264de4)
- JavaScript: Yellow (#f0db4f)

### Architecture Decisions
- **Pure Django Templates**: No React/Vue/Angular - keep it simple
- **Progressive Enhancement**: HTMX for dynamic features
- **Mobile-First**: Bootstrap responsive design
- **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
- **i18n from Day 1**: Built-in bilingual support

## Documentation

### Project Analysis (NEW)

Comprehensive analysis of the project's current state:

- **[Analysis Summary](ANALYSIS_SUMMARY.md)** - Executive summary with key findings and action items
- **[Project Analysis](PROJECT_ANALYSIS.md)** - Complete technical architecture and feature review (500+ lines)
- **[Code Quality Report](CODE_QUALITY_REPORT.md)** - Test results, linting analysis, and security audit

### Technical Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

- **[OAuth Authentication & Account Linking](docs/oauth-authentication.md)** - Comprehensive guide covering Google OAuth integration, account linking behavior, email verification, edge cases, and security considerations.
- **[Translation System](docs/translation-system.md)** - Modular translation architecture and workflow

See the [docs README](docs/README.md) for a complete list of available documentation.

## Testing

The project includes comprehensive test coverage:

### Test Structure
```
base/tests/
├── test_i18n_settings.py    # i18n configuration tests
├── test_i18n_urls.py         # URL pattern tests
└── test_language_switch.py   # Language switching tests
users/
├── test_social_auth.py       # OAuth authentication tests
├── test_models.py            # User model tests
└── test_admin_auth.py        # Admin authentication tests
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest christmax/base/tests/test_i18n_urls.py

# With coverage
coverage run -m pytest
coverage html  # Generate HTML report
```

## Contributing

### Branch Strategy
- `main` - Stable production code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Commit Guidelines
- Follow conventional commits format
- Write clear, descriptive commit messages
- Reference issues/tickets where applicable

### Code Standards
- Follow PEP 8 (enforced by ruff)
- Write docstrings (Google style)
- Maintain >80% test coverage
- Use type hints for function signatures
- Keep functions focused and testable

## Acknowledgments

- Inspired by NYTimes Wordle: https://www.nytimes.com/games/wordle/
- Django documentation: https://docs.djangoproject.com/
- Bootstrap: https://getbootstrap.com/

## Roadmap

- [x] Phase I planning complete
- [x] Project scaffolding
- [x] i18n implementation
- [ ] User authentication system
- [ ] Wordle game backend
- [ ] Quiz system backend
- [ ] Phase I frontend integration
- [ ] Phase II planning
- [ ] Multiplayer features
- [ ] Phase III planning
- [ ] AI assistant integration
- [ ] Payment system integration

---

**Status**: Active Development | **Version**: 0.0.1 | **Phase**: I
