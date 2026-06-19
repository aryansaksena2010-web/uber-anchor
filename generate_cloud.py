#!/usr/bin/env python3
"""
Cloud generator — runs on a GitHub Actions Linux runner (no Mac needed).

Each daily run:
  1. Generates today's lesson (topic rotates by weekday).
  2. Writes it to   public/today.m4a   (what the phone plays).
  3. Rotates it into a 15-item "skip pool"  public/pool/1.m4a .. 15.m4a
     (newest = 1). The phone's Skip button plays a random one of these.

The audio is committed back to the repo by the workflow, and the phone fetches
it over plain HTTPS from raw.githubusercontent.com — so no Mac, no iCloud, and
no API keys are involved.
"""
import os
import shutil

import common
import generate_lesson as gl

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")
POOL = os.path.join(PUBLIC, "pool")
POOL_SIZE = 15


def rotate_pool(new_m4a):
    """Shift 1->2 ... 14->15 (drop old 15), then put the new story at slot 1."""
    os.makedirs(POOL, exist_ok=True)
    oldest = os.path.join(POOL, f"{POOL_SIZE}.m4a")
    if os.path.exists(oldest):
        os.remove(oldest)
    for n in range(POOL_SIZE, 1, -1):
        src = os.path.join(POOL, f"{n - 1}.m4a")
        dst = os.path.join(POOL, f"{n}.m4a")
        if os.path.exists(src):
            shutil.move(src, dst)
    shutil.copyfile(new_m4a, os.path.join(POOL, "1.m4a"))


def main():
    cfg = common.load_config()
    common.ensure_dirs()
    os.makedirs(PUBLIC, exist_ok=True)

    # Allow the workflow to pick a lighter/faster model on the CPU runner.
    model = os.environ.get("OLLAMA_MODEL")
    if model:
        cfg["ollama"]["model"] = model

    import datetime as dt
    today = dt.date.today()
    topic = cfg["topics"][today.weekday()]
    print(f"[cloud] {today.isoformat()} -> {topic['name']}")

    # Reuse the exact same pipeline as the Mac version.
    recent = gl.fetch_recent_items(topic.get("feeds", []))
    prompt = gl.build_prompt(cfg, topic, recent)
    script = gl.call_ollama(cfg, prompt)

    wav = os.path.join(common.LESSONS_DIR, f"{today.isoformat()}.wav")
    gl.synth_with_kokoro(cfg, script, wav)

    # Convert to a phone-friendly m4a (ffmpeg on the Linux runner).
    today_m4a = os.path.join(PUBLIC, "today.m4a")
    common.convert_to_m4a(wav, today_m4a, cfg.get("publish", {}).get("aac_bitrate", 64000))
    print(f"[cloud] wrote {today_m4a}")

    rotate_pool(today_m4a)
    print(f"[cloud] rotated skip pool (newest -> pool/1.m4a)")

    # Tidy local wav so it isn't committed.
    try:
        os.remove(wav)
    except OSError:
        pass


if __name__ == "__main__":
    main()
