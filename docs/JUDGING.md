# What the judges look for, and how to build toward it

**Status of this file:** the Space Apps 2026 Judging and Awards Guide was due 13 Nov. The criteria below come from older guides and a 2026 event handout, **not yet checked against the 2026 guide**. Role D must read the official guide and correct this file. Until then, treat the list as a good guess, not as fact.

Official pages:
- https://www.spaceappschallenge.org/resources/judging-awards-guide
- https://www.spaceappschallenge.org/resources/project-submission-guide/
- https://www.spaceappschallenge.org/resources/participant-faqs/

## What is confirmed vs. not

| Item | Confidence |
|---|---|
| The challenge page itself gives **no scoring sheet**; it only lists optional ideas (see `docs/CHALLENGE.md`) | Confirmed |
| Past guides: teams confirm "All Work is Original", list all code, data, tools and resources used (even open source), and clearly say where and how AI tools were used | From the 2025 guide; check the 2026 version |
| Criteria named in past guides and event handouts: Impact, Creativity, Validity; also commonly Relevance and Presentation | Partly from memory; verify |
| Presentation (clear video and write-up) is treated as seriously as the technical criteria | From the guide; verify |
| Organizer said an unfinished AI-assisted starting prototype is allowed if it is modified during the two days | Told to the team by the organizer; keep the written proof |

## The criteria and what to do about them

| Criterion | What judges likely want | What we do |
|---|---|---|
| **Validity** (does it really work, is the science right) | Real SPHEREx data, nothing faked, honest limits | Live IRSA data for all 5 test targets. Never show synthetic data as real. State limits (6.2 arcsec pixels, wavelength changes between frames, proper motion). |
| **Relevance** (does it answer the challenge) | Exactly what the brief asks: enter RA/Dec, get a "little video" of SPHEREx images that makes movers easy to spot | Stay close to `docs/CHALLENGE.md`. Test on Barnard's Star, Epsilon Indi B, WISE 0855, RW Aur, R Dra. Coordinates in the URL. |
| **Impact** (useful to real people) | Non-experts can use it in seconds, and it helps discovery | Example buttons, clear explanation on the page, no setup, works on a phone, embeddable. |
| **Creativity** (original ideas) | One or two memorable features, not ten half-finished ones | Pick from the brief's "extra kudos" list: stacking per detector and spectra on the fly. Do these well. |
| **Presentation** (communication) | Clear 2-minute video, clean README, a live link that works | Role D owns this. Rehearse. Record only real data. |

## Rules of thumb for every agent and teammate
1. A smaller tool that works smoothly on real data beats a bigger one that is half-working.
2. Build in this order: real frames for WISE 0855, then all five targets, then one standout feature, then polish and deploy, and only then stretch goals (Gaia/WISE overlay).
3. Every feature should support one sentence: *"Type any sky position and watch SPHEREx's view of it change over time, so anyone can spot moving objects."* If it does not, skip it.
4. Anything a judge will see must be correct: the live page, the demo video, the README, the submission text.
5. **Feature freeze at hour 40.** The last 8 hours are for testing, the video and the submission.

## What each role does for the judges
- **A (Data):** Validity. Real data, fast enough for a demo, updates automatically.
- **B (Image and science):** Validity and Creativity. Stacking, difference mode, spectra, honest science notes.
- **C (Frontend):** Impact and Presentation. Clarity, mobile layout, embed mode, good screenshots.
- **D (Product):** Relevance and Presentation. Verified coordinates, deployed link, tests, README, 2-minute video, submission text, the checklist from the official guides.

## Submission honesty (important)
- List every data source, library and tool, including AI assistance, as the guide requires.
- Keep the organizer's written confirmation about the starting prototype.

## Demo video outline (about 2 minutes, real data only)
1. Hook, 10 s: "Pluto was found because one dot moved."
2. Live demo on WISE 0855 with visible motion, 40 s.
3. One standout feature (stack, difference or spectrum), 30 s.
4. URL embedding and automatic updates with new data, 20 s.
5. Impact and honest limits, 20 s.
