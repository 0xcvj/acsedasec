Browser screenshots could not be captured in this environment.

Chrome exits at startup with `setsockopt: Operation not permitted`.
Chromium headless shell exits with `sandbox_host_linux.cc:41 ... shutdown: Operation not permitted`.
Firefox headless exits with signal 139.

Run `scripts/check-browser.cjs` in an environment that permits browser processes. It saves full-page desktop-1440.png, desktop-1024.png, desktop-768.png and mobile-390.png here. It uses reduced motion to make the captures stable and scrolls the page to load the supplied photos before capture.

Visual comparison against `reference/acseda-landing-preview.png` is pending. No substitute or fabricated screenshots are included.
