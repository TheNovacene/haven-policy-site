# Haven Policy Site

Public-facing static site for The Haven's policy stack. Generates from the Haven Policy Vault using Quartz v4 and deploys to GitHub Pages.

## What lives here

```
Haven Policy Site/
├── README.md                         ← this file
├── quartz.config.ts                  ← Haven branding and plugin config
├── quartz.layout.ts                  ← page layout
├── content/                          ← prepared markdown for the build (populated by sync script)
├── quartz/                           ← Quartz source (cloned, see Setup)
│   └── styles/
│       └── custom.scss               ← Haven CSS overrides (haven-specific + internal-only callouts)
├── scripts/
│   ├── sync-vault.py                 ← copies vault → content/ with role-holder substitutions and internal-only stripping
│   └── role-holders.json             ← canonical role → name/email mappings (mirror of vault _meta/role-holders.md)
├── .github/
│   └── workflows/
│       └── deploy.yml                ← GitHub Pages deployment workflow
└── .gitignore
```

## How it works

1. **Source of truth:** `~/Documents/Claude/Projects/The Haven/Haven Policy Vault/` (Obsidian vault).
2. **Sync step:** `scripts/sync-vault.py` copies the vault into `content/`, applying:
   - role placeholder substitutions (e.g. `{{Proprietor}}` → the actual name from `role-holders.json`)
   - email placeholder substitutions (e.g. `{{DSL email}}` → the actual address)
   - URL placeholder substitutions (e.g. `{{Haven anonymous reporting form URL}}` → actual URL)
   - stripping of `> [!internal-only]` callouts (these never appear on the public site)
   - exclusion of `_dashboards/`, `_templates/`, `_meta/` (vault-internal)
3. **Build step:** `npx quartz build` renders `content/` to `public/` as a static site.
4. **Deploy step:** GitHub Action publishes `public/` to GitHub Pages.

## First-time local setup

You need Node.js 22+ and Python 3.

```bash
cd "Haven Policy Site"

# 1. Install Quartz (clones into quartz/ subfolder)
git clone --depth 1 --branch v4 https://github.com/jackyzha0/quartz.git quartz-upstream
cp -r quartz-upstream/* . 2>/dev/null || true
cp -r quartz-upstream/.* . 2>/dev/null || true
rm -rf quartz-upstream

# 2. Install dependencies
npm install

# 3. Sync the vault into content/
python3 scripts/sync-vault.py

# 4. Preview locally
npx quartz build --serve
# → opens http://localhost:8080
```

## Updating the site

Whenever the vault changes:

```bash
cd "Haven Policy Site"
python3 scripts/sync-vault.py     # re-sync
npx quartz build --serve          # preview locally
```

Once happy, push to GitHub — the Action runs sync + build + deploy automatically.

## Deployment to GitHub Pages

Once the GitHub repo is created and connected:

1. Settings → Pages → Build and deployment → Source = GitHub Actions.
2. Push to `main`. The Action in `.github/workflows/deploy.yml` runs sync, build, and deploys to Pages.
3. The site is reachable at `https://{org}.github.io/{repo}/` initially.
4. Custom domain (e.g. `policies.thehavenonline.school`) can be added via Settings → Pages → Custom domain. Add a CNAME record at the DNS host pointing to `{org}.github.io`.

## Build targets

The sync script supports a build target via `--target`:

- `--target haven` (default) — substitutes role-holders for Haven; keeps `> [!haven-specific]` callouts; strips `> [!internal-only]`.
- `--target generic` — leaves role placeholders unsubstituted; strips both `> [!haven-specific]` and `> [!internal-only]` callouts. Used for a portable export of the policy stack for other schools to fork.
- `--target neo` — for future use; would substitute NEO's role-holders from a separate `role-holders-neo.json`.

## Privacy and safety

- The sync script deliberately strips `> [!internal-only]` callouts. The personal mobile number flagged in the Remediation List is inside one of these and will not appear on the public site.
- The vault's `_meta/role-holders.md` is excluded from sync. Names and email addresses appear on the public site only via placeholder substitution and only for the `haven` target.
- `_dashboards/` and `_templates/` are excluded from sync.

## Authoritative documents

For accreditation evidence, the audit dashboard and remediation list are not exposed publicly — they are vault-only. The sign-off provenance for each policy lives in the `sign_off_record:` frontmatter, which Quartz can render at the top of each policy.

## Maintenance

- When a role holder changes (e.g. new DSL appointed), update `scripts/role-holders.json` and `_meta/role-holders.md` in the vault. Re-sync. The new holder's name will replace the old one across all policies in the next build.
- When a policy changes, edit it in the vault, set `status: draft`, get re-signoff, set `status: live`, push. Site rebuilds automatically.
