# Contributing to Cognitive Traces

Thank you for your interest in contributing to the Cognitive Traces project! We welcome contributions from the community.

## Ways to Contribute

There are many ways you can contribute to this project:

### Report Bugs

If you find a bug, please open an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Python/Node version, etc.)
- Screenshots if applicable

### Suggest Features

Have an idea for a new feature? Open an issue with:
- A clear description of the feature
- Why it would be valuable
- Potential implementation approach
- Examples of similar features in other tools

### Add Dataset Annotations

We're always looking to expand our collection! To contribute annotations:
1. Apply our framework to a new dataset
2. Ensure annotations follow our IFT-based schema
3. Include validation metrics (inter-annotator agreement if applicable)
4. Submit a pull request with the annotated data and documentation

### Improve the Annotator Tool

UI/UX improvements, new features, bug fixes - all welcome:
- Frontend (Next.js/TypeScript)
- Backend (FastAPI/Python)
- Documentation

### Enhance Documentation

Help others understand and use the framework:
- Improve README clarity
- Add tutorials or examples
- Fix typos or broken links
- Translate documentation

### Add Tests

Improve code reliability:
- Unit tests for backend
- Integration tests for API
- E2E tests for frontend

---

## Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of the repository page.

### 2. Clone Your Fork

```bash
git clone https://github.com/searchsim-org/cognitive-traces.git
cd cognitive-traces
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 4. Set Up Development Environment

#### Backend
```bash
cd backend
poetry install
cp .env.example .env
# Add your API keys to .env
```

#### Frontend
```bash
cd frontend
pnpm install
cp .env.local.example .env.local
```

### 5. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 6. Test Your Changes

#### Backend
```bash
cd backend
poetry run pytest
poetry run black .
poetry run isort .
poetry run flake8
```

#### Frontend
```bash
cd frontend
pnpm lint
pnpm type-check
```

### 7. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new cognitive label visualization"
# or
git commit -m "fix: resolve session parsing bug"
```

**Commit Message Convention:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 8. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 9. Create a Pull Request

1. Go to the original repository
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template with:
   - Description of changes
   - Related issues (if any)
   - Screenshots (if UI changes)
   - Testing performed

---

## Pull Request Guidelines

### Before Submitting

- ✅ Code follows project style guidelines
- ✅ All tests pass
- ✅ Documentation is updated
- ✅ Commit messages are clear
- ✅ No unnecessary files included

### PR Review Process

1. **Automated Checks**: CI/CD will run tests and linting
2. **Maintainer Review**: A project maintainer will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged!

### What Makes a Good PR?

- **Focused**: One feature or fix per PR
- **Small**: Easier to review and merge
- **Tested**: Includes tests for new functionality
- **Documented**: Clear description and updated docs
- **Clean**: No unrelated changes or files

---

## Code Style Guidelines

### Python (Backend)

- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort
- **Linting**: flake8
- **Type Hints**: Use type hints where appropriate
- **Docstrings**: Use Google-style docstrings

```python
def annotate_session(session_id: str, events: List[Event]) -> AnnotationResult:
    """
    Annotate a session with cognitive labels using the multi-agent framework.
    
    Args:
        session_id: Unique identifier for the session
        events: List of user events in the session
        
    Returns:
        AnnotationResult containing labeled events and metadata
        
    Raises:
        ValueError: If session_id is empty or events list is invalid
    """
    pass
```

### TypeScript/React (Frontend)

- **Style**: Follow Airbnb style guide
- **Components**: Use functional components with hooks
- **Naming**: PascalCase for components, camelCase for functions
- **Types**: Prefer interfaces over types for object shapes

```typescript
interface SessionViewerProps {
  sessions: Session[]
  selectedSession: Session | null
  onSelectSession: (session: Session) => void
}

export function SessionViewer({ 
  sessions, 
  selectedSession, 
  onSelectSession 
}: SessionViewerProps) {
  // Component implementation
}
```

---

## Testing Guidelines

### Backend Tests

```python
# tests/test_annotation.py
import pytest
from app.services.annotation_service import AnnotationService

def test_annotate_session_with_valid_data():
    service = AnnotationService()
    result = service.annotate_session({
        'session_id': 'test_001',
        'events': [...]
    })
    assert result.session_id == 'test_001'
    assert len(result.annotated_events) > 0
```

### Frontend Tests

```typescript
// components/__tests__/SessionViewer.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { SessionViewer } from '../SessionViewer'

describe('SessionViewer', () => {
  it('renders sessions list', () => {
    const mockSessions = [{ id: '1', name: 'Session 1', events: 5 }]
    render(<SessionViewer sessions={mockSessions} />)
    expect(screen.getByText('Session 1')).toBeInTheDocument()
  })
})
```

---

## Documentation Guidelines

- Use clear, concise language
- Include code examples where helpful
- Keep formatting consistent
- Update relevant sections (README, API docs, etc.)
- Add inline comments for complex logic


## License

By contributing, you agree that your contributions will be licensed under the MIT License.



