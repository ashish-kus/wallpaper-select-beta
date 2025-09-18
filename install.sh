#!/bin/bash

set -e # exit on error

APP_NAME="huegen-gui"
ENTRY_POINT="src/huegen-gui.py"
CONFIG_FILE="src/config.json"

echo "🔧 Building $APP_NAME with PyInstaller..."

pyinstaller --onefile --noconsole \
  --add-data "$CONFIG_FILE:." \
  "$ENTRY_POINT"

echo "✅ Build complete."

# Copy binary to /usr/local/bin (system-wide) or ~/.local/bin (user-only)
if [ -w /usr/local/bin ]; then
  echo "📦 Installing system-wide..."
  sudo cp "dist/$APP_NAME" /usr/local/bin/
else
  echo "📦 Installing to ~/.local/bin..."
  mkdir -p ~/.local/bin
  cp "dist/$APP_NAME" ~/.local/bin/
  echo "👉 Make sure ~/.local/bin is in your PATH"
fi

echo "🚀 Installed successfully! You can run it with: $APP_NAME"
