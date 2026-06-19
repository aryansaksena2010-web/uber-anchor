# ☁️ Cloud setup — runs forever, no Mac needed

This makes a free server (GitHub Actions) generate a new story every day and
publish it, so your uncle's phone always has fresh content **even if no computer
is ever turned on again**. After this one-time setup, it's fully autonomous.

```
  GitHub Actions (free server)        GitHub repo (public)         iPhone
 ┌───────────────────────────┐  cron  ┌────────────────────┐  HTTPS ┌──────────┐
 │ every day: write story +  │ ─────► │ public/today.m4a   │ ─────► │ Hey Siri,│
 │ voice, rotate 15-pool     │        │ public/pool/1..15  │        │ read /skip│
 └───────────────────────────┘        └────────────────────┘        └──────────┘
```

There are no API keys to buy and no servers to rent. GitHub's free runners do
the work; the only account you need is a free GitHub account.

---

## What only YOU can do (I'm not allowed to)

I can't create accounts or type your passwords/tokens anywhere — that's a hard
safety rule. So these three are yours; everything else is already built:

### 1. Make a free GitHub account + repo
- Go to <https://github.com/signup> and create an account (free).
- Create a new repository: name it `uber-anchor`, set it to **Public**
  (public = free unlimited Actions + the phone can fetch the audio with no
  login). Don't add a README.

### 2. Push this project to it (one time)
GitHub will show you commands after creating the repo. In Terminal:

```bash
cd ~/Desktop/uber-anchor
git init
git add .
git commit -m "Uber Anchor"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/uber-anchor.git
git push -u origin main
```

When it asks you to sign in, follow the browser prompt (or paste a Personal
Access Token). That's the only auth step.

### 3. Turn on write permission for the robot
In your repo on github.com: **Settings → Actions → General → Workflow
permissions →** choose **"Read and write permissions" → Save.**
(This lets the daily job publish the audio back to the repo.)

---

## Kick off the first run

In your repo: **Actions** tab → "Daily Uber Anchor Lesson" → **Run workflow**.
It takes ~5–15 min the first time (it installs the AI + voice on the server).
When it finishes, you'll have `public/today.m4a` and `public/pool/1.m4a…15.m4a`
in the repo. After that it runs automatically every day at 06:00 UTC.

> Change the time by editing the `cron` line in
> `.github/workflows/daily.yml` (it's in UTC).

---

## Your audio URLs (for the phone)

Once the first run finishes, your files are at (replace `<YOU>`):

- Today's story:
  `https://raw.githubusercontent.com/<YOU>/uber-anchor/main/public/today.m4a`
- Skip pool (random of 15):
  `https://raw.githubusercontent.com/<YOU>/uber-anchor/main/public/pool/1.m4a`
  … through `/pool/15.m4a`

Give these to the phone setup — see **IPHONE_SETUP.md**.

---

## Notes

- **Voice/model on the server:** to keep the free runner fast, the cloud job
  uses a lighter AI model (`llama3.2:1b`). The voice (Kokoro) is identical to
  the Mac version. You can bump the model in `daily.yml` if you want richer
  writing (slower runs).
- **Cost:** public repo = unlimited free Actions minutes. $0.
- **The Mac version still works too** — this just removes the need for it.
