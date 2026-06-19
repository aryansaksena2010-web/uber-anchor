#!/usr/bin/env python3
"""
Narrate an already-written transcript into today.wav — WITHOUT running Ollama.
Lightweight: use this on low-RAM machines, or to re-make audio after a crash.

Usage:
  python narrate.py                 # narrate today's transcript
  python narrate.py 2026-06-19      # narrate a specific date
"""
import datetime as dt
import os
import shutil
import sys

import common


def main():
    cfg = common.load_config()
    common.ensure_dirs()

    stamp = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    transcript_path = os.path.join(common.LESSONS_DIR, f"{stamp}.txt")
    if not os.path.exists(transcript_path):
        print(f"No transcript at {transcript_path}. Run generate_lesson.py first.",
              file=sys.stderr)
        sys.exit(1)

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Drop the "# Title — date" header line if present.
    lines = text.splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    text = "\n".join(lines).strip()
    print(f"[narrate] {len(text)} characters from {os.path.basename(transcript_path)}")

    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    voice = cfg["tts"].get("voice", "am_michael")
    lang_code = cfg["tts"].get("lang_code", "a")
    speed = float(cfg["tts"].get("speed", 1.0))
    sr = int(cfg["tts"].get("sample_rate", 24000))

    out_wav = os.path.join(common.LESSONS_DIR, f"{stamp}.wav")
    print(f"[kokoro] voice '{voice}' -> {out_wav}")
    pipeline = KPipeline(lang_code=lang_code)
    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed):
        chunks.append(audio)
    full = np.concatenate(chunks)
    sf.write(out_wav, full, sr)

    shutil.copyfile(out_wav, common.TODAY_AUDIO)
    print(f"[done] Audio ready: {common.TODAY_AUDIO}")

    # Push a phone-friendly copy to iCloud for the iPhone Shortcut.
    common.publish_to_iphone(cfg, out_wav)


if __name__ == "__main__":
    main()
