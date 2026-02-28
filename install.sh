#!/usr/bin/env bash
set -e

DEFAULT_INSTALL_DIR="$HOME/.config/crush/skills"
SKILL_NAME="ytchannelwatch"

INSTALL_DIR="${DEFAULT_INSTALL_DIR}"
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    cat << EOF
Usage: ./install.sh [OPTIONS]

Install the ytchannelwatch Crush skill.

Options:
  -d, --dir DIR    Installation directory (default: ~/.config/crush/skills)
  -h, --help       Show this help message

Examples:
  ./install.sh                            # Install to default location
  ./install.sh -d ~/.config/crush/skills # Install globally
  ./install.sh -d ./my-agent/skills      # Install to specific agent

The skill will be installed at: <DIR>/ytchannelwatch/
EOF
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/${SKILL_NAME}"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: ${SOURCE_DIR}"
    echo "This script should be run from the root of the yt-subs repository."
    exit 1
fi

TARGET_DIR="${INSTALL_DIR}/${SKILL_NAME}"
mkdir -p "$INSTALL_DIR"

if [ -d "$TARGET_DIR" ]; then
    echo "Warning: ${TARGET_DIR} already exists."
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    rm -rf "$TARGET_DIR"
fi

echo "Installing ytchannelwatch skill..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

chmod +x "${TARGET_DIR}/scripts"/*.py 2>/dev/null || true

echo "✓ Successfully installed to: ${TARGET_DIR}"
echo ""
echo "Next steps:"
echo "  1. Ensure you have Python 3 and yt-dlp installed"
echo "  2. Ask your agent: 'Use ytchannelwatch to track my channels'"
echo ""
echo "For more information, see README.md"
