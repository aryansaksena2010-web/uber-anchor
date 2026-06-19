#!/usr/bin/env bash
# ===========================================================================
#  Uber Anchor — schedule the nightly lesson on macOS.
#
#  This installs ONE background job (Apple's launchd) that generates a fresh
#  lesson and pushes it to iCloud:
#    - every night at 00:00, AND
#    - once at login (so a laptop that was asleep at midnight still catches up).
#
#  There is NO always-on microphone here. On the iPhone, Siri is the wake
#  word (see IPHONE_SETUP.md). Run this once:
#       bash install_autostart_mac.sh
# ===========================================================================
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$DIR/.venv/bin/python"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS" "$DIR/logs"

GEN_PLIST="$AGENTS/com.uberanchor.generate.plist"

cat > "$GEN_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.uberanchor.generate</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$DIR/generate_lesson.py</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <!-- Top up the buffer at login and every 6 hours while the Mac is awake. -->
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>21600</integer>
  <key>StandardOutPath</key><string>$DIR/logs/generate.log</string>
  <key>StandardErrorPath</key><string>$DIR/logs/generate.err</string>
</dict></plist>
EOF

# (Re)load the job.
launchctl unload "$GEN_PLIST" 2>/dev/null || true
# Remove the old always-on listener job if a previous version installed it.
OLD_LISTEN="$AGENTS/com.uberanchor.listen.plist"
if [ -f "$OLD_LISTEN" ]; then
  launchctl unload "$OLD_LISTEN" 2>/dev/null || true
  rm -f "$OLD_LISTEN"
  echo "Removed the old always-on listener (Siri replaces it)."
fi
launchctl load "$GEN_PLIST"

echo "Installed: keeps the lesson buffer topped up at login + every 6 hours."
echo "($GEN_PLIST)"
echo ""
echo "Filling the buffer now (make sure the Ollama app is running)."
echo "The FIRST run makes ~15 lessons and can take 20-40 min. Later runs make"
echo "only the 1 new day needed. You can keep using your Mac while it works."
"$PY" "$DIR/generate_lesson.py" || true
echo ""
echo "Done. The Mac side is now automatic."
echo "Next: set up the iPhone Shortcut once — see IPHONE_SETUP.md."
echo "To stop later:  launchctl unload $GEN_PLIST"
