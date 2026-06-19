"""Shared helpers: config loading, paths, and audio playback."""
import os
import sys
import shutil
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LESSONS_DIR = os.path.join(HERE, "lessons")
TODAY_AUDIO = os.path.join(LESSONS_DIR, "today.wav")


def load_config():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def abspath(path):
    """Resolve a path from config relative to this folder."""
    if os.path.isabs(path):
        return path
    return os.path.join(HERE, path)


def ensure_dirs():
    os.makedirs(LESSONS_DIR, exist_ok=True)


def icloud_dir(cfg):
    """The iCloud Drive folder the iPhone will read from."""
    folder = cfg.get("publish", {}).get("icloud_folder", "UberAnchor")
    base = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs")
    return os.path.join(base, folder)


def publish_to_iphone(cfg, wav_path):
    """Convert the WAV to a phone-friendly .m4a and drop it in iCloud Drive.

    Returns the published file path, or None if publishing is disabled.
    """
    pub = cfg.get("publish", {})
    if not pub.get("enabled", False):
        return None

    target_dir = icloud_dir(cfg)
    base = os.path.dirname(target_dir)
    if not os.path.isdir(base):
        print(
            "[publish] iCloud Drive folder not found on this Mac. Sign in to "
            "iCloud and enable iCloud Drive, then re-run. (Looked for: "
            f"{base})",
            file=sys.stderr,
        )
        return None

    os.makedirs(target_dir, exist_ok=True)
    out = os.path.join(target_dir, pub.get("filename", "today.m4a"))
    bitrate = str(pub.get("aac_bitrate", 64000))

    if shutil.which("afconvert"):  # built into every Mac, no install needed
        subprocess.run(
            ["afconvert", wav_path, out, "-f", "m4af", "-d", "aac", "-b", bitrate],
            check=True,
        )
    elif shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-b:a", bitrate, out], check=True
        )
    else:  # last resort: just copy the WAV so it still works
        out = os.path.join(target_dir, "today.wav")
        shutil.copyfile(wav_path, out)

    print(f"[publish] iPhone copy ready in iCloud: {out}")
    return out


# ---------------------------------------------------------------------------
# Dated buffer publishing (keeps N days of lessons ready in iCloud)
# ---------------------------------------------------------------------------

def icloud_ready(cfg):
    """True if this Mac has iCloud Drive available."""
    return os.path.isdir(os.path.dirname(icloud_dir(cfg)))


def convert_to_m4a(wav_path, out_path, bitrate=64000):
    if shutil.which("afconvert"):  # built into every Mac
        subprocess.run(
            ["afconvert", wav_path, out_path, "-f", "m4af", "-d", "aac",
             "-b", str(bitrate)],
            check=True,
        )
    elif shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-b:a", str(bitrate), out_path],
            check=True,
        )
    else:
        raise RuntimeError("Need 'afconvert' (macOS) or 'ffmpeg' to make m4a.")
    return out_path


def dated_m4a_path(cfg, date):
    """iCloud path for a specific day's lesson, e.g. .../2026-06-19.m4a"""
    return os.path.join(icloud_dir(cfg), f"{date.isoformat()}.m4a")


def dated_exists(cfg, date):
    return os.path.exists(dated_m4a_path(cfg, date))


def publish_dated(cfg, wav_path, date):
    """Write a date-named .m4a into iCloud for the rolling buffer."""
    pub = cfg.get("publish", {})
    if not pub.get("enabled", False):
        return None
    if not icloud_ready(cfg):
        print("[publish] iCloud Drive not found on this Mac.", file=sys.stderr)
        return None
    os.makedirs(icloud_dir(cfg), exist_ok=True)
    out = dated_m4a_path(cfg, date)
    convert_to_m4a(wav_path, out, pub.get("aac_bitrate", 64000))
    print(f"[publish] {date.isoformat()} -> {out}")
    return out


def cleanup_old(cfg, today):
    """Delete iCloud dated .m4a files and local .wav/.txt from before today."""
    import datetime
    import glob

    # iCloud dated files
    d = icloud_dir(cfg)
    if os.path.isdir(d):
        for f in glob.glob(os.path.join(d, "*.m4a")):
            name = os.path.splitext(os.path.basename(f))[0]
            try:
                fd = datetime.date.fromisoformat(name)
            except ValueError:
                continue  # skip non-dated files like today.m4a
            if fd < today:
                try:
                    os.remove(f)
                except OSError:
                    pass

    # local working copies
    for f in glob.glob(os.path.join(LESSONS_DIR, "*")):
        name = os.path.splitext(os.path.basename(f))[0]
        try:
            fd = datetime.date.fromisoformat(name)
        except ValueError:
            continue
        if fd < today:
            try:
                os.remove(f)
            except OSError:
                pass


def play_audio(path):
    """Play a WAV file using whatever player exists on this machine."""
    if not os.path.exists(path):
        print(f"[play] No audio found at {path}", file=sys.stderr)
        return False

    # Try platform players in order of preference.
    candidates = [
        ["afplay", path],                       # macOS
        ["aplay", path],                        # Linux (ALSA)
        ["paplay", path],                       # Linux (PulseAudio)
        ["ffplay", "-nodisp", "-autoexit", path],  # ffmpeg, cross-platform
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            print(f"[play] {cmd[0]} -> {os.path.basename(path)}")
            subprocess.run(cmd, check=False)
            return True

    # Last resort: Python package.
    try:
        import simpleaudio as sa
        wave_obj = sa.WaveObject.from_wave_file(path)
        wave_obj.play().wait_done()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[play] No audio player available ({e}).", file=sys.stderr)
        return False
