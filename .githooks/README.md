# Git hooks

Install the hooks with this command:

```sh
make hooks        # = git config core.hooksPath .githooks
```

These hooks protect the repository against broken commits. Contributors broke each rule in past work. Mechanical checks prevent these errors.

| hook check | protects | rule |
| --- | --- | --- |
| blocks edits to `config/sha1/**` | retail hash oracle | "Never edit the hash files" (LSD rule 1) |
| blocks edits to `asm/` (additions allowed) | generated disassembly | "Never edit `asm/`, splat regenerates it" (LSD rule 4) |
| blocks commits to `disk/`, `sdk/`, `lib/`, `include/psyq/`, `assets/`, `baselines/` | source-only policy | "Never commit anything of Sony's or the game's" (LSD rule 3) |

The hooks block common errors. They do not supply a full security boundary.

Use `--no-verify` only when you record the initial retail hash. Also use it for approved policy changes.

Reviewers must check these items manually:

* Commits occur only after `make verify` succeeds.
* Each commit declares its claim in the commit message.
* Ratchet baselines match the current tree (`make ratchets`).
