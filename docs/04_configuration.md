# Configuration Reference

The `config/config.json` file controls the entire behavior of the Downloads Cleanup Manager. The `JsonConfigAdapter` reads this file and automatically expands the `$HOME` variable into your system's absolute path to your home directory.

## Base Configuration

```json
{
	"paths": {
		"downloads": "$HOME/Downloads",
		"archive_base": "$HOME/downloads_cleanup/data/archive",
		"log_dir": "$HOME/downloads_cleanup/data/logs",
		"cache_dir": "$HOME/downloads_cleanup/data/cache"
	}
}
```
- **`downloads`**: The directory that the Use Case will scan for files.
- **`archive_base`**: The root directory for the `ArchivePolicy` to move un-routed files. It creates subdirectories by date (e.g., `YYYY-MM-DD`).
- **`log_dir`**: The directory to store application logs (`engine.log`).

## Routing Configuration

The `routing` section defines the hierarchical rules that organize your files. **Order of Evaluation**: Keywords -> Extensions -> Mime Type.

```json
"routing": {
	"keyword_map": {
		"invoice": {
			"target": "$HOME/Documents/Finance",
			"scan": "filename"
		}
	},
	"extension_map": {
		"pdf": "$HOME/Documents"
	},
	"mime_map": {
		"image": "$HOME/Pictures",
		"application/pdf": "$HOME/Documents"
	}
}
```

- **`keyword_map`**: Checks if the filename contains the key string. Extremely useful for school subjects (`"lecture"`) or personal labels (`"cv"`).
- **`extension_map`**: Exact match against file extensions. Do not include the leading dot (`.`).
- **`mime_map`**: Matches the exact MIME type (`application/pdf`) or a MIME prefix (`image` matches `image/jpeg` and `image/png`).

## Archiving Policy

Dictates how to handle files that didn't trigger any routing rules.

```json
"archive": {
	"max_age_days": 14,
	"exclude_large_files_over_mb": 500
}
```
- **`max_age_days`**: Files newer than this many days will be skipped and left in your Downloads folder to be reviewed manually.
- **`exclude_large_files_over_mb`**: Extremely large files (e.g., ISOs, large zip files) are ignored by the archiver to prevent accidentally duplicating massive files across disks.

### Email Notifications (`notifications`)

You can receive an email summary of the cleanup process.

```json
"notifications": {
    "email_enabled": true,
    "email_to": "you@example.com",
    "email_from": "downloads-cleanup@localhost",
    "email_format": "html",
    "attach_log": true,
    "smtp": {
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "$SMTP_USER",
        "pass": "$SMTP_PASS",
        "use_tls": true
    }
}
```

> [!IMPORTANT]
> **Security Best Practice:** Do not hardcode your actual email passwords in `config.json`. The configuration parser uses `python-dotenv` to automatically replace values starting with `$` with environment variables.

#### Setting up Gmail App Passwords
If you use Gmail, standard passwords will be blocked. You must use an App Password:

1. Go to your [Google Account Security page](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is enabled.
3. Search for **"App passwords"** and create a new one (e.g., name it `Downloads Cleanup`).
4. Copy the generated 16-character password.

#### Creating the `.env` file
In the root of the project, create or open the `.env` file (which is safely ignored from version control) and add your credentials:

```bash
SMTP_USER=your.email@gmail.com
SMTP_PASS=paste_your_16_char_app_password_here
```

---
[Previous: Infrastructure Layer](03_infrastructure.md) | [Home](index.md)
