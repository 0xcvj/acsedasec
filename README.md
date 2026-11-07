# Acseda Cybersecurity

Serve this folder with `python3 -m http.server 8000` (opening `index.html` directly also works, but the EN/NL links point at folders and only resolve on a web server). No build step or runtime dependencies. Google Fonts needs an internet connection; system fallbacks are included.

- `index.html`: English page: all sections, inline owl/icons, metadata and booking form.
- `nl/index.html`: Dutch page with identical markup and classes (assets via `../`). Keep both pages structurally in sync; `scripts/check-source.py` fails if they drift.
- `css/styles.css`: design tokens, responsive layouts, interaction and motion styles.
- `js/main.js`: navigation, reveals, counts, console sequence, stack highlighting, calculator and validation. JS-generated text (menu label, number format, calculator total, form messages) comes from a small dictionary keyed by `<html lang>`.
- `assets/`: supplied placeholder photos and owl SVG favicon.
- `reference/`: approved design and source copy, local only (gitignored). `scripts/check-source.py` needs it.
- `scripts/`: source checks and optional browser verification.

Language: the header switch links `EN` to `./` (or `../` from `nl/`) and `NL` to `nl/`, marking the current language with `aria-current`. Both pages carry `hreflang` alternates (relative; make them absolute once the production URL is known). There is no redirect based on browser language.

The calculator beneath the example quotes and the form within the CTA band extend the approved design as requested. The stack reflows and packages use a segmented control on small screens. Without JavaScript, content, links and both packages remain visible.

Photos, contact details, incident sample and legal labels remain placeholders. Form submission validates locally and displays a clearly identified preview success; it sends and stores nothing. The endpoint TODO is in `js/main.js`. Set `og:image` to an absolute production URL once the hosting address is known.

Run `python3 scripts/check-source.py` (validates both pages, the language switch, hreflang and EN/NL structural parity) and `node --check js/main.js`. For browser checks, install Playwright as a local development tool (`npm install --no-save --package-lock=false playwright`; run it where a `package.json` or `node_modules` exists, as npm otherwise installs into the nearest parent `node_modules` and prunes it), then run `BROWSER_EXECUTABLE=/usr/bin/google-chrome node scripts/check-browser.cjs`. It serves the folder over HTTP itself, checks both languages (behavior, language switch, no leftover English on the Dutch page) and captures 1440–390px screenshots in `screenshots/`.

