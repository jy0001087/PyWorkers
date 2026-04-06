# Workspace AGENTS.md

## Project: TG_Downloader

Telegram media downloader using Telethon. Downloads files from configured groups/topics to `BASE_DIR`.

## Known Bug

**file_indexer.py:52** - `get_group_and_topic_from_path()` has wrong boundary condition:
```python
# 错误
topic_name = path_parts[1] if len(path_parts) > 2 else None
# 应为
topic_name = path_parts[1] if len(path_parts) >= 3 else None
```

When path is `group/file.ext` (2 parts), the current logic incorrectly sets `topic_name = path_parts[1]` (the filename), when it should be `None`.

## Two File Registration Systems

This project has **two separate** file registration systems:
1. `file_register.json` - used by `fileRegis.py` (local registration, keyed by filename+size)
2. `register_file` from `config.py` - used by `file_indexer.py` (group/topic hierarchy, keyed by file_hash)

Do not confuse them. They have different data structures and purposes.

## Key Entry Points

- `get_media.py` - Main script to fetch all media info from configured groups
- `telegram_client.py` - Telegram client setup, entity/topic fetching utilities
- `file_indexer.py` - Scan existing files, build register_file.json, check duplicates by hash
- `fileRegis.py` - Separate file registration CLI tool (standalone, different logic)

## Config

All config in `config.py`:
- `API_ID`, `API_HASH` - Telegram credentials
- `PROXY` - SOCKS5 proxy tuple for Telethon
- `GROUPS` - List of group IDs/usernames to process
- `BASE_DIR` - Download destination
- `REGISTER_FILE` - Path to the hash-based register file

## Dependencies

- `telethon` - Telegram client
- `webdav3.client` - WebDAV support (in fileRegis.py)

No `requirements.txt` or `pyproject.toml` exists. Dependencies are not pinned.

## Logging

`telegram_logger.py` creates log files in `logs/` directory with timestamps in filenames. Each run generates new log files.

## Running Scripts

All scripts are standalone and run with `python <script>.py`. No test suite exists.
