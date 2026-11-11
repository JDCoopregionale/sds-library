# SDS Library — static site

A self-contained, password-gated chemical SDS library. No account needed to
view (just the access code), works on WiFi or cellular data, and you own
the whole thing once it's on GitHub.

## What's in here

- `index.html` — the whole site (search, categories, QR code generator, access gate)
- `sds/` — the SDS PDFs, one per product
- `sds-review.csv` — SDS date, supplier and last supplier check for each product
- `scripts/sds_review.py` and `.github/workflows/sds-review.yml` — the monthly review reminder
- `vendor/` — the QR code library (MIT licence), served from this site instead of an outside CDN
- This README

## Access code

The code isn't written here, because this repository is public. Ask the
H&S lead or accounting for it.

To change it, ask Claude to regenerate `index.html` with a new code
(takes a minute). A phone only
needs to enter it once; it stays unlocked on that device after.

**Heads up on what this code actually protects:** it's a simple deterrent
(keeps search engines and casual visitors out), not bank-level security —
someone with the code could technically download everything. Since SDS
sheets themselves are legally-required public safety documents (most are
already free on the manufacturer's site), that's a reasonable trade-off —
what you're really protecting is "our specific inventory, casually
browsable," not secret information.

## Deploying to GitHub Pages (10 minutes, no coding)

1. Go to [github.com](https://github.com) and sign up free if you don't
   have an account (use a coop email/organization one if you want it
   owned by the business, not a personal account).
2. Click **New repository**. Name it something like `sds-library`. Keep it
   **Public** (required for free GitHub Pages) — this is fine, since the
   passcode is what actually gates entry, and `index.html` tells search
   engines not to index it.
3. On the new repo page, click **uploading an existing file**.
4. Drag in `index.html`, `README.md`, and the entire `sds` folder (GitHub
   will keep the folder structure).
5. Click **Commit changes**.
6. Go to **Settings → Pages** (left sidebar).
7. Under "Build and deployment," set **Source: Deploy from a branch**,
   branch **main**, folder **/ (root)**. Save.
8. Wait ~1 minute, then refresh — GitHub shows your live URL, something
   like `https://yourusername.github.io/sds-library/`.

That URL is your permanent site. It'll keep working as long as GitHub
exists and the repo does — no subscription, nothing tied to any account
but yours.

## Printing QR codes

Open the site, enter the code, tap the **QR** button on any product for
its code, or **Master QR** at the top for one code linking to the whole
library. Each downloads as an SVG (scales to any size without blurring).

## Adding or fixing a product later

Easiest: send me the new/updated PDF and I'll regenerate `index.html` and
the `sds` folder — you re-upload the changed files to the same GitHub repo
(drag-and-drop again, GitHub will ask if you want to replace them — say
yes) and it's live again within a minute.

## Keeping SDS current

SDS don't expire in Ontario. An older sheet is fine as long as it's still the
supplier's latest version, and suppliers have to send updated sheets when they
change one. A good habit is still to check older sheets with the supplier
regularly, so the site tracks that for you:

- **SDS review** (button at the top of the site) lists every sheet that's 3+
  years old and hasn't been confirmed with the supplier in the last 12 months,
  plus any sheet with a known problem. It's grouped by supplier, so you can
  send one request per supplier.
- **Monthly reminder:** on the 1st of each month a GitHub Action updates an
  issue called "SDS review" with the same list. GitHub emails the repo owner.
  It closes itself when nothing is due. To run it right away, open the
  **Actions** tab → *SDS review reminder* → **Run workflow**.

When you've checked a sheet, edit `sds-review.csv` on GitHub (open the file →
pencil icon → Commit changes):

- **Supplier says it's still the latest:** put today's date in `last_checked`
  (format `YYYY-MM-DD`).
- **There's a newer version:** upload the new PDF to `sds/` with the same file
  name, then update `sds_date` and `last_checked`.
- **Something's wrong with a sheet** (wrong country, label instead of SDS):
  describe it in `problem`. Clear `problem` once it's fixed.

Each edit is checked automatically (bad dates, missing PDFs, extra rows). If
there's a mistake, the commit shows a red ✗ on GitHub with the reason.

The rules (3 years, 12 months) are at the top of `scripts/sds_review.py` and
in `index.html` (`REVIEW_AFTER_YEARS`, `RECHECK_AFTER_MONTHS`).

## Known limitation to review

Category tags (Herbicide/Fungicide/Insecticide/Other) were guessed from
filenames, not read from the actual SDS content — about 90 came back as
"Other." Worth a quick skim once it's live to correct any that are wrong;
categories are just for filtering, not required for the QR/lookup to work.
