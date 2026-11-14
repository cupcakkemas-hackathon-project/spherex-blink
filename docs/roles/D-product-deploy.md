# Role D: Product, deployment and presentation

**Your job:** make sure the project is correct, public, tested and presented well. The Space Apps judging guide says to give **presentation** as much attention as the technical criteria, and many teams lose points there.

Read `AGENTS.md` first (rules, facts, known traps, section 5 especially).

## You own
`README.md`, `docs/` (except `irsa_notes.md` (A) and `science_notes.md` (B)), `tests/` (create it), `.gitignore`, deployment files (`Dockerfile`, `render.yaml` or similar), the demo video and the submission text. You are also the team coordinator.

---

## D1. Repo and team set-up (tonight)
1. Create a shared GitHub repo with the project folder. Add a `.gitignore` containing at least `.cache/`, `__pycache__/`, `.venv/`, `*.fits`, `.env`.
2. Add everyone as collaborators. Agree: pull before starting, small commits, no force-push, one owner per file (`AGENTS.md` section 3).
3. Create GitHub issues for each task in the four role files (labels: A, B, C, D) so progress is visible.
4. Choose a team name and project name.
5. Pick a licence (MIT is a safe default) and add `LICENSE`.

**Done when:** all four people can clone, run the app in synthetic mode, and push.

## D2. Verify the five target coordinates (most important correctness task)
Create `docs/targets.md`: a table with name, RA, Dec (degrees), the epoch of those coordinates, proper motion (arcsec/year), and a recommended field of view. Use **SIMBAD** (https://simbad.cds.unistra.fr) and the challenge page. Known concerns:
- **WISE 0855**: challenge gives RA 08h55m10.831s, Dec -7d14m42.53s. It moves about 8 arcsec/year, so the position depends on the epoch.
- **Barnard's Star**: moves about 10 arcsec/year; the J2000 position is roughly 4 arcminutes away from where it is in 2026. Either use a position propagated to 2026 or a field large enough to include the motion.
- **Epsilon Indi B**: the current code probably holds the position of the bright star Epsilon Indi A. The B pair is several arcminutes away (verify the separation). Find B's own coordinates.
- **R Draconis**: the RA in `app.py` (245.39) looks wrong; it should be near 16h32m (about 248.2 degrees). Verify.
- **RW Aurigae**: verify.
Send the table to role A so `TARGETS` in `app.py` is updated.

**Done when:** `docs/targets.md` is complete, each value has a source, and role A has applied it.

## D3. Deployment
1. Choose a host that can run Python and make **outbound HTTPS requests to `irsa.ipac.caltech.edu`** (Render, Fly.io, Railway, a small VPS, or a Hugging Face Space). Free tiers may sleep or block outbound traffic: test early.
2. Start command: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT` (`requirements.txt` is at the repo root).
3. Environment variables: `CACHE_DIR` (use a persistent disk if the host has one), `MAX_FRAMES`, `SPHEREX_COLLECTION`.
4. After deploying, open `/healthz` (role A adds it, task A9), then a **live** request for WISE 0855 on the deployed site.
5. Before the demo and before judging, run `scripts/warm_cache.py` against the deployed server (role A writes it) so the five targets load instantly, and keep the server awake.
6. **Fallback, only with real data:** if live queries are too slow for judges, prepare cached results for the five targets generated from real data, and label them clearly in the UI as "cached real SPHEREx data fetched on <date>". Never use synthetic data as a fallback.

**Done when:** a public URL shows real WISE 0855 data, and you have tested it from a different network (a phone on mobile data).

## D4. Testing
- Create `tests/smoke_test.py` using FastAPI's `TestClient` (needs `httpx`; add to a `requirements-dev.txt`) that checks, with `source=synthetic`: `/api/targets` has 5 entries, `/api/frames` returns frames for all three modes, bad input returns 400, and the response matches the contract in `AGENTS.md` section 6.
- Keep a manual checklist in `docs/test_checklist.md`: for each of the 5 targets x 3 modes, record: loads? seconds? motion visible? bugs? Do this on the **deployed** site, with real data.
- File bugs as GitHub issues with the owner's label.

**Done when:** the smoke test passes locally and the checklist is filled in for real data.

## D5. Read the official guides (released 13 Nov)
Read the Space Apps **Judging and Awards Guide** and the **Project Submission Guide** (https://www.spaceappschallenge.org/resources/). Write `docs/submission_checklist.md` listing: what must be submitted, where, in what format, the deadline, what the video must contain, any rule about disclosing AI assistance, and the exact judging criteria. Share it with the team.

**Done when:** the checklist exists and every required item has an owner.

## D6. README and documentation
Keep `README.md` current: challenge explanation, definitions, screenshots (from role C), how to run, honest status table, limitations, and a short paragraph on how updating with new data works (from role A task A7). Replace the "Current status" table as things get finished. Add a short architecture sentence for judges.

**Done when:** a judge can understand and run the project from the README alone.

## D7. Demo video (about 2 minutes) and script
Write the script in `docs/demo_script.md` and record with a screen recorder (use real data on the deployed site):
1. Hook (10 s): "Pluto was found because one dot moved."
2. Live demo on WISE 0855, motion visible (40 s).
3. A standout feature: stack, difference or spectrum (30 s).
4. URL embedding and automatic new-data updates (20 s).
5. Impact: anyone can now help look for discoveries; honest limits (20 s).
Record 2-3 takes. Check the audio. Add captions if possible.

**Done when:** a final video exists, is under the allowed length, and shows only real data.

## D8. Submission text
Write the project summary: what it does, how it answers the challenge, what data it uses (SPHEREx via IRSA), what is original, limitations, future work, team members. Include the SPHEREx acknowledgement text and DOI (QR2: 10.26131/IRSA652) exactly as IRSA states on its SPHEREx page (copy the wording from the page, do not paraphrase). Credit the tools used (Astropy, reproject, FastAPI, Aladin if used).

**Done when:** the text is ready and the team has proofread it.

## D9. Coordination and timeline
- Short check-in with the team every ~4 hours: what is done, what is blocked.
- Watch role A: if A3 (real frames) is not done by hour 8, everyone helps.
- **Hour 40: feature freeze.** Hours 40-46: full test on the deployed site, video, README, submission. Submit before the deadline with margin (aim for hour 46).

## Hand-offs
- From A: live demo working, updating notes, health endpoint.
- From B: caveats and talking points.
- From C: screenshots.
- To A: verified coordinates (D2).
- To everyone: bug list and the submission checklist.
