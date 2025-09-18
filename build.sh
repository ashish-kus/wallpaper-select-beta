#!/bin/bash
pyinstaller --onefile --noconsole \
  --add-data "src/config.json:." \
  src/huegen-gui.py
