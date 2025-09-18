import sys
import os
import json
from PySide6.QtWidgets import QApplication

from app import WallpaperApp


CONFIG_PATH = os.path.expanduser("./config.json")


def main():
    app = QApplication(sys.argv)

    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "wallpaper_dir": os.path.expanduser("~/Pictures"),
            "wallpaper_command": "feh --bg-scale {path}",
            "thumbnail_size": 180,
            "_command_examples": {
                "feh": "feh --bg-scale {path}",
                "swww": "swww img {path}",
                "hyprpaper": "hyprctl hyprpaper wallpaper ,{path}",
                "swaybg": "swaybg -i {path} -m fill",
                "nitrogen": "nitrogen --set-zoom-fill {path}",
                "gsettings": "gsettings set org.gnome.desktop.background picture-uri file://{path}",
                "custom_with_different_placeholder": "your_command <selected image path>",
            },
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {CONFIG_PATH}")
            print("Edit the config file to set your wallpaper directory and command")
        except Exception as e:
            print(f"Could not create config file: {e}")

    window = WallpaperApp(CONFIG_PATH)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
