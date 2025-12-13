#!/usr/bin/env python3

"""
cleanup_engine.py - simple skeleton for initial testing.
It validates and prints a summary of the config file.
"""

import json
import argparse
from pathlib import Path
import os
import sys
import shutil
import datetime
import mimetypes

try:
	import magic  # python-magic
	_HAVE_MAGIC = True
except Exception:
	_HAVE_MAGIC = False


def expand_path(raw_path: str) -> Path:
	if not isinstance(raw_path, str):
		raise ValueError(f"Invalid path type (expected string): {raw_path}")

	forbidden_patterns = ["$(", "`", ";", "|", "&"]
	if any(passed_path in raw_path for passed_path in forbidden_patterns):
		raise ValueError(
				f"Forbidden shell-like expression detected in path: {raw_path}\n"
				"Use only '~' or '$HOME' for dynamic user resolution."
			)

	expanded_path = os.path.expandvars(os.path.expanduser(raw_path))
	return Path(expanded_path)


def load_config(config_file_path) -> dict:
	config_file = Path(config_file_path).expanduser()
	if not config_file.is_file():
		raise FileNotFoundError(f"Config file not found: {config_file}")
	return json.loads(config_file.read_text(encoding='utf-8'))


def validate_config_paths(config: dict):
	"""
	Validates all paths in:
		- paths.*
		- routing.keyword_map.*.target
		- routing.extension_map.*
		- routing.mime_map.*
	Every path must exist or we fail immediately.
	"""
	errors = []

	# 1. Validate top-level paths
	paths_section = config.get("paths", {})
	for name, raw_path in paths_section.items():
		resolved = expand_path(raw_path)
		if not resolved.exists():
			errors.append(f"[paths.{name}] Missing directory: {resolved}")

	# 2. Keyword targets
	keyword_map = config.get("routing", {}).get("keyword_map", {})
	for keyword, rule in keyword_map.items():
		target = rule.get("target")
		resolved = expand_path(target)
		if target is None:
			errors.append(f"[keyword_map.{key}] Missing target field")
			continue
		resolved = expand_path(target)
		if not resolved.exists():
			errors.append(f"[keyword_map.{keyword}] Missing target directory: {resolved}")

	# 3. Extension targets
	extension_map = config.get("routing", {}).get("extension_map", {}) or {}
	for extension, raw_target in extension_map.items():
		resolved = expand_path(raw_target)
		if not resolved.exists():
			errors.append(f"[extension_map.{extension}] Missing target directory: {resolved}")

	# 4. MIME targets
	mime_map = config.get("routing", {}).get("mime_map", {}) or {}
	for mime_type, raw_target in mime_map.items():
		resolved = expand_path(raw_target)
		if not resolved.exists():
			errors.append(f"[mime_map.{mime_type}] Missing target directory: {resolved}")

	# FAIL FAST if any error found
	if errors:
		print("CONFIG VALIDATION FAILED:", file=sys.stderr)
		for err in errors:
			print(f"  - {err}", file=sys.stderr)
		sys.exit(3)


def discover_files(downloads_path: Path):
	"""
	Return a list of file Paths in downloads_path.
	- ignores directories
	- ignores hidden files (starting with .)
	- ignores symlinks to dirs (but will include regular symlink files)
	"""
	
	files = []
	
	if not downloads_path.exists():
		return files
	
	for file_entry in downloads_path.iterdir():
		if file_entry.name.startswith("."):
			continue
		
		try:
			if file_entry.is_file():
				files.append(file_entry)
		except Exception:
			continue
	return sorted(files, key=lambda file: file.name.lower())


def match_keyword(filename: str, keyword_map: dict):
	"""
	Case-insensitive substring matching.
	Returns (matched_rule_key, target_path) or (None, None)
	First-match wins in the order of insertion of keyword_map (preserves config order).
	"""
	
	lower_name = filename.lower()
	
	for key, rule in keyword_map.items():
		token = str(key).lower()
		if token in lower_name:
			return key, rule.get("target")
	return None, None


