# Acseda Cybersecurity

Open `index.html` directly, or serve this folder with `python3 -m http.server 8000`. No build step or runtime dependencies. Google Fonts needs an internet connection; system fallbacks are included.

- `index.html`: all sections, inline owl/icons, metadata and booking form.
- `css/styles.css`: design tokens, responsive layouts, interaction and motion styles.
- `js/main.js`: navigation, reveals, counts, console sequence, stack highlighting, calculator and validation.
- `assets/`: supplied placeholder photos and owl SVG favicon.
- `reference/`: approved design and source copy, local only (gitignored). `scripts/check-source.py` needs it.
- `scripts/`: source checks and optional browser verification.

The calculator beneath the example quotes and the form within the CTA band extend the approved design as requested. The stack reflows and packages use a segmented control on small screens. Without JavaScript, content, links and both packages remain visible.

Photos, contact details, incident sample, language display and legal labels remain placeholders. Form submission validates locally and displays a clearly identified preview success; it sends and stores nothing. The endpoint TODO is in `js/main.js`. Set `og:image` to an absolute production URL once the hosting address is known.

Run `python3 scripts/check-source.py` and `node --check js/main.js`. For browser checks, install Playwright as a local development tool (`npm install --no-save --package-lock=false playwright`), then run `BROWSER_EXECUTABLE=/usr/bin/google-chrome node scripts/check-browser.cjs`. It checks behavior and captures 1440, 1024, 768 and 390px screenshots in `screenshots/`.

Source and JavaScript syntax checks pass. Browser verification is unfinished: the supplied sandbox prevents Chrome/Chromium from starting; Firefox also crashes. No screenshots were produced. Commits are blocked because `.git` is mounted read-only; changes remain on `feat/landing-v1`, uncommitted. Nothing was pushed or merged.
