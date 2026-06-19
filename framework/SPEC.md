# Theme spec format

A **theme spec** is a short, human-written brief that describes the theme you want. An agent (or you)
turns it into a real agent-island data theme: original sprites, chiptune sounds, and a valid
`theme.json`. Copy this template, fill it in plain language, and hand it to the agent playbook
([`AGENTS.md`](AGENTS.md)). Nothing here needs to be precise — the agent refines it with you.

agent-island has six **canonical states** a theme renders an indicator for; describe each:

| State | When it shows |
|-------|---------------|
| `idle` | no active session |
| `working` | the agent is running (the main animation) |
| `waitingPermission` | blocked on a permission/approval prompt — your move |
| `waitingTurnEnd` | the agent finished its turn and is idling for your reply |
| `finished` | the session ended successfully |
| `failed` | the session ended in error |

There are four **sound cues** (edge-triggered, quiet + no-overlap): `start` (enters working),
`waiting` (enters either waiting state), `success` (finished), `fail` (failed).

---

## Template

```markdown
# Theme: <Display Name>

- **id**: <lowercase-id>            # also the folder name
- **vibe**: <one-line aesthetic, e.g. "NES platformer level", "cozy terminal", "space shooter">
- **layout**: <"banner" (wide, own row) | "inline" (small glyph beside the title)>
- **palette**: <key colours, e.g. sky #5C94FC, ground tan, accent red>

## States
- **working**: <what the main animation shows / does>
- **waitingPermission**: <visual>
- **waitingTurnEnd**: <visual>
- **finished**: <visual>
- **failed**: <visual>
- **idle**: <visual>

## Sounds
- **start / waiting / success / fail**: <describe the feel, e.g. "coin blip", "victory arpeggio">
  (synthesized chiptune by default; or list your own WAV files)

## Token bands (optional — requires agent-island 0.4.0+)
Describe how the theme should change as token usage climbs. Give ordered tiers with thresholds and
what each looks like. Example:
- rookie (< 50k): <base look>
- super (< 100k): <powered-up look>
- fire (< 200k): <look>
- star (≥ 200k): <look>
Which state(s) change per band? (usually `working`.)
```

---

## Notes the agent will apply for you

- **Original assets only.** Sprites are drawn procedurally (original art); sounds are synthesized.
  No copyrighted game art/audio gets generated or shipped.
- **Banner sizing.** A `banner` layout renders ~288×40 pt on its own row (like the built-in Road Trip
  / the Mario theme); `inline` is a small ~28 pt glyph beside the title.
- **Token bands map to `visualBands`.** Each tier becomes a per-band sprite sheet; `minAppVersion`
  is set to `0.4.0`. A theme with no token bands works on any agent-island version.
- **Validation is the gate.** The agent always finishes by running `agentisland theme add` — if the
  manifest or any asset is off, that rejects it with a precise reason, and the agent fixes it.

See [`examples/spec-mario.md`](examples/spec-mario.md) for a complete, worked spec.