def match_extension(filename: str, extension_map: dict):
	"""
	Match file extension (no dot). Returns (extension, target) or (None, None)
	"""
	
	suffix = Path(filename).suffix.lower().lstrip(".")
	
	if not suffix:
		return None, None
	
	target = extension_map.get(suffix)
	
	if target:
		return suffix, target
	
	return None, None


def detect_mime(path: Path):
	"""
	Return normalized mime string (e.g., 'image', 'video', 'application/pdf', 'text')
	"""
	
	if _HAVE_MAGIC:
		try:
			mime_magic = magic.from_file(str(path), mime=True)
			return mime_magic
		except Exception:
			pass
	
	guessed, _ = mimetypes.guess_type(str(path))
	return guessed or ""


def match_mime(mime_str: str, mime_map: dict):
	"""
	Return (matched_key, target) or (None, None).
	We support:
		- exact mime matches (application/pdf)
		- prefix matches like 'image/' -> map key 'image'
	"""
	
	if not mime_str:
		return None, None
	
	if mime_map.get(mime_str):
		return mime_str, mime_map[mime_str]
	
	prefix = mime_str.split("/", 1)[0]
	if mime_map.get(prefix):
		return prefix, mime_map[prefix]
	
	return None, None


def ensure_dir(path: Path):
	"""Create dir if missing. In strict mode this should already exist for config targets.
	"""
	path.mkdir(parents=True, exist_ok=True)


def make_collision_safe_target(destination_dir: Path, filename: str) -> Path:
	"""If destination/filename exists, append ' (n)' before extension.
	"""

	destination = destination_dir / filename

	if not destination.exists():
		return destination
    
	name = filename
	stem = Path(filename).stem
	suffix = Path(filename).suffix  # includes dot if present
	
	counter = 1
	while True:
		candidate = destination_dir / f"{stem} ({counter}){suffix}"
		if not candidate.exists():
			return candidate
		counter += 1


def do_move(src: Path, destination: Path):
	"""
	Perform safe move: attempt atomic replace if same filesystem, otherwise shutil.move.
	Returns final destination Path.
	"""

	try:
		# create parent if needed (archive subfolder may be autogen)
		destination.parent.mkdir(parents=True, exist_ok=True)

		try:
			os.replace(str(src), str(destination))
		except OSError:
			# fallback
			shutil.move(str(src), str(destination))
		return destination
	except Exception as e:
		raise


