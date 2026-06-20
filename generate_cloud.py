#!/usr/bin/env python3
"""
Cloud generator — runs on a GitHub Actions Linux runner (no Mac needed).

Normal daily run:
  1. Generates today's lesson (topic rotates by weekday).
  2. Writes it to   public/today.m4a   (what the phone plays).
  3. Rotates it into a 15-item "skip pool"  public/pool/1.m4a .. 15.m4a
     (newest = 1). The phone's Skip button plays a random one of these.

Seed run (env SEED_ALL=1): generates ONE story for every topic so the skip
pool immediately has variety across all interests (instead of copies of one
story while the daily pool is still building up).

The audio is committed back to the repo by the workflow, and the phone fetches
it over plain HTTPS from raw.githubusercontent.com — so no Mac, no iCloud, and
no API keys are involved.
"""
import datetime as dt
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
    newest = os.path.join(POOL, "1.m4a")
    shutil.copyfile(new_m4a, newest)
    # Fill any still-empty slots so the phone's random Skip (1..15) never hits
    # a missing file while the pool is still building.
    for n in range(2, POOL_SIZE + 1):
        slot = os.path.join(POOL, f"{n}.m4a")
        if not os.path.exists(slot):
            shutil.copyfile(newest, slot)


def make_story(cfg, topic_index):
    """Generate one story for a topic index and return its .m4a path."""
    topic = cfg["topics"][topic_index]
    print(f"[gen] topic {topic_index}: {topic['name']}")
    recent = gl.fetch_recent_items(topic.get("feeds", []))
    prompt = gl.build_prompt(cfg, topic, recent)
    script = gl.call_ollama(cfg, prompt)
    wav = os.path.join(common.LESSONS_DIR, f"gen_{topic_index}.wav")
    gl.synth_with_kokoro(cfg, script, wav)
    m4a = os.path.join(common.LESSONS_DIR, f"gen_{topic_index}.m4a")
    common.convert_to_m4a(wav, m4a, cfg.get("publish", {}).get("aac_bitrate", 64000))
    try:
        os.remove(wav)
    except OSError:
        pass
    return m4a


def seed_all(cfg):
    """Generate one story per topic so Skip has real variety immediately."""
    today_idx = dt.date.today().weekday()
    today_path = os.path.join(PUBLIC, "today.m4a")
    for idx in range(len(cfg["topics"])):
        m4a = make_story(cfg, idx)
        rotate_pool(m4a)
        if idx == today_idx:
            shutil.copyfile(m4a, today_path)
        try:
            os.remove(m4a)
        except OSError:
            pass
    print("[seed] done — pool seeded with all topics.")


def main():
    cfg = common.load_config()
    common.ensure_dirs()
    os.makedirs(PUBLIC, exist_ok=True)

    # Allow the workflow to pick a lighter/faster model on the CPU runner.
    model = os.environ.get("OLLAMA_MODEL")
    if model:
        cfg["ollama"]["model"] = model

    if os.environ.get("SEED_ALL") == "1":
        seed_all(cfg)
        return

    today = dt.date.today()
    today_m4a = make_story_for_today(cfg, today)
    rotate_pool(today_m4a)
    print("[cloud] rotated skip pool (newest -> pool/1.m4a)")


def make_story_for_today(cfg, today):
    """Normal daily path: make today's story, write public/today.m4a."""
    m4a_src = make_story(cfg, today.weekday())
    today_m4a = os.path.join(PUBLIC, "today.m4a")
    shutil.copyfile(m4a_src, today_m4a)
    try:
        os.remove(m4a_src)
    except OSError:
        pass
    print(f"[cloud] wrote {today_m4a}")
    return today_m4a


if __name__ == "__main__":
    main()
