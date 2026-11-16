# dotdoctor launch kit

## The test

Run for **3 weeks**. Build Pro only if we hit **either**:

- **50 waitlist signups**, or
- **100 GitHub stars**

Under 15 signups and under 30 stars after 3 weeks: the problem isn't painful enough. Try a different angle or idea (we still keep the content and audience).

Track every Sunday:

| Week | Stars | Signups | Video views | Best-performing post |
|------|-------|---------|-------------|----------------------|
| 1    |       |         |             |                      |
| 2    |       |         |             |                      |
| 3    |       |         |             |                      |

## One-time setup (≈1 hour, £0–£12)

1. ✅ GitHub repo created: github.com/Deltaharsha/dotdoctor
2. Make a free form at formspree.io (or Tally). Replace `FORM_ID` in `docs/index.html`.
3. ✅ Landing page on GitHub Pages: deltaharsha.github.io/dotdoctor
4. Optional: buy `dotdoctor.dev` (~£10/yr), then replace `DOMAIN` in `README.md`.

## Video 1: the 60-second short (YouTube Shorts / TikTok / Reels)

Record with OBS: terminal full screen, big font (18pt+). Cut in Kdenlive.

| Time | On screen | Voice / caption |
|------|-----------|-----------------|
| 0–3s | Pressing SUPER+E, the wrong app opens | "My keybind opened the wrong app. Again." |
| 3–10s | Scrolling a huge bindings file | "Hyprland quietly runs *every* action bound to a key. One forgotten default and your shortcuts fight each other." |
| 10–15s | Type `./dotdoctor.py --demo` | "So I built a doctor for my dotfiles." |
| 15–40s | Output appears; zoom on each finding | "Keybinds doing 3 things. Shortcuts launching apps I uninstalled. Symlinks to a dotfiles repo I deleted last year." |
| 40–52s | Add the `hl.unbind` line, rerun, all green | "One line, rerun, fixed." |
| 52–60s | GitHub link on screen | "It's free and open source. Link in bio. What should it check next?" |

End with a question. Comments push the video to more people.

## Video 2: the longer YouTube video (8–12 min)

**"I built a tool that finds what's broken in your Linux setup"**

1. The problem (my own config breaking after updates)
2. Why it's hard: Lua configs, live vs written binds, false alarms
3. Live build: the false-alarm fix story (13 warnings → 0 on a healthy setup)
4. Running it on viewers' configs (ask for submissions in Video 1's comments)
5. Pro waitlist and roadmap

## Written posts (copy, tweak, post)

Space them out: one community per day, not all at once. Reply to every comment within the first 2 hours.

### r/hyprland and r/omarchy

> **Title:** I made a tool that finds conflicting keybinds and broken configs in Hyprland (works with the new Lua configs)
>
> After my third "why does SUPER+E open the wrong thing" moment I wrote dotdoctor. It reads your *live* binds from hyprctl (so it works with Lua configs and Omarchy) and flags:
>
> - keys bound to 3+ actions (forgotten defaults)
> - shortcuts that launch programs you don't have
> - broken symlinks in ~/.config
> - Hyprland config errors
>
> Read-only, no dependencies, MIT. `./dotdoctor.py --demo` shows it on a broken example.
>
> [GitHub link]
>
> What should it check next? Waybar? Neovim? I'm taking requests.

### r/unixporn

Post a screenshot of your desktop with dotdoctor output in a terminal. Use the flair they require. Put the link in a comment, not the post body.

### Hacker News (week 2 or 3, after fixing early feedback)

> **Title:** Show HN: dotdoctor – a checkup for your Linux desktop config
>
> Post on a weekday around 2–4pm UK time. In the first comment, explain why you built it and what was hard (false positives).

### X / Bluesky / Mastodon

> My Hyprland config had a key doing 3 things at once and I had no idea.
>
> Built a tiny doctor for dotfiles. Free, open source, one command. 🩺
>
> [30s screen recording] [link]

## Weekly rhythm (fits 5–15 h/week)

| Day | Task | Time |
|-----|------|------|
| Mon | Fix or add one thing users asked for | 2–3 h |
| Wed | Record and edit one short | 1–2 h |
| Fri | Post the short + one written post | 1 h |
| Sun | Fill in the tracking table, reply to issues | 30 min |

## Rules

- Never post your waitlist link without something useful next to it (the free tool, a fix tip).
- Read every subreddit's self-promotion rules before posting.
- Every bug report is content: "a viewer found a bug, here's the fix".
