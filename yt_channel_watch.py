#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple


CONFIG_PATH = Path.home() / ".config" / "yt-channel-watch" / "channels.json"
YOUTUBE_HANDLE_RE = re.compile(r"^@[A-Za-z0-9._-]+$")
YOUTUBE_CHANNEL_ID_RE = re.compile(r"^UC[0-9A-Za-z_-]{20,}$")


@dataclass
class Channel:
    channel_id: str
    name: str
    source: str


@dataclass
class Video:
    channel_name: str
    title: str
    url: str
    duration: str
    published: datetime


def ensure_config_file(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text("[]\n", encoding="utf-8")


def load_channels(config_path: Path) -> List[Channel]:
    ensure_config_file(config_path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    channels: List[Channel] = []
    for entry in data:
        channels.append(
            Channel(
                channel_id=entry["channel_id"],
                name=entry["name"],
                source=entry.get("source", entry["channel_id"]),
            )
        )
    return channels


def save_channels(config_path: Path, channels: List[Channel]) -> None:
    payload = [asdict(channel) for channel in channels]
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_channel_input(value: str) -> str:
    text = value.strip()
    if text.endswith("/"):
        text = text[:-1]
    return text


def extract_channel_id_from_url(url: str) -> str | None:
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return None
    if parsed.netloc not in {"youtube.com", "www.youtube.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "channel" and YOUTUBE_CHANNEL_ID_RE.match(parts[1]):
        return parts[1]
    return None


def resolve_channel(channel_input: str, explicit_channel_id: str | None) -> Tuple[str, str, str]:
    source = normalize_channel_input(channel_input)

    if explicit_channel_id:
        channel_id = explicit_channel_id.strip()
        if not YOUTUBE_CHANNEL_ID_RE.match(channel_id):
            raise ValueError("Provided --channel-id does not look like a valid YouTube channel id.")
        return channel_id, source, source

    if YOUTUBE_CHANNEL_ID_RE.match(source):
        return source, source, source

    from_url = extract_channel_id_from_url(source)
    if from_url:
        return from_url, source, source

    if YOUTUBE_HANDLE_RE.match(source):
        source_url = f"https://www.youtube.com/{source}"
    elif source.startswith("http://") or source.startswith("https://"):
        source_url = source
    else:
        source_url = source

    if shutil.which("yt-dlp") is None:
        raise RuntimeError(
            "yt-dlp is required to resolve handles/URLs. Install it first (e.g. `brew install yt-dlp`)."
        )

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--playlist-items",
        "1",
        "--print",
        "channel_id",
        "--print",
        "uploader",
        source_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        raise RuntimeError(f"Failed to resolve channel: {stderr}")

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError("Could not resolve channel id/name from yt-dlp output.")

    channel_id, channel_name = lines[0], lines[1]
    if not YOUTUBE_CHANNEL_ID_RE.match(channel_id):
        raise RuntimeError(f"Resolved channel id looks invalid: {channel_id}")

    return channel_id, channel_name, source


def parse_published(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def fetch_video_duration(video_url: str) -> str:
    if shutil.which("yt-dlp") is None:
        return "unknown"

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--print",
        "duration_string",
        video_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return "unknown"

    for line in result.stdout.splitlines():
        value = line.strip()
        if value:
            return value

    return "unknown"


def fetch_most_recent_full_length_video(channel: Channel, cutoff: datetime) -> Video | None:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel.channel_id}"
    with urllib.request.urlopen(url, timeout=20) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }

    for entry in root.findall("atom:entry", ns):
        published_text = entry.findtext("atom:published", default="", namespaces=ns)
        if not published_text:
            continue
        published = parse_published(published_text)
        if published < cutoff:
            continue

        title = entry.findtext("atom:title", default="", namespaces=ns).strip()
        link_node = entry.find("atom:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        if not link or "/shorts/" in link:
            continue

        duration = fetch_video_duration(link)
        return Video(
            channel_name=channel.name,
            title=title,
            url=link,
            duration=duration,
            published=published,
        )

    return None


def command_add(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    channels = load_channels(config_path)

    channel_id, channel_name, source = resolve_channel(args.channel, args.channel_id)
    for channel in channels:
        if channel.channel_id == channel_id:
            print(f"Channel already added: {channel.name} ({channel.channel_id})")
            return 0

    display_name = args.name.strip() if args.name else channel_name
    channels.append(Channel(channel_id=channel_id, name=display_name, source=source))
    save_channels(config_path, channels)
    print(f"Added: {display_name} ({channel_id})")
    return 0


def command_remove(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    channels = load_channels(config_path)
    target = normalize_channel_input(args.channel)

    before = len(channels)
    channels = [
        channel
        for channel in channels
        if channel.channel_id != target
        and normalize_channel_input(channel.source) != target
        and normalize_channel_input(channel.name) != target
    ]

    if len(channels) == before:
        print("No matching channel found.")
        return 1

    save_channels(config_path, channels)
    print("Removed.")
    return 0


def command_channels(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    channels = load_channels(config_path)
    if not channels:
        print("No channels configured.")
        return 0

    for channel in channels:
        print(f"- {channel.name} ({channel.channel_id}) [{channel.source}]")
    return 0


def command_list(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    channels = load_channels(config_path)
    if not channels:
        print("No channels configured. Add one with `add`.")
        return 1

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)
    all_videos: List[Video] = []
    failures: List[str] = []

    for channel in channels:
        try:
            video = fetch_most_recent_full_length_video(channel, cutoff)
            if video is not None:
                all_videos.append(video)
        except Exception as exc:
            failures.append(f"{channel.name} ({channel.channel_id}): {exc}")

    all_videos.sort(key=lambda video: video.published, reverse=True)

    if all_videos:
        for video in all_videos:
            timestamp = video.published.astimezone().strftime("%Y-%m-%d %H:%M")
            print(f"[{timestamp}] {video.channel_name} [{video.duration}] - {video.title}")
            print(video.url)
    else:
        print(f"No full-length videos in the last {args.hours} hours.")

    if failures:
        print("\nErrors:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Track a fixed list of YouTube channels and report new videos."
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to channels json file (default: %(default)s)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a channel")
    add_parser.add_argument("channel", help="YouTube channel URL, @handle, or channel id")
    add_parser.add_argument("--name", help="Optional display name override")
    add_parser.add_argument("--channel-id", help="Optional explicit channel id (UC...) to skip lookup")
    add_parser.set_defaults(func=command_add)

    remove_parser = subparsers.add_parser("remove", help="Remove a channel")
    remove_parser.add_argument("channel", help="Channel id, source URL/handle, or exact display name")
    remove_parser.set_defaults(func=command_remove)

    channels_parser = subparsers.add_parser("channels", help="Show configured channels")
    channels_parser.set_defaults(func=command_channels)

    list_parser = subparsers.add_parser("list", help="List recent videos")
    list_parser.add_argument("--hours", type=float, default=24.0, help="How many hours back to check")
    list_parser.set_defaults(func=command_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
