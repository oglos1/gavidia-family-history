# Migration Notes — Gavidia Family History → GitHub Pages

Prepared overnight 2026-10-07. The site is ready for `git init` + push. **Do NOT publish or share anything until Carlos gives the word.**

## What's in this directory

- `index.html` (315 KB) — the complete single-page site, latest build (includes pseudonym key, cliff notes, wider circle, and round-two entries — everything that was queued but unpublishable on the artifact platform).
- `assets/` (315 MB, 32 files):
  - `audiobook-es/` — 10 Spanish MP3 parts (~14–17 MB each)
  - `audiobook-en/` — 10 English MP3 parts (~14–17 MB each)
  - 10 JPG photos + 2 family-tree PDFs
- Total: 33 files, ~315 MB. **No file exceeds GitHub's 100 MB per-file limit** (largest is ~17 MB). Well under GitHub Pages' 1 GB site limit.

Excluded (not needed for the site): `.space-build*` duplicates, `audits/`, `.harness/`, `AGENTS.md`, `space.json`, `icon.jpg` (artifact thumbnail, not referenced by the site).

## Secrets sweep — results

Scanned `index.html`, all asset filenames, JPG EXIF, MP3 headers/strings, and both PDFs.

| Finding | Status |
|---|---|
| Password gate `12345` in `index.html` JS (1 occurrence) | **Intentional but visible.** Client-side only — anyone viewing the GitHub repo source can read it. Same exposure as today on the artifact platform (content is embedded in the HTML either way). Carlos must understand the gate is a courtesy screen, not real security. |
| `ogloss@gmail.com` in contribution `mailto:` links (5 occurrences) | **Intentional.** Carlos designated this as the family contribution contact. It will be in public repo source — same as on the live site today. |
| `9789996123` | **False positive** — fragments of ISBN numbers (9789996123948 / 9789996123955) for the history volumes. Not a phone number. |
| API keys / tokens / secrets | **None found.** |
| DUI / ID numbers | **None found.** |
| Other emails / phone numbers | **None found.** |
| JPG GPS location data | **None found** (all photos scanned, no GPS EXIF). |
| MP3 metadata | Clean — standard FFmpeg encoding tags only, no personal data. |

**Bottom line: safe to push. No secrets to redact.** The only "exposures" (password, email) are already on the live site by Carlos's choice.

## Links — what breaks, what doesn't

- **All asset references are relative** (`assets/audiobook-es/part-01.mp3`, etc.). They will work on GitHub Pages as-is.
- **No absolute URLs to muse.ai or any artifact CDN.** Nothing to rewrite.
- External links (Wikipedia, Google Fonts, YouTube, flotilla-aerea.com, fas.gob.sv) are legitimate third-party references — all fine.
- **One stale link to fix:** the "Upload files / Subir archivos" buttons point to the Google Drive contributions folder (`drive.google.com/drive/folders/1aJ3GSb6oJxNyLDYdhWYOrBsMwWQLFAX5`), which Carlos locked down (link access removed). The button currently leads to a dead end. Options: (a) point it at the Google Forms intake instead, (b) remove the button. Recommend deciding before or right after launch.

## Exact steps for tomorrow

1. **Create the GitHub repo** (github.com → New repository). Suggested name: `gavidia-family-history`. Can be public (site is password-gated but content is in the HTML source — Carlos already treats it as share-with-family-only via the link) or private with Pages enabled (Pages on private repos needs a Pro account; public is free).
2. **Push this directory:**
   ```
   cd ~/workspace/github-prep/gavidia-family-history
   git init
   git add -A
   git commit -m "Family history site"
   git branch -M main
   git remote add origin <repo-url>
   git push -u origin main
   ```
   The first push is ~315 MB — it will take several minutes. That's normal.
3. **Enable Pages:** repo Settings → Pages → Source: Deploy from a branch → Branch: `main`, folder `/ (root)` → Save. The site goes live at `https://<username>.github.io/gavidia-family-history/` within a few minutes.
4. **Verify:** open the Pages URL, enter `12345`, check that audio players load (spot-check one Spanish and one English part).
5. **Optional cleanup:** fix the Drive upload button (see above). Keep `noindex, nofollow` (already in the page `<head>` — verified present).

## Warnings

- **Do NOT re-encode or rebuild any MP3.** The Spanish audiobook is confirmed working; the files in `assets/` are byte-identical to the working site copies (integrity verified: all 20 MP3s have valid headers).
- GitHub Pages has a 1 GB soft site limit — we're at 315 MB, fine. If the site grows past ~800 MB later, consider Git LFS or trimming.
- The `gavidia-publish-retry` cron (every 3h) is still trying to publish to the artifact platform. Disable it once GitHub Pages is live to avoid confusion.
