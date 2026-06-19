# 📱 iPhone setup — cloud version (no Mac, with Skip)

Two simple Siri shortcuts. Do this once on the iPhone. After this, your uncle
just talks — no app, no buttons, no Mac, no always-on mic (Siri listens).

You need your audio URLs from the cloud setup first (see CLOUD_SETUP.md). They
look like, with `<YOU>` = your GitHub username:

- **Today:** `https://raw.githubusercontent.com/<YOU>/uber-anchor/main/public/today.m4a`
- **Pool:** `https://raw.githubusercontent.com/<YOU>/uber-anchor/main/public/pool/`

---

## Shortcut 1 — "Read to me" (plays today's story)

Open **Shortcuts** → **+** → add these actions:

1. Search **Get Contents of URL**, add it. In its URL box paste your **Today**
   URL exactly.
2. Search **Play Sound**, add it (it uses the downloaded audio from step 1).
3. Tap the name at top → rename to **Read to me** → Done.

Test: say **"Hey Siri, read to me."**

---

## Shortcut 2 — "Skip" (plays a different, random story)

Open **Shortcuts** → **+** → add:

1. Search **Random Number**, add it. Set **Minimum 1**, **Maximum 15**.
2. Search **Text**, add it. In the box, paste your **Pool** URL, then tap the
   variable bar and insert **Random Number**, then type `.m4a`.
   - It should read: `…/public/pool/`**[Random Number]**`.m4a`
3. Search **Get Contents of URL**, add it. Tap its URL field and insert the
   **Text** variable from step 2.
4. Search **Play Sound**, add it.
5. Rename to **Skip** (or "Another one" / "Skip this one") → Done.

Now: *"Hey Siri, read to me"* plays today's; *"Hey Siri, skip"* gives a random
recent one. Both work with the Mac off — the cloud keeps them fresh.

---

## Tips

- **First run** asks permission to access the URL — allow it.
- **Multiple wake phrases:** duplicate a shortcut and rename the copy (e.g.
  "I'm in my Uber") — each name becomes its own "Hey Siri, ___" trigger.
- **Keeps playing when the phone locks** — yes, like a podcast.
- **Pin to Home/Lock Screen** for a one-tap backup if Siri mishears.
- **"Could not load"** → the daily job hasn't run yet, or you're offline. Run
  the workflow once from the GitHub Actions tab (see CLOUD_SETUP.md).
