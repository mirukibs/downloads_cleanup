# The Domain Layer

The Domain Layer encapsulates the core business logic of the Downloads Cleanup application. According to Domain-Driven Design (DDD), this layer is completely isolated; it does not import or depend on the Application or Infrastructure layers. It represents the "truth" of the system.

## Domain Models (`src/domain/models.py`)

Models define the basic data structures the business logic acts upon.

### `FileItem`
A representation of a file in the system. It abstracts away OS-specific paths and focuses on the properties relevant to our domain.

- `name` (str): Base name of the file.
- `path` (str): Absolute file path.
- `size_mb` (float): Size in megabytes.
- `extension` (str): File extension without the leading dot.

### `Action`
A simple record of an operation performed by the system.

- `stage` (str): The step where the action occurred (e.g., `keyword`, `extension`, `archive`, `skip`, `error`).
- `rule_id` (str): Which rule or policy triggered this action.
- `source_path` (str): The original absolute path of the file.
- `target_path` (Optional[str]): The destination path, if moved.
- `error` (Optional[str]): Error message if the action failed.

## Domain Rules (`src/domain/rules.py`)

Rules evaluate `FileItem`s to determine if they match specific criteria and belong in a specific `target` directory.

### `Rule` (Abstract Base Class)
Defines the `matches()` method. Any new routing logic must extend this class.

- **`KeywordRule`**: Checks if the filename contains a specific keyword (case-insensitive).
- **`ExtensionRule`**: Checks if the file extension perfectly matches (e.g., `pdf`, `docx`).
- **`MimeRule`**: Checks the file's MIME type. It supports exact matching (e.g., `application/pdf`) and prefix matching (e.g., `image` matches `image/jpeg` and `image/png`). It uses the `IMimeDetector` port to query the file's type.

## Domain Policies (`src/domain/policies.py`)

Policies handle files that fall through the standard `Rules`. 

### `ArchivePolicy`
Dictates what happens to a file that didn't match any routing rule.
It evaluates:

- **Age**: Is the file older than `max_age_days`?
- **Size**: Is the file too large to archive (`exclude_large_files_over_mb`)?

If the policy determines the file should be archived, it calculates the dynamic target path based on the file's modification date (e.g., `archive_base/YYYY-MM-DD/`).

## Domain Interfaces (Ports) (`src/domain/interfaces.py`)

Ports are interfaces defined in the Domain layer that must be fulfilled by external services (the Infrastructure layer) to allow the Domain to function.

### `IMimeDetector`
To evaluate a `MimeRule`, the Domain needs to know a file's MIME type. However, detecting MIME types often requires native libraries (like `libmagic`), which is an infrastructure concern. The Domain exposes the `IMimeDetector` interface, ensuring it can request this data without caring *how* it's implemented.

---
[Home](index.md) | [Next: Application Layer](02_application.md)
