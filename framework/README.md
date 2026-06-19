# Theme-authoring framework

A tiny, **dependency-free** (pure Python stdlib) toolkit for generating agent-island **data themes**
from a plain-language spec — designed so a coding agent (Claude Code) can read a spec, refine it with
you in conversation, and produce a validated, installable theme.

## What's here

| File | What it does |
|------|--------------|
| `art.py` | A pixel-art engine with its **own PNG encoder** (no Pillow). Draws original chunky sprites and composes them into the wide animated **sprite sheets** + per-state banners a theme needs. Edit the sprite maps / palettes / scene to make your own art. |
| `synth.py` | Synthesizes the four **chiptune lifecycle cues** (`start`/`waiting`/`success`/`fail`) as short WAV PCM — all original square-wave audio, no copyrighted clips. `python3 synth.py <out_dir>`. |
| `zoom.py` | A nearest-neighbour PNG up-scaler (with PNG filter handling) to eyeball tiny pixel art. `python3 zoom.py in.png out.png 3`. |
| `SPEC.md` | The **spec format** you (or the agent) fill in to describe a theme. |
| `AGENTS.md` | The **playbook** an AI agent follows to turn a spec into a theme. |
| `examples/spec-mario.md` | The Super Mario theme written as a spec (a worked example). |

## The idea

A data theme is just **config + assets**. The hard parts are (a) drawing crisp tiny pixel art that
slices cleanly into sprite sheets, and (b) getting the `theme.json` schema exactly right. This
framework handles both: `art.py`/`synth.py` produce pixel-perfect, validation-passing assets, and the
spec → `theme.json` mapping is mechanical. So the loop becomes:

```
describe in plain language  →  agent generates art + sounds + theme.json  →  agentisland theme add  →  see it  →  refine by prompting
```

## Quickstart (do it yourself)

```sh
# 1. Generate sounds for a theme folder
python3 synth.py ../themes/mytheme/sounds

# 2. Edit art.py's sprite maps / scene, then generate sheets + banners
#    (art.py writes into its OUT folder — point it at your theme's sprites/ + images/)
python3 art.py

# 3. Preview tiny art at 3×
python3 zoom.py ../themes/mytheme/_preview.png /tmp/preview.png 3 && open /tmp/preview.png

# 4. Write theme.json (see SPEC.md / the agent playbook), then validate + install
agentisland theme add ../themes/mytheme
```

## Quickstart (with an agent)

Open Claude Code in this repo and say, e.g.:

> "Read `framework/AGENTS.md` and `framework/SPEC.md`. Build me a theme spec'd like this: <your
> description>. Generate it, install it, and show me a preview."

The agent reads the playbook, drafts a spec, generates the assets with these tools, writes a valid
`theme.json`, runs `agentisland theme add`, and iterates with you.

## Constraints the tools already respect

- **Sprite sheets** are a single horizontal strip of `frameCount` cells, each `frameWidth × frameHeight`
  px, exported 1× — exactly what agent-island's slicer expects. `art.py` authors at 2× the point size
  so it stays crisp on Retina.
- **Sounds** are WAV PCM (NSSound can't decode FLAC/MP3). `synth.py` emits 44.1 kHz mono 16-bit.
- **No copyrighted assets.** Everything generated here is original — safe to publish.
