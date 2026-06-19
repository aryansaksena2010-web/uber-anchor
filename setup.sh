#!/usr/bin/env bash
# ===========================================================================
#  Uber Anchor — one-time setup (macOS / Linux)
#  Run:  bash setup.sh
# ===========================================================================
set -e
cd "$(dirname "$0")"

echo "==> 1/5  Finding a compatible Python (Kokoro needs 3.10-3.12)"
PYBIN=""
for cand in python3.12 python3.11 python3.10; do
  if command -v "$cand" >/dev/null 2>&1; then PYBIN="$cand"; break; fi
done

if [ -z "$PYBIN" ]; then
  echo "    No Python 3.10-3.12 found. Installing python@3.12 via Homebrew..."
  if command -v brew >/dev/null 2>&1; then
    brew install python@3.12
    PYBIN="$(brew --prefix)/bin/python3.12"
  else
    echo "    (!) Homebrew not found. Install it from https://brew.sh then re-run."
    echo "    (Your default python3 is too new for the voice engine.)"
    exit 1
  fi
fi
echo "    Using: $PYBIN ($($PYBIN --version))"

echo "    Creating a fresh virtual environment (.venv)"
rm -rf .venv
"$PYBIN" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

echo "==> 2/5  Installing Python packages"
pip install -r requirements.txt

echo "==> 3/5  Checking system audio tools (espeak-ng for the voice)"
if command -v brew >/dev/null 2>&1; then
  brew list espeak-ng >/dev/null 2>&1 || brew install espeak-ng
elif command -v apt >/dev/null 2>&1; then
  dpkg -s espeak-ng >/dev/null 2>&1 || sudo apt-get install -y espeak-ng
else
  echo "    (!) Please install 'espeak-ng' manually for your system."
fi

echo "==> 4/5  Downloading the offline wake-word model (Vosk, ~40MB)"
mkdir -p models
if [ ! -d "models/vosk-model-small-en-us-0.15" ]; then
  curl -L -o models/vosk.zip \
    https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -q models/vosk.zip -d models
  rm models/vosk.zip
fi

echo "==> 5/5  Checking Ollama"
if command -v ollama >/dev/null 2>&1; then
  ollama pull llama3.2 || true
else
  echo "    (!) Ollama is not installed. Get it free at https://ollama.com/download"
  echo "        Then run:  ollama pull llama3.2"
fi

echo ""
echo "============================================================"
echo "  Setup done. Next:"
echo "    1) Test a lesson now:   .venv/bin/python generate_lesson.py"
echo "    2) Start listening:     .venv/bin/python wake_listener.py"
echo "    3) Automate it:         see README (midnight + auto-start)"
echo "============================================================"
