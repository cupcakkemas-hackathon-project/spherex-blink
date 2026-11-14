# Team brief: NASA Space Apps 2026, "Planet X and SPHEREx"

Event: 14-15 November 2026. Team of 4. **This file is planning and background only. No coding is needed before the event starts.**

## 1. The challenge in plain words

NASA's **SPHEREx** space telescope photographs the whole sky again and again, in 102 colours of infrared light. It produces far more images than any person can look through.

Astronomers use a simple trick: take two photos of the same patch of sky on different dates. Almost everything stays still, because stars are very far away. Things close to us **move**: comets, asteroids, brown dwarfs and nearby stars. Spot the dot that moved and you may have found something. This is how Pluto was discovered. Volunteers have found many comets, stars and brown dwarfs this way.

**What we must build:** a public web tool where a user enters the coordinates of a patch of sky (Right Ascension and Declination). The tool shows a series of SPHEREx images of that patch like a little video, so moving objects are easy to spot.

We are not expected to discover anything ourselves. We are building the tool that helps everyone else look.

**Test targets named by the challenge:**
- Barnard's Star
- Epsilon Indi B (a pair of brown dwarfs orbiting a star)
- WISE 0855 (a fast-moving brown dwarf, RA 08h55m10.831s, Dec -7d14m42.53s)
- RW Aurigae and R Draconis (variable stars)

**Optional ideas from the challenge (bonus only after the core works):**
- Easy to update as new SPHEREx data arrives (new data comes weekly)
- Add together the images from each of the six detector arrays to make faint things clearer
- Spectra on the fly ("extra kudos")
- Add or subtract images taken at different times
- Let users choose the field of view
- Overlay data from other telescopes, such as Gaia or WISE
- Coordinates in the web address (URL), so the tool can be embedded elsewhere
- Show metadata such as contamination flags
- Use existing tools such as Astropy and Aladin

## 2. Words explained

| Word | Meaning |
|---|---|
| **SPHEREx** | A NASA space telescope launched in 2025. It maps the whole sky every six months in 102 colours of near-infrared light. |
| **IRSA** | NASA/IPAC Infrared Science Archive, run by Caltech. NASA's online library for infrared telescope data. SPHEREx's images are stored there and programs can download them. |
| **Cutout** | Instead of downloading a huge full image (about 70 MB), ask for only a small square around the spot. |
| **WISE** | An older NASA infrared space telescope. WISE 0855 is a cold brown dwarf it discovered and is one of our test objects. WISE data could also be an optional overlay. |
| **RA and Dec** | The sky's longitude and latitude. Two numbers give an address for any spot in the sky. |
| **Brown dwarf** | An object bigger than a planet but too small to be a star. Dim and cold; nearby ones move noticeably. |
| **Gaia** | A European Space Agency telescope that measures positions and motions of over a billion stars. |
| **Aladin** | A free sky-viewer tool from the CDS data centre in Strasbourg that can be embedded in websites. |
| **Detector array** | SPHEREx has six detectors, each seeing a different range of infrared colours. |
| **Stacking** | Adding several images together so faint objects become clearer. |
| **Difference image** | Subtracting one image from another so static things disappear and movers remain. |

## 3. Roles

| Role | Person | Focus |
|---|---|---|
| **A: Data** | Dhiya | Get real SPHEREx images from IRSA for a given position. The biggest risk, because everyone depends on it. |
| **B: Image and science** | Ian | Make the images reveal moving objects (stacking, differencing); build the spectrum feature; keep the science honest. |
| **C: Frontend** | Sam | The website: search box, animation player, controls, info panel, mobile layout. |
| **D: Product, deploy and presentation** | Riff | Verify the target coordinates, put the project online, test everything, write the README, record the 2-minute video, write the submission. |

## 4. What each person can do before the event (no coding)

**Everyone**
- Register for the 2026 NASA Space Apps Challenge on the official site and join the challenge "Planet X and SPHEREx" and our team (needed to qualify for global judging).
- Install Python 3.10 or newer, VS Code and Git, and make sure they work.
- Read this brief. Read the **Judging and Awards Guide** and **Project Submission Guide** (released 13 Nov). Note anything about originality, AI-tool disclosure and what the video must contain.
- Check your time zone against the event start and agree on a meeting time.

**A (Dhiya):** read the IRSA SPHEREx pages (spherex-data-access and the intro and cutouts tutorials on caltech-ipac.github.io) so the data approach is clear.
**B (Ian):** read about SPHEREx spectral images and the six detectors; think about how stacking and difference images work.
**C (Sam):** look at Backyard Worlds (backyardworlds.org), a similar blink-style tool, for ideas about what is easy to use.
**D (Riff):** look up the five targets in SIMBAD (simbad.cds.unistra.fr): coordinates, the date the coordinates are for, and proper motion. Fast movers such as Barnard's Star and WISE 0855 may be far from older catalogue positions.

## 5. What success looks like

A working public website using **real SPHEREx data**, where anyone types coordinates and watches an animation that makes moving objects easy to spot. It works on the five test targets, comes with a clear README and a 2-minute demo video, and honestly states its limits.

## 6. Ground rules

- Be honest in the submission about what we built, which tools and AI assistance we used, and what data we used.
- Never show fake or synthetic data as if it were real.
- Agree who owns which part, so we do not overwrite each other's work.
