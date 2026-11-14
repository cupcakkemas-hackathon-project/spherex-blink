# Role C: Frontend

**Your job:** make the page understandable to a stranger in 10 seconds, pleasant to use, and good on a phone. Judges judge what they can see.

Read `AGENTS.md` first (rules, API contract in section 6).

## You own
Everything in `frontend/`. Do not edit the backend. If you need a new API field, ask role A.

## What exists today
`frontend/index.html` is one self-contained page (HTML, CSS and JavaScript, no build step):
- Search panel: RA, Dec, field of view, view mode (single/stack/diff), data source (live/synthetic), Search button, five target buttons loaded from `/api/targets`.
- A canvas that shows frames from `/api/frames` as an animation, a frame info box (frame number, MJD, detector, wavelength, flags, position), play/pause, scrub slider, speed select.
- URL parameters `?ra=&dec=&fov=&mode=&source=` are read on load and written after a search.
- A red banner when the data source is synthetic.

Frames are PNGs, **north up, east left**, 64x64 px, displayed with `image-rendering: pixelated`.

Keep it dependency-free where possible. If you add a library, load it from `cdnjs.cloudflare.com` with an **exact pinned version**.

---

## C1. Run it and review it (30 min)
Run the app (see `AGENTS.md` section 7), use `source=synthetic`, click every control, and write a list of 5-10 things that confuse or annoy you as a first-time user. Keep the list in a GitHub issue or in your notes.

**Done when:** you have the list; use it to prioritise C2-C8.

## C2. Make it self-explanatory
- Short one-paragraph "what am I looking at?" text near the top: dots that stay put are far stars; a dot that moves between frames is a nearby object such as a comet, asteroid, brown dwarf or star.
- A loading state: spinner or progress message while fetching (live queries can take 10-60 seconds). Disable the Search button while loading.
- Friendly error messages (the backend sends `{"detail": "..."}` with 400, 404, 502). 404 means "no SPHEREx images cover this position yet".
- Add a small note that the frames are in time order and that brightness can change because the wavelength changes.
- Keep the red synthetic banner. Never hide it.

**Done when:** someone who has never seen the page can use it without asking you a question.

## C3. Mobile and layout
- Test at 375 px width (browser dev tools). No horizontal scrolling; controls wrap; the image stays square and large.
- Touch-friendly buttons (at least 40 px high).

**Done when:** the whole flow works on a phone-sized screen.

## C4. Click to select a point
- When the user clicks the image, draw a marker (a small circle) and show the sky position of that point in the info box.
- Convert canvas click to pixel coordinates using the displayed size: `x = (event.offsetX / cssWidth) * canvas.width`, same for `y`. Then use the geometry formulas in `AGENTS.md` section 6 (grid centre at 31.5, north up, east left). Use `size_px` and `pixel_scale_arcsec` from the response when role A has added them; until then assume 64 and `fov*60/64`.
- Keep the marker drawn on every frame as the animation plays.

**Done when:** clicking on the centre of the picture reports a position within about 1 pixel of the search position.

## C5. Spectrum plot (needs role B task B6)
- After a click, call `/api/spectrum?ra=&dec=&fov=&x=&y=` (x and y are **array** indices: array row = `63 - canvasRow`; confirm with role B).
- Draw a simple chart: wavelength (micron) on x, flux (MJy/sr) on y, error bars if given, points coloured by detector. A hand-drawn canvas or SVG is fine; Chart.js (pinned version, from cdnjs) is also fine.
- Handle "loading", "no data" and error states.

**Done when:** clicking a bright star shows a spectrum under the image.

## C6. Better frame information
- Show detector as a coloured chip (6 distinct, colour-blind-safe colours) and wavelength in micron.
- A thin timeline under the slider showing where each frame sits in time (dots or ticks), with the current frame highlighted.
- Show the flags text clearly; if it says nothing is flagged, show a calm "no flags".

**Done when:** every field in the frame object is visible somewhere sensible.

## C7. Controls
- Keyboard: Space = play/pause, Left/Right = previous/next frame.
- Step buttons (previous/next), a speed control, optional "reverse".
- Optional: "Download as GIF" or "Copy link" button. Copy link copies the current URL (the URL state already holds the settings).

**Done when:** you can step frame by frame with the keyboard.

## C8. Embedding mode
- Support `?embed=1`: hide the header text and the example buttons, keep the viewer and controls, remove outer margins. This is the "embed in other websites" feature the challenge mentions.
- Make sure all settings round trip through the URL.

**Done when:** `/?ra=...&dec=...&embed=1` looks good inside an `<iframe>`; test with a tiny local HTML page.

## C9. Stretch: sky context with Aladin Lite
- Add an optional side panel using **Aladin Lite** (from CDS Strasbourg, load a pinned version from a CDN) centred on the same RA/Dec and field of view, with a survey layer (for example WISE or Gaia) so users can compare our images with other telescopes.
- Only after C1-C8 are done.

## C10. Accessibility and polish
- Colour contrast, visible focus outlines, `aria-label`s on buttons and canvas, no information conveyed by colour alone.
- Make a title, favicon and page description. Take two good screenshots for the README (send them to role D).

## Hand-offs
- From A: `size_px`, `pixel_scale_arcsec` in the response; live data working.
- From B: spectrum route.
- To D: screenshots, any text that should go in the README.
