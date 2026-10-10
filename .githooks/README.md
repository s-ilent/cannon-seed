# Git hooks

Installed with:

```sh
make hooks        # = git config core.hooksPath .githooks
```

They exist because someone — usually an agent under deadline pressure —
broke each rule once and the tree suffered. Enforcement is mechanical so
that it never depends on a reviewer catching it.

| hook check | protects | rule |
| --- | --- | --- |
| blocks edits to `config/sha1/**` | the retail hash, i.e. the oracle | "Never edit the hash files" (LSD rule 1) |
| blocks modifications/deletions under `asm/` (additions allowed) | generated disassembly | "Never edit `asm/`, splat regenerates it" (LSD rule 4) |
| blocks commits under `disk/`, `sdk/`, `lib/`, `include/psyq/`, `assets/`, `baselines/` | the source-only policy | "Never commit anything of Sony's or the game's" (LSD rule 3) |

The hooks guard the obvious escape routes; they are not a security
boundary. `--no-verify` exists for the one legitimate case (recording your
retail hash at setup) and for deliberate policy changes, which should be
rare and reviewed.

What the hooks do NOT check — the reviewer's job:

* commits happen only on green (`make verify` — the whole-image SHA-1);
* every change states which claim it makes (binary match, semantic
  recovery, typing, naming, organization) — see CONTRIBUTING.md;
* ratchet baselines equal the current tree (`make ratchets`).
