---
name: ytchannelwatch
description: "Track a fixed list of YouTube channels, manage per-channel tags, and list each channel's most recent full-length upload in a time window. Use this skill whenever the user wants to monitor recent YouTube uploads from specific channels, filter channels by tag regex, or maintain channel/tag lists."
---

# ytchannelwatch

Manage a fixed YouTube channel watchlist and report recent uploads.

## Commands

```bash
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" add <channel_or_handle_or_url>
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" remove <channel_or_id_or_name>
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" channels
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" list [--hours 24] [--tag-regex '<regex>']
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tag-add <channel> <tag1> [tag2 ...]
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tag-remove <channel> <tag1> [tag2 ...]
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tags
```

## Behavior

- Stores channels in `~/.config/yt-channel-watch/channels.json` by default.
- Ignores YouTube Shorts when listing uploads.
- Returns at most one video per channel for the selected time window: the most recent full-length upload.
- Includes title, URL, publish time, and duration in `list` output.
- Supports regex filtering by tag with `--tag-regex`.

## Prerequisites

- Python 3.10+
- `yt-dlp` available on PATH

## Typical workflow

1. Add channels (`add`)
2. Add tags to channels (`tag-add`)
3. Inspect channel+tag mapping (`channels`, `tags`)
4. List uploads (`list`), optionally with `--tag-regex`

## Notes for agents

- If channel resolution by handle/url fails, retry with explicit `--channel-id`.
- Use `channels` to verify state after mutations (`add`, `remove`, `tag-add`, `tag-remove`).
- Preserve user display names and tags unless explicitly asked to change them.
