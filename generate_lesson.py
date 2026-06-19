#!/usr/bin/env python3
"""
Generate today's ~20-minute lesson.

Pipeline:
  1. Pick today's topic (one per weekday).
  2. Pull a few recent headlines from that topic's RSS feeds (for freshness).
  3. Ask the local Ollama model to write it as a CNN-style anchor segment.
  4. Narrate it to a WAV file with Piper TTS.

Run manually:   python generate_lesson.py
Force a topic:  python generate_lesson.py --weekday 1     (0=Mon ... 6=Sun)
"""
import argparse
import datetime as dt
import os
import shutil
import sys
import textwrap
import time

import requests

import common

try:
    import feedparser
except ImportError:
    feedparser = None


def fetch_recent_items(feeds, max_items=5):
    """Return a list of 'Headline — summary' strings from the topic's feeds."""
    if not feeds or feedparser is None:
        return []
    items = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:max_items]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                # Strip crude HTML tags from summaries.
                import re
                summary = re.sub(r"<[^>]+>", "", summary)
                summary = summary[:400]
                if title:
                    items.append(f"- {title}: {summary}".strip(": ").strip())
        except Exception as e:  # noqa: BLE001
            print(f"[feed] could not read {url}: {e}", file=sys.stderr)
    return items[:max_items]


def build_prompt(cfg, topic, recent_items):
    target_words = cfg["lesson"]["target_minutes"] * cfg["lesson"]["words_per_minute"]
    persona = cfg["persona"].strip()

    if recent_items:
        news_block = (
            "Here are some RECENT headlines on this topic. Use them as the "
            "anchor for today's segment, but explain everything in your own "
            "words and add useful background:\n\n" + "\n".join(recent_items)
        )
    else:
        news_block = (
            "There are no fresh headlines today, so pick ONE genuinely "
            "fascinating, lesser-known thing in this area and teach it in depth."
        )

    prompt = f"""{persona}

Today's beat is: {topic['name']}.
Focus: {topic['brief']}.

{news_block}

Write a spoken radio/TV segment of about {target_words} words (around
{cfg['lesson']['target_minutes']} minutes when read aloud at a brisk anchor
pace). Requirements:
- Open with a punchy on-air cold open ("Happening now...", "Good morning, and
  welcome...").
- Teach ONE main thing well, with vivid, concrete detail and a couple of
  "here's why that matters" moments.
- Speak directly to a single curious 60-year-old listener relaxing in a car.
- Use short, clear sentences that are easy to listen to. No headers, no bullet
  points, no stage directions, no markdown — just the words to be spoken.
- End with a warm sign-off that teases that there's more tomorrow.

Begin the segment now."""
    return prompt


def call_ollama(cfg, prompt):
    url = cfg["ollama"]["url"].rstrip("/") + "/api/generate"
    payload = {
        "model": cfg["ollama"]["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.8},
        # Unload the model from memory immediately after generating, so the
        # ~2GB it uses is freed BEFORE the voice engine loads. Critical on
        # low-RAM machines (e.g. 8GB MacBook Air) to avoid crashes.
        "keep_alive": 0,
    }
    print(f"[ollama] generating with {cfg['ollama']['model']} ...")
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    text = r.json()["response"].strip()
    # Give macOS a moment to reclaim the freed memory before TTS starts.
    time.sleep(3)
    return text


def synth_with_kokoro(cfg, text, out_wav):
    """Narrate text to a WAV using Kokoro (best free local TTS)."""
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as e:
        raise RuntimeError(
            "Kokoro TTS is not installed. Run:\n"
            "  pip install kokoro soundfile\n"
            "and install espeak-ng (macOS: 'brew install espeak-ng', "
            "Ubuntu: 'sudo apt install espeak-ng'). See the README.\n"
            f"(import error: {e})"
        )

    voice = cfg["tts"].get("voice", "am_michael")
    lang_code = cfg["tts"].get("lang_code", "a")
    speed = float(cfg["tts"].get("speed", 1.0))
    sr = int(cfg["tts"].get("sample_rate", 24000))

    print(f"[kokoro] narrating with voice '{voice}' -> {out_wav}")
    pipeline = KPipeline(lang_code=lang_code)
    chunks = []
    # Kokoro auto-splits long text into natural sentence chunks.
    for _, _, audio in pipeline(text, voice=voice, speed=speed):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("Kokoro produced no audio.")
    full = np.concatenate(chunks)
    sf.write(out_wav, full, sr)


def produce_lesson(cfg, date):
    """Generate one full lesson for a given date and publish a dated m4a.

    Returns the local WAV path.
    """
    topic = cfg["topics"][date.weekday()]
    stamp = date.isoformat()
    print(f"[make] {stamp} ({date.strftime('%a')}) -> {topic['name']}")

    recent = fetch_recent_items(topic.get("feeds", []))
    prompt = build_prompt(cfg, topic, recent)
    script = call_ollama(cfg, prompt)

    transcript_path = os.path.join(common.LESSONS_DIR, f"{stamp}.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(f"# {topic['name']} — {stamp}\n\n{script}\n")

    dated_wav = os.path.join(common.LESSONS_DIR, f"{stamp}.wav")
    synth_with_kokoro(cfg, script, dated_wav)

    # Publish a date-named copy for the rolling buffer.
    common.publish_dated(cfg, dated_wav, date)
    return dated_wav


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=str, default=None,
                    help="Make just one lesson for YYYY-MM-DD (default: top up buffer).")
    ap.add_argument("--buffer", type=int, default=None,
                    help="Override how many days to keep ready.")
    args = ap.parse_args()

    cfg = common.load_config()
    common.ensure_dirs()
    today = dt.date.today()

    # Single-date mode (handy for testing).
    if args.date:
        d = dt.date.fromisoformat(args.date)
        wav = produce_lesson(cfg, d)
        if d == today:
            shutil.copyfile(wav, common.TODAY_AUDIO)
            common.publish_to_iphone(cfg, wav)
        return

    # Buffer mode (default): make sure the next N days are all ready.
    buffer_days = args.buffer or cfg.get("publish", {}).get("buffer_days", 15)
    print(f"[buffer] target: {buffer_days} days ready (from {today.isoformat()})")

    made = 0
    skipped = 0
    today_wav = None
    for i in range(buffer_days):
        d = today + dt.timedelta(days=i)
        if common.dated_exists(cfg, d):
            skipped += 1
            continue
        wav = produce_lesson(cfg, d)
        if d == today:
            today_wav = wav
        made += 1

    # Keep today.m4a / today.wav pointing at today's lesson (fallback shortcut).
    if today_wav is None:
        # today already existed in the buffer; rebuild local today.wav from its transcript if present
        t_txt = os.path.join(common.LESSONS_DIR, f"{today.isoformat()}.wav")
        today_wav = t_txt if os.path.exists(t_txt) else None
    if today_wav and os.path.exists(today_wav):
        shutil.copyfile(today_wav, common.TODAY_AUDIO)
        common.publish_to_iphone(cfg, today_wav)

    common.cleanup_old(cfg, today)
    print(f"[buffer] done. made {made} new, {skipped} already ready.")


if __name__ == "__main__":
    main()
