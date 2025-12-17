# Contributing to OOBIR

Thank you for your interest in contributing to OOBIR! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Code of Conduct](#code-of-conduct)
3. [Development Setup](#development-setup)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing Requirements](#testing-requirements)
6. [Submitting Changes](#submitting-changes)
7. [Pull Request Process](#pull-request-process)
8. [Reporting Issues](#reporting-issues)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized development)
- Git for version control
- Basic understanding of FastAPI, pandas, and yfinance

### Fork and Clone the Repository

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/oobir.git
cd oobir

# Add upstream remote
git remote add upstream https://github.com/Greg-2600/oobir.git
```

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

### Expected Behavior

- Be respectful of differing opinions and experiences
- Use welcoming and inclusive language
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Offensive comments or language
- Unwelcome advances or requests
- Posting private information without consent

---

## Development Setup

### Option 1: Local Python Environment (Recommended for Active Development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Verify installation
python flow.py --list
```

### Option 2: Docker Setup (For Testing Across Environments)

```bash
# Build containers
docker compose up -d --build

# Run tests inside container
docker compose exec app python -m pytest -v

# Access Python shell in container
docker compose exec app python
```

### Option 3: Hybrid (Local Code, Docker Services)

```bash
# Start only Ollama and API services
docker compose up -d ollama

# Run local code against Docker services
python flow.py --host http://localhost:11435 AAPL get_fundamentals
```

---

## Code Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications. Key points:

#### Formatting

- **Line Length**: Maximum 100 characters
- **Indentation**: 4 spaces (not tabs)
- **Imports**: 
  - Standard library imports first
  - Third-party imports second
  - Local imports last
  - Alphabetical order within groups

#### Naming Conventions

```python
# Classes: PascalCase
class DataFetcher:
    pass

# Functions and variables: snake_case
def get_stock_data(ticker):
    stock_price = 100.50
    return stock_price

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

#### Docstrings

Use **Google-style docstrings** for all public functions and classes:

```python
def get_fundamentals(ticker: str) -> dict:
    """Fetch fundamental financial data for a stock ticker.

    Retrieves company fundamentals including P/E ratio, market cap,
    earnings per share, and other key metrics using yfinance.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g., 'AAPL', 'MSFT').

    Returns
    -------
    dict
        Dictionary containing fundamental metrics:
        - 'longName': Company name
        - 'currentPrice': Current stock price
        - 'trailingPE': Trailing P/E ratio
        - 'marketCap': Market capitalization
        - And more...

    Raises
    ------
    ValueError
        If ticker is invalid or data unavailable.

    Examples
    --------
    >>> fundamentals = get_fundamentals('AAPL')
    >>> print(fundamentals['currentPrice'])
    150.25
    """
    pass
```

#### Comments

- Write comments that explain **why**, not **what**
- Use `#` for inline comments
- Use `"""docstrings"""` for module, class, and function documentation
- Disable linting rules only when necessary with `# pylint: disable=...`

### Code Quality Tools

#### Linting with Ruff

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

#### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional, Dict, List

def analyze_stock(
    ticker: str,
    historical_days: int = 121,
    use_ai: bool = False
) -> Dict[str, float]:
    """Analyze stock data."""
    pass

def get_multiple_stocks(
    tickers: List[str]
) -> Optional[Dict[str, Dict]]:
    """Get data for multiple stocks."""
    pass
```

---

## Testing Requirements

### Running Tests

```bash
# Run all tests with pytest
python -m pytest -v

# Run specific test file
python -m pytest tests/test_flow.py -v

# Run with coverage report
python -m pytest --cov=. --cov-report=html

# Run tests inside Docker
docker compose exec app python -m pytest -v
```

### Writing Tests

#### Test File Organization

```
tests/
├── test_flow.py           # Tests for flow.py core functions
├── test_flow_api.py       # Tests for flow_api.py endpoints
└── fixtures/              # Shared test data and mocks
    └── sample_data.json
```

#### Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock
import flow

class TestFundamentals:
    """Test suite for fundamental data functions."""

    def test_get_fundamentals_success(self):
        """Test successful fundamental data retrieval."""
        with patch('flow.yf.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {
                'currentPrice': 150.0,
                'trailingPE': 25.5,
            }
            result = flow.get_fundamentals('AAPL')
            assert result['currentPrice'] == 150.0

    def test_get_fundamentals_invalid_ticker(self):
        """Test error handling for invalid ticker."""
        with patch('flow.yf.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {}
            with pytest.raises(ValueError):
                flow.get_fundamentals('INVALID_TICKER')

    @pytest.mark.parametrize("ticker", ['AAPL', 'MSFT', 'TSLA'])
    def test_get_fundamentals_multiple_tickers(self, ticker):
        """Test fundamentals for multiple tickers."""
        # Test implementation
        pass
```

#### Test Best Practices

- **Mock External Services**: Mock yfinance and Ollama calls
- **Use Fixtures**: Create reusable test data
- **Test Edge Cases**: Invalid inputs, missing data, API errors
- **Test Integration**: Ensure components work together
- **Aim for Coverage**: Target >80% code coverage

### Test Coverage Requirements

- **New Functions**: Must have unit tests
- **API Endpoints**: Must have integration tests
- **Bug Fixes**: Must include regression tests
- **Minimum Coverage**: 80% code coverage

### API Endpoint Testing

```bash
# Test all data endpoints (9 endpoints)
./test_data_endpoints.sh http://localhost:8000

# Test all AI endpoints (5 endpoints)
./test_ai_endpoints.sh http://localhost:8000

# Test specific endpoint category manually
curl http://localhost:8000/api/fundamentals/AAPL
curl http://localhost:8000/api/ai/action-recommendation/AAPL
```

---

## Submitting Changes

### Create a Feature Branch

```bash
# Update main branch
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description
```

### Commit Messages

Use clear, descriptive commit messages:

```bash
# Format: <type>(<scope>): <subject>
git commit -m "feat(api): add endpoint for portfolio analysis

This adds a new /api/portfolio/{id} endpoint that aggregates
recommendations for multiple stocks in a portfolio.

- Added portfolio data model
- Added database queries
- Added comprehensive tests
- Updated API documentation"
```

#### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation updates
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **test**: Adding or updating tests
- **chore**: Dependency updates, build changes, etc.

### Before Submitting

```bash
# Update from upstream
git fetch upstream
git rebase upstream/main

# Run tests
python -m pytest -v

# Check code style
ruff check --fix .

# Ensure no uncommitted changes
git status
```

---

## Pull Request Process

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what and why
   - Reference any related issues (#123)
   - Screenshots or examples if applicable

3. **PR Template** (fill out completely):
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Breaking change

   ## Related Issues
   Closes #123

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests passed
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes
   ```

### Review Process

- **Code Review**: At least one maintainer will review
- **CI/CD Checks**: All automated tests must pass
- **Discussion**: Be open to feedback and suggestions
- **Updates**: Push new commits to address review comments
- **Merge**: Approved PRs will be merged to main branch

### After Merge

- Delete your feature branch (local and remote)
- Update your local main: `git pull upstream main`
- Check if your changes are in the next release

---

## Reporting Issues

### Found a Bug?

1. **Check existing issues** first at GitHub Issues
2. **Create detailed bug report** with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Python version, Docker version)
   - Relevant logs or error messages

### Example Bug Report

```markdown
## Bug: API returns 500 when ticker has special characters

### Description
The API endpoint `/api/fundamentals/BRK.B` returns a 500 error 
instead of fetching the data.

### Steps to Reproduce
1. Start API: `docker compose up -d`
2. Call endpoint: `curl http://localhost:8000/api/fundamentals/BRK.B`
3. See error

### Expected Behavior
Should return fundamental data for Berkshire Hathaway Class B

### Actual Behavior
Returns: `{"detail":"Internal Server Error"}`

### Environment
- OS: macOS 13.0
- Python: 3.11.0
- Docker: 24.0.6

### Logs
```
ERROR - yfinance: Failed to download BRK.B: invalid ticker format
```
```

### Feature Requests

Include:
- Clear description of the feature
- Motivation (why this would be useful)
- Proposed implementation approach
- Example usage

---

## Development Workflow Checklist

Before submitting a PR, ensure you've completed:

- [ ] Code follows PEP 8 and project style guidelines
- [ ] All tests pass locally: `python -m pytest -v`
- [ ] Code coverage maintained or improved
- [ ] Docstrings added/updated with Google style
- [ ] Type hints added to function signatures
- [ ] No breaking changes without discussion
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] No debug code or commented-out code left
- [ ] Changes tested in both local and Docker environments

---

## Questions or Need Help?

- **GitHub Issues**: Ask questions in issue discussions
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Contact maintainers directly for sensitive issues

---

## Additional Resources

- [README.md](README.md) - Quick start guide
- [DOCS.md](DOCS.md) - API documentation
- [DOCKER.md](DOCKER.md) - Docker setup
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) - Python style guide
- [Google Python Docstring Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

---

**Thank you for contributing to OOBIR!** 🎉

Your contributions help make this project better for everyone.
