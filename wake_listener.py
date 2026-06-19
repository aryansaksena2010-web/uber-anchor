#!/usr/bin/env python3
"""
Always-on, hands-free listener.

Sits quietly in the background listening to the microphone (fully offline,
using Vosk). When it hears one of the wake phrases from config.yaml
(e.g. "read to me" or "I'm in my Uber"), it plays today's lesson.

No buttons. Ever.

Run:  python wake_listener.py
Stop: Ctrl+C
"""
import json
import os
import queue
import sys
import time

import common

try:
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
except ImportError as e:  # noqa: BLE001
    print(
        "Missing dependencies. Run:\n"
        "  pip install vosk sounddevice\n"
        f"(import error: {e})",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    cfg = common.load_config()
    common.ensure_dirs()

    model_path = common.abspath(cfg["speech"]["vosk_model"])
    if not os.path.isdir(model_path):
        print(
            f"Vosk model not found at {model_path}.\n"
            "Download the small English model and unzip it there. See README.",
            file=sys.stderr,
        )
        sys.exit(1)

    phrases = [p.lower() for p in cfg["speech"]["wake_phrases"]]
    print(f"[listen] Wake phrases: {phrases}")

    model = Model(model_path)
    samplerate = 16000
    rec = KaldiRecognizer(model, samplerate)
    rec.SetWords(False)

    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):  # noqa: ARG001
        if status:
            print(f"[mic] {status}", file=sys.stderr)
        audio_q.put(bytes(indata))

    last_trigger = 0.0
    cooldown_seconds = 5  # ignore repeats right after a trigger

    def heard(text):
        text = text.lower().strip()
        return text and any(p in text for p in phrases)

    print("[listen] Listening... say a wake phrase. (Ctrl+C to stop)")
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        while True:
            data = audio_q.get()
            triggered = False
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result()).get("text", "")
                triggered = heard(result)
            else:
                partial = json.loads(rec.PartialResult()).get("partial", "")
                triggered = heard(partial)

            if triggered and (time.time() - last_trigger) > cooldown_seconds:
                last_trigger = time.time()
                print("[listen] Wake phrase heard -> playing today's lesson.")
                if not os.path.exists(common.TODAY_AUDIO):
                    print("[listen] No lesson generated yet for today.",
                          file=sys.stderr)
                else:
                    common.play_audio(common.TODAY_AUDIO)
                # Reset recognizer so leftover words don't re-trigger.
                rec = KaldiRecognizer(model, samplerate)
                print("[listen] Listening again...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[listen] Stopped.")
