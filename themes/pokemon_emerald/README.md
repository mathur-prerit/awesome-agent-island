# Pokémon Emerald Ride — agent-island theme

A side-scrolling forest bike ride inspired by the Pokémon Emerald intro: a kid pedals a
mountain bike down a meadow route while a flying bug-type buzzes overhead and a fox-like critter
runs alongside. Parallax mountains, pine trees and grass scroll past, and the whole scene shifts
**day → golden hour → dusk → night** as a session burns tokens.

![preview](preview.png)

*(Top rows: the `working` animation at each token tier. Then waiting / turn-end / finished / error / idle.)*

## Install

> Requires **agent-island 0.4.0+** (token bands). Update with `agentisland update` if you're older.

```sh
agentisland theme add ./themes/pokemon_emerald
agentisland theme set pokemon_emerald
agentisland config set soundEnabled true   # optional: chiptune cues
```
Then relaunch agent-island and pick **Pokémon Emerald Ride** from the menu-bar **Animation theme** submenu.

## Day-to-night tiers (by token usage)

| Tokens | Tier | Look |
|--------|------|------|
| < 50k | day | bright blue sky, green meadow |
| < 100k | golden | warm golden-hour light |
| < 200k | dusk | purple-orange sky |
| ≥ 200k | night | moon, stars, fireflies |

The cyclist, the flyer and the runner are tinted to match each tier's lighting; mountains drift
slowest, trees mid, grass fastest, for a parallax depth effect.

## Sound cues

| Transition | Cue |
|------------|-----|
| starts working | route pickup |
| waiting on you | soft chime |
| finished OK | victory arpeggio |
| failed | low descent |

## How the art is built

The background (sky, parallax mountains, pine trees, grass) is drawn procedurally by
[`framework/art.py`](../../framework/art.py). The moving characters live in
[`framework/sources/pokemon_emerald/`](../../framework/sources/pokemon_emerald) as generated PNG
sprites; `art.py` strips their backgrounds, downscales them onto the pixel grid, and composites them
into every tier and banner. To re-render after swapping a sprite, run `python3 framework/art.py`.

## Disclaimer

Fan tribute, unaffiliated with and unendorsed by Nintendo / Game Freak. The character sprites
(`framework/sources/pokemon_emerald/`) were AI-generated for personal use and resemble third-party
creatures, so this theme is **not** intended for redistribution. The background art and chiptune
audio are original.
