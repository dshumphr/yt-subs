# yt-subs

Simple CLI tool to track a fixed set of YouTube channels and list each channel's most recent full-length upload from the last 24 hours (or a custom window).

## Requirements

- Python 3.10+
- `yt-dlp` (used for channel resolution and video duration lookup)

## Usage

```bash
python3 yt_channel_watch.py add @lourlo
python3 yt_channel_watch.py add @yogscast --name "the yogscast"
python3 yt_channel_watch.py channels
python3 yt_channel_watch.py list
python3 yt_channel_watch.py list --hours 48
python3 yt_channel_watch.py remove @lourlo
```

## Notes

- Channel config is stored at `~/.config/yt-channel-watch/channels.json` by default.
- `list` ignores Shorts and prints title, URL, and duration.
