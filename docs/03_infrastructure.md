# The Infrastructure Layer

The Infrastructure Layer contains concrete implementations (Adapters) for all the interfaces (Ports) defined in the Domain and Application layers. This layer is highly coupled to external frameworks, the operating system, databases, and third-party libraries.

## Config Adapter (`src/infrastructure/config_parser.py`)

### `JsonConfigAdapter`
Implements `IConfigProvider`.

- Reads `config/config.json`.
- Dynamically expands the `$HOME` environment variable for all path-related strings to ensure cross-user compatibility.
- Provides structured dictionaries directly to the Application Use Case to construct Rules and Policies.

## File System Adapter (`src/infrastructure/file_system.py`)

### `LocalFileSystemAdapter`
Implements `IFileSystem`.

- Uses standard Python libraries (`os`, `shutil`, `pathlib`) to interact with the local disk.
- Converts raw file paths into Domain `FileItem` objects by calculating sizes and timestamps.
- Handles directory creation and safe file moves, catching permission errors and raising them cleanly for the Use Case to log.

## MIME Detection (`src/infrastructure/magic_mime.py`)

### `MagicMimeDetector`
Implements `IMimeDetector` (Domain Port).

- Wraps the `python-magic` library (libmagic) to perform deep byte-level inspection of files.
- Provides highly accurate MIME type resolution (e.g., distinguishing a renamed `.txt` file that is actually a `.pdf`).

## Notifications (`src/infrastructure/notifications.py`)

### `SmtpNotifier`
Implements `INotifier`.

- Uses Python's built-in `smtplib` and `email` packages.
- Reads SMTP credentials and preferences from the configuration.
- Constructs an HTML summary of all `Action`s performed during the run.
- Attaches the raw `.log` file if configured.

## Dependency Injection (`src/main.py`)

The `main.py` entrypoint acts as the Composition Root. It has full knowledge of all layers and is responsible for wiring them together.

It instantiates the concrete Infrastructure classes and passes them into the Application's Use Case:

```python
# main.py Snippet
config_provider = JsonConfigAdapter(args.config)

file_system = LocalFileSystemAdapter()
notifier = SmtpNotifier(config_provider)
mime_detector = MagicMimeDetector()

use_case = OrganizeDownloadsUseCase(
    file_system=file_system,
    config_provider=config_provider,
    notifier=notifier,
    mime_detector=mime_detector
)

summary = use_case.execute(dry_run=args.dry_run)
```

---
[Previous: Application Layer](02_application.md) | [Home](index.md) | [Next: Configuration](04_configuration.md)
