# GAIR Agent Coding Guidelines

To maintain a clean, maintainable, and robust codebase, all agents and developers must follow these principles.

## 1. Clean Code & SOLID Principles

- **S: Single Responsibility**: Each class/module should have one job. (e.g., `Config` for settings, `Processor` for logic).
- **O: Open/Closed**: Code should be open for extension but closed for modification. Use interfaces or base classes if needed.
- **L: Liskov Substitution**: Derived classes must be substitutable for their base classes.
- **I: Interface Segregation**: Don't force dependencies on methods they don't use.
- **D: Dependency Inversion**: Depend on abstractions, not concretions (e.g., pass the `Config` object instead of hardcoding paths).

## 2. Pythonic Best Practices

- **Type Hinting**: Use `typing` (e.g., `def process(q: str) -> Dict:`) to improve readability and catch bugs.
- **Docstrings**: Every function and class must have a docstring explaining its purpose, inputs, and outputs.
- **Explicit is better than implicit**: Avoid magic numbers; use `Config` or constants.
- **Error Handling**: Use `try...except` blocks with specific exceptions. Never use bare `except:`.

## 3. Project Specific Rules

- **Modularity**: Keep API calls (`client.py`), processing logic (`processor.py`), and RAG (`rag.py`) separate.
- **Paths**: Always use `pathlib.Path` for cross-platform compatibility.
- **Logging**: Log estimated costs and token usage for every campaign.
- **Format**: All predictions must follow the `[Answer] [x]` format to ensure parsing works.
- **Parallelism**: Use `concurrent.futures` for multiple API calls to optimize execution time while respecting rate limits.

## 4. Testing & Verification

- Before committing changes, run at least one `train` run to ensure the parsing and logic are still functional.
- Ensure `kaggle_submission.csv` is generated with the correct 5-column format for `test` mode.
