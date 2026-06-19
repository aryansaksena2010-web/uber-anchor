# 🎙️ Uber Anchor

A free "personal news anchor" for your uncle's Uber rides.

Every night a **Mac** writes a fresh ~20-minute lesson on one of his favorite
topics, narrates it in a **CNN-anchor style** voice, and pushes it to his
**iPhone** via iCloud. In the car he just says **"Hey Siri, read to me"** and
it plays. **No buttons, no app to open, no always-on microphone.** Everything
runs on your own Mac and costs **$0**.

## How it works (the real / iPhone version)

```
   Mac (at home)                  iCloud Drive                 iPhone
 ┌────────────────┐   midnight   ┌──────────────┐   auto-sync  ┌──────────────┐
 │ AI writes the  │ ───────────► │ UberAnchor/  │ ───────────► │ "Hey Siri,   │
 │ lesson + voice │              │   today.m4a  │              │  read to me" │
 └────────────────┘              └──────────────┘              └──────────────┘
```

The iPhone **can't** run the AI or the voice engine — those need a Mac. So the
Mac does all the heavy lifting overnight, and the phone only plays a file.
Siri is the wake word, which is why there's no background app or mic drain.

**Two setups, done once each:**
1. **Mac** — install + schedule the nightly generation (below).
2. **iPhone** — build the Siri Shortcut (see **`IPHONE_SETUP.md`**).

Do the Mac side on *your* Mac first to test, then repeat the identical steps on
your uncle's Mac + iPhone (you both have the same setup).

---

## What it teaches (one topic per day)

| Day | Topic |
|-----|-------|
| Monday | Quantum physics |
| Tuesday | Cricket |
| Wednesday | Booker Prize books |
| Thursday | Interesting dishes to cook at home |
| Friday | New health technology |
| Saturday | Bollywood |
| Sunday | Strength & cardio workouts for 60-year-olds |

Each lesson pulls a few **recent headlines** from free news feeds so it stays
current, then the local AI turns them into a clear, vivid spoken segment.

---

## The pieces (all free & open source)

- **Ollama** — runs a free local AI model (`llama3.2`) that writes the script.
- **Kokoro TTS** — the voice. **#1 on the TTS Arena leaderboard**, close to
  ElevenLabs quality, not robotic. Runs on a laptop CPU. Default voice
  `am_michael` (warm anchor); `am_onyx` is deeper/"primetime."
- **iCloud Drive** — free, automatic file sync from Mac to iPhone.
- **Apple Shortcuts + Siri** — the hands-free wake word on the phone.
- **RSS feeds** — free, for fresh daily material.

---

## Mac setup (do this once, ~10 minutes)

**1. Install Ollama** (the free local AI): download from
<https://ollama.com/download>, install, and leave it running.

**2. Run the setup script.** Open Terminal, go into this folder, run:

```bash
cd ~/Desktop/uber-anchor
bash setup.sh
```

It builds a Python environment (with a compatible Python 3.12), installs the
voice engine, and pulls the AI model.

**3. Generate today's lesson and check it:**

```bash
.venv/bin/python generate_lesson.py
afplay lessons/today.wav
```

You should hear the anchor voice. It also drops `today.m4a` into
**iCloud Drive → UberAnchor** for the phone.

**4. Schedule it nightly:**

```bash
bash install_autostart_mac.sh
```

This generates a fresh lesson **every night at midnight and at login** (so a
laptop that slept through midnight still catches up). That's the whole Mac side.

---

## iPhone setup

See **`IPHONE_SETUP.md`** — a 2-minute Siri Shortcut named "Read to me" that
plays the synced file. After that he just says *"Hey Siri, read to me."*

---

## Tweaking it

Everything is in **`config.yaml`** — no coding needed:
- **voice** (`am_michael`, `am_onyx`, `am_adam`, `bm_george`),
- **lesson length**,
- the **AI model** (e.g. `qwen2.5:7b` for richer writing),
- **news feeds** per topic,
- **publish** settings (iCloud folder name, audio quality).

---

## Low-memory Macs (8GB MacBook Air)

The AI model (~2GB) and the voice engine are both memory-heavy. To avoid
crashes, the generator now tells Ollama to release its memory the instant it
finishes writing, before the voice step starts. If you ever hit a crash mid-run,
the text transcript is already saved — re-create just the audio with the
lightweight, no-AI script:

```bash
.venv/bin/python narrate.py
```

---

## Files in this project

- `generate_lesson.py` — the nightly job: news → AI script → voice → iCloud.
- `narrate.py` — re-make audio from an existing transcript (low memory).
- `config.yaml` — all settings.
- `install_autostart_mac.sh` — schedules the nightly job.
- `IPHONE_SETUP.md` — the Siri Shortcut guide.
- `common.py` — shared helpers (audio + iCloud publishing).
- `wake_listener.py` — *optional* computer-only wake word (NOT used in the
  iPhone setup; Siri replaces it). Keep it only if you also want a Mac to listen.

---

## Troubleshooting

- **"Ollama connection refused"** → make sure the Ollama app is running.
- **No sound on the Mac** → macOS has `afplay` built in; it should just work.
- **Voice errors about espeak** → `brew install espeak-ng`.
- **iPhone can't find the file** → the Mac hasn't generated today yet, or iCloud
  is still syncing. Check the Files app → iCloud Drive → UberAnchor.
- **Computer crashed during generation** → see "Low-memory Macs" above.