def process_run(config: dict, dry_run: bool = True):
	paths = config["paths"]
	downloads = expand_path(paths["downloads"])
	archive_base = expand_path(paths["archive_base"])

	keyword_map = config.get("routing", {}).get("keyword_map", {}) or {}
	extension_map = config.get("routing", {}).get("extension_map", {}) or {}
	mime_map = config.get("routing", {}).get("mime_map", {}) or {}

	# Counters
	counts = {
		"scanned": 0,
		"keyword": 0,
		"extension": 0,
		"mime": 0,
		"archived": 0,
		"errors": 0,
	}

	actions = []  # collect planned actions for dry-run or logging

	files = discover_files(downloads)
	counts["scanned"] = len(files)

	for file in files:
		try:
			filename = file.name
			matched = False

			# 1) keyword
			keyword_key, keyword_target = match_keyword(filename, keyword_map)
			if keyword_key:
				destination_dir = expand_path(keyword_target)
				destination = make_collision_safe_target(destination_dir, filename)
				action = ("keyword", keyword_key, file, destination)
				matched = True
				counts["keyword"] += 1

			# 2) extension
			if not matched:
				extension, extension_target = match_extension(filename, extension_map)
				if extension:
					destination_dir = expand_path(extension_target)
					destination = make_collision_safe_target(destination_dir, filename)
					action = ("extension", extension, file, destination)
					matched = True
					counts["extension"] += 1

			# 3) mime
			if not matched:
				mime_magic = detect_mime(file)
				mime_match, mime_target = match_mime(mime_magic, mime_map)
				if mime_match:
					destination_dir = expand_path(mime_target)
					destination = make_collision_safe_target(destination_dir, filename)
					action = ("mime", mime_match, file, destination)
					matched = True
					counts["mime"] += 1

			# 4) archive fallback
			if not matched:
				today = datetime.date.today().isoformat()
				archive_dir = archive_base / today
				# archive folder may be created here (allowed)
				destination = make_collision_safe_target(archive_dir, filename)
				action = ("archive", "archive_fallback", file, destination)
				counts["archived"] += 1

			# Execute or plan
			if dry_run:
				actions.append(action)
			else:
				stage, rule, src_path, destination_path = action
				# ensure destination parent exists (archive date folder allowed)
				destination_parent = destination_path.parent
				if not destination_parent.exists():
					# Only create archive date folder automatically; do not create other config targets.
					# Enforce strict mode: config target directories must exist (we validated earlier).
					if str(destination_parent).startswith(str(archive_base)):
						destination_parent.mkdir(parents=True, exist_ok=True)
					else:
						raise RuntimeError(f"Destination parent does not exist for non-archive target: {destination_parent}")
				final_destination = do_move(src_path, destination_path)
				actions.append((stage, rule, str(src_path), str(final_destination)))

		except Exception as e:
			counts["errors"] += 1
			actions.append(("error", None, str(file), str(e)))
			continue

	# Summary
	summary = {
		"counts": counts,
		"actions": actions
	}
	return summary


def summarize_config(config_file):
	routing = config_file.get('routing', {})
	keywords = routing.get('keyword_map', {}) or {}
	extensions = routing.get('extension_map', {}) or {}
	mimes = routing.get('mime_map', {}) or {}
	return {
		'keyword_rules': len(keywords),
		'extension_rules': len(extensions),
		'mime_rules': len(mimes)
	}


def pretty_print_plan(summary: dict, dry_run: bool):
	counts = summary["counts"]
	actions = summary["actions"]
	print(f"Total files scanned: {counts['scanned']}")
	print(f"Matched by keyword: {counts['keyword']}")
	print(f"Matched by extension: {counts['extension']}")
	print(f"Matched by mime: {counts['mime']}")
	print(f"Archived fallback: {counts['archived']}")
	print(f"Errors: {counts['errors']}")
	print()

	if dry_run:
		print("Planned actions (dry-run):")
	else:
		print("Performed actions:")
	for action in actions:
		if action[0] == "error":
			print(f"[ERROR] {a[2]} -> {a[3]}")
		else:
			stage, rule, src, destination = action
			print(f"[{stage.upper():7}] {Path(src).name} -> {destination} (rule: {rule})")


def main():
	arg_parser = argparse.ArgumentParser(description="Downloads Cleanup Engine")
	arg_parser.add_argument('--config', required=True, help='Path to config.json')
	arg_parser.add_argument('--dry-run', action='store_true', help='Do not move files')
	args = arg_parser.parse_args()

	try:
		config_file = load_config(args.config)
	except Exception as e:
		print(f"Failed to load config: {e}", file=sys.stderr)
		sys.exit(2)

	# Strict validation (fail-fast)
	validate_config_paths(config_file)

	# Print config summary
	config_summary = summarize_config(config_file)
	print("Config loaded successfully.")
	print(f"Keywords: {config_summary['keyword_rules']}")
	print(f"Extensions: {config_summary['extension_rules']}")
	print(f"MIME rules: {config_summary['mime_rules']}")

	# Run the pipeline
	summary = process_run(config_file, dry_run=args.dry_run)

	# Print plan or results
	pretty_print_plan(summary, dry_run=args.dry_run)

	# Exit
	if summary["counts"]["errors"] > 0:
		sys.exit(4)
	sys.exit(0)


if __name__ == '__main__':
	main()

