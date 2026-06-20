# 📱 iPhone setup — cloud version (no Mac, with Skip + voice-stop)

Two Siri shortcuts. Build them once on YOUR phone, test, then AirDrop to your
uncle. After this it's fully hands-free, no Mac, no maintenance.

Your live URLs (already working):
- **Today:** `https://raw.githubusercontent.com/aryansaksena2010-web/uber-anchor/main/public/today.m4a`
- **Pool base:** `https://raw.githubusercontent.com/aryansaksena2010-web/uber-anchor/main/public/pool/`
  (files are `1.m4a` … `15.m4a`)

> We use the **Open URLs** action (not "Play Sound") on purpose: it plays in the
> native iOS player, so **"Hey Siri, stop"** / "pause" / "skip" work by voice,
> and audio keeps playing with the screen off.

---

## Shortcut 1 — "Read to me" (today's story)

Shortcuts app → **+** → add these in order (use the search bar each time):

1. **URL** — add it, paste:
   `https://raw.githubusercontent.com/aryansaksena2010-web/uber-anchor/main/public/today.m4a`
2. **Open URLs** — add it (it auto-uses the URL above).
3. Tap the name at top → rename **Read to me** → Done.

Test: **"Hey Siri, read to me."**

---

## Shortcut 2 — "Skip" (a different, random story)

Shortcuts app → **+** → add:

1. **Random Number** — Minimum **1**, Maximum **15**.
2. **Text** — type the pool base, then insert the Random Number variable, then `.m4a`:
   `https://raw.githubusercontent.com/aryansaksena2010-web/uber-anchor/main/public/pool/`**[Random Number]**`.m4a`
3. **Open URLs** — add it; tap its field and insert the **Text** variable from step 2.
4. Rename **Skip** → Done.

Test: **"Hey Siri, skip."** (The cloud keeps all 15 pool files filled, so this
never errors.)

---

## Make Siri fully hands-free

On the phone (yours, and later your uncle's): **Settings → Apple Intelligence
& Siri**
- Turn ON **"Listen for 'Hey Siri'"** (or "Hey Siri").
- Turn ON **"Allow Siri When Locked."**

Now he doesn't unlock or tap anything — just speaks. To stop: **"Hey Siri,
stop."**

---

## Put it on your uncle's phone (AirDrop)

1. In Shortcuts, long-press the **Read to me** shortcut → **Share** → **AirDrop**
   → choose his iPhone. He taps **Add Shortcut**.
2. Repeat for **Skip**.
3. On his phone, do the "Make Siri fully hands-free" settings above.

Because both shortcuts point at the **same public URLs**, they work on his phone
with zero extra setup — the cloud feeds both phones.

---

## Tips

- **First run** asks permission to open the URL / use the data — allow it.
- **More wake phrases:** duplicate a shortcut, rename the copy (e.g. "I'm in my
  Uber") — each name is its own "Hey Siri ___" trigger.
- **If "Read to me" ever says no file:** the daily cloud job hasn't finished;
  re-run it from the repo's Actions tab. Normal days it's automatic at 6am UTC.
