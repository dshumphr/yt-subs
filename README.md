# yt-subs

Simple CLI tool to track a fixed set of YouTube channels and list each channel's most recent full-length upload from the last 24 hours (or a custom window).

## Requirements

- Python 3.10+
- `yt-dlp` (used for channel resolution and video duration lookup)

## Usage

```bash
SKILL_DIR="$HOME/.config/crush/skills/ytchannelwatch"
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" add @lourlo
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" add @yogscast --name "the yogscast"
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tag-add @lourlo league toplane
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tag-remove @lourlo toplane
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" tags
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" channels
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" list
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" list --hours 48 --tag-regex "league|variety"
python3 "$SKILL_DIR/scripts/yt_channel_watch.py" remove @lourlo
```

## Skill packaging

This repo also includes an Anthropic-style skill for Crush in `ytchannelwatch/`.

Install it with:

```bash
./install.sh
```

Or install to a custom skills directory:

```bash
./install.sh --dir /path/to/skills
```

Installed location (default): `~/.config/crush/skills/ytchannelwatch/`

## Notes

- Channel config is stored at `~/.config/yt-channel-watch/channels.json` by default.
- `list` ignores Shorts and prints title, URL, and duration.
- `list --tag-regex` filters channels to those with matching tags.
