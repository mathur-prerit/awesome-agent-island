# Agent playbook: build an agent-island theme from a spec

You are an AI coding agent (e.g. Claude Code). Your job: turn a **theme spec** (see `SPEC.md`) into a
validated, installable agent-island **data theme**, refining it with the user in conversation. Follow
these steps in order. The tools here are pure Python stdlib — no installs.

## 0. Read first
- `SPEC.md` (the spec format + the six canonical states and four sound cues).
- `art.py` (the pixel-art engine — sprite maps, palette, `working_sheet`/banner builders) and
  `synth.py` (the four chiptune cues). You will EDIT `art.py` to make the theme's art.
- The authoritative schema: agent-island's `Sources/AgentIslandApp/Themes/README.md`
  (`theme.json`, sprite rules, `tokenBands`/`visualBands`, asset/path rules).

## 1. Pin down the spec (talk to the user)
Fill any gaps in the spec by asking — but propose sensible defaults, don't interrogate. Lock: `id`
(== folder name), display name, layout (`banner` vs `inline`), the look of each of the six states, the
four sounds, and (optional) token bands + which state(s) change per band.

## 2. Lay out the theme folder
```
themes/<id>/
  theme.json
  sprites/   images/   sounds/
```

## 3. Generate sounds
`python3 synth.py themes/<id>/sounds` → `start/waiting/success/fail.wav`. Re-voice them by editing the
note sequences in `synth.py` if the user wants a different feel. Keep clips short (NSSound, no-overlap).

## 4. Generate art (edit `art.py`)
- The `working` state is the centrepiece: a wide animated **sprite sheet** (a single horizontal strip
  of `frameCount` cells). Author at **2× the point size** for Retina crispness; keep `frameWidth ≤ 4096`,
  `frameCount ≤ 1024`, `fps ≤ 240`.
- Edit the sprite **pixel-maps** (rows of characters → palette keys) and the **scene builder** to match
  the spec. Other states are static banners/glyphs (or short sprite loops).
- For **token bands**, render one `working` sheet per tier (e.g. `run_small/super/fire/star.png`).
- ALWAYS regenerate a `_preview.png`, up-scale it with `zoom.py`, and **look at it**. Iterate until it
  reads clearly at small size. Show the user.
- **Original art only** — draw it; never trace or embed copyrighted sprites.

## 5. Write `theme.json`
- `schemaVersion: 1`, `id` == folder name, `displayName`, `showsPersonaGlyph: false` for a banner.
- One `visual` per state (`sprite` | `image` | `text` | `symbol`); attach `sound` (`onEnter`) where the
  spec wants a cue. `layout: { ownRow: true/false, size: {width,height} }`.
- **Token bands:** add top-level `tokenBands` (ordered, ascending exclusive `upTo`, last is the
  catch-all) and per-state `visualBands` (band name → visual). Set `minAppVersion: "0.4.0"`.
- Colours: `#RRGGBB[AA]` · a `palette` name · `system:<name>` · `clear`.

## 6. Validate (the gate — never skip)
```sh
agentisland theme add ./themes/<id>
```
This runs the full validated pipeline. If it rejects, the error names the exact problem (`unknownField`,
`badTokenBands`, `unknownBand`, `disallowedAsset`, `pathTraversal`, sprite-dims, …) — fix and re-run
until it installs. Then `agentisland theme set <id>` + relaunch the app to see it; enable sound with
`agentisland config set soundEnabled true`.

## 7. Headless preview (optional, no live session needed)
From an agent-island checkout: `swift run AgentIslandApp -renderTheme <id> /tmp/out.png` renders all
six states through the real interpreter. (For token bands it renders at a fixed token count — to see
other tiers, eyeball the per-tier sheets directly.)

## 8. Refine
The user prompts changes ("slower", "bigger Mario", "more coins on the star tier") → edit `art.py` /
`synth.py` / `theme.json`, regenerate, re-validate, re-preview. Repeat.

## 9. Publish (if asked)
Zip it (`cd themes && ditto -c -k --keepParent <id> <id>.zip`), add a `themes/<id>/README.md` card +
preview image + a row in the repo README table, and open a PR. Run the **Publishing checklist** in the
repo README — especially: original/licensed assets only, WAV PCM sounds, validates clean.

## Hard rules
- **No copyrighted assets** ever get generated or committed (original pixel art + synthesized audio).
- **Always validate** with `agentisland theme add` before declaring done.
- **Always look at a preview** before claiming the art is good.
