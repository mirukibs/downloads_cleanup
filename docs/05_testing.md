# Testing Strategy

The **Downloads Cleanup Manager** uses `pytest` to guarantee system stability and prevent regressions. Since the application is built using Domain-Driven Design (DDD), our testing strategy perfectly mirrors the architecture, testing each layer in complete isolation before validating the full pipeline.

## 1. Unit Testing Suite

The unit tests are located in `tests/unit/` and are organized by layer.

### Domain Layer Tests (`tests/unit/domain/`)
Domain tests do not require the file system or configuration files. They purely test business logic.

- `test_models.py`: Validates the `FileItem` model's size calculations and extension parsing.
- `test_rules.py`: Ensures `KeywordRule`, `ExtensionRule`, and `MimeRule` correctly evaluate files based on strict matching logic.
- `test_policies.py`: Verifies `ArchivePolicy` logic for excluding large files and calculating expiration dates.

### Application Layer Tests (`tests/unit/application/`)

- `test_use_cases.py`: Instantiates the `OrganizeDownloadsUseCase` using mock dependencies (in-memory file system and fake configuration). It verifies that files are routed in the correct order: Keywords > Extensions > MIME types > Archive fallback.

### Infrastructure Layer Tests (`tests/unit/infrastructure/`)
Infrastructure tests validate that our adapters correctly interact with Python libraries and the operating system.

- `test_config_parser.py`: Verifies `JsonConfigAdapter` can parse `config.json` and expand environment variables (`$HOME`).
- `test_file_system.py`: Uses `pytest`'s `tmp_path` fixture to write real files to disk and verify `LocalFileSystemAdapter` can safely move them, preventing overwrite collisions.
- `test_magic_mime.py`: Verifies `MagicMimeDetector` interfaces successfully with `python-magic`.
- `test_notifications.py`: Mocks `smtplib` to guarantee that `SmtpNotifier` builds the correct email payload without actually sending emails.

## 2. Integration Testing

The integration test suite is located in `tests/integration/`.

- `test_pipeline.py`: This runs an end-to-end "Dry Run" test. It writes real files to a temporary `downloads/` directory, loads a mock `config.json` file using the real `JsonConfigAdapter`, executes the Use Case using the real `LocalFileSystemAdapter`, and validates that the output actions exactly match expectations.

## 3. Running Tests Locally

To run the entire test suite, open a terminal in the root directory and ensure the conda environment is active:

```bash
conda activate downloads_cleanup
pytest -v tests/
```

## 4. Continuous Integration (CI)

I utilize **GitHub Actions** to automate testing and documentation deployment.

- **`ci.yml`**: Triggers on every push and pull request to the `main` branch. It sets up Miniconda, installs dependencies, and runs `pytest`. If any test fails, the commit is marked with a red cross.
- **`docs.yml`**: Triggers on every push to the `main` branch. It builds this very MkDocs documentation website and automatically deploys it to the `gh-pages` branch.

---
[Previous: Configuration](04_configuration.md) | [Home](index.md)
