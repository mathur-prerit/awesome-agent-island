# Super Mario — agent-island theme

A scrolling NES-style platformer level for your menu-bar island that **powers up with your token
usage**. Original pixel art + synthesized chiptune — no Nintendo assets.

![preview](preview.png)

*(Top rows: the `working` animation at each token tier. Then waiting / turn-end / finished / game-over.)*

## Install

> Requires **agent-island 0.4.0+** (token bands). Update with `agentisland update` if you're older.

```sh
agentisland theme add https://raw.githubusercontent.com/mathur-prerit/awesome-agent-island/main/themes/mario.zip
agentisland theme set mario
agentisland config set soundEnabled true   # optional: chiptune cues
```
Then relaunch agent-island and pick **Super Mario** from the menu-bar **Animation theme** submenu.

## Powerup tiers (by token usage)

| Tokens | Tier | Look |
|--------|------|------|
| < 50k | rookie | small classic Mario |
| < 100k | super | powered-up + sparkles |
| < 200k | fire | white overalls + fireball, more coins |
| ≥ 200k | star | flashing invincible colours + sparkles, most coins |

Mario runs, **hops the pipe and the goomba**, a mushroom sprouts, coins scroll by — and as a session
burns more tokens he climbs tiers automatically.

## Sound cues

| Transition | Cue |
|------------|-----|
| starts working | coin blip |
| waiting on you | pause beep |
| finished OK | victory arpeggio |
| failed | game-over tune |

## Built with the framework

This theme was generated from [`framework/examples/spec-mario.md`](../../framework/examples/spec-mario.md)
using the [authoring framework](../../framework) (`art.py` for the original sprites, `synth.py` for the
chiptune). Fork the spec to make your own.

## Disclaimer

A fan tribute. All art is original (procedurally drawn, not traced) and all audio is synthesized — no
Nintendo assets are included. Mario is a trademark of Nintendo; this theme is unaffiliated with and
unendorsed by Nintendo.
