# Guidelines

Conventions applied by review and ratchet rather than by hook. They encode
the taste the four source projects converged on — a taste for evidence,
longevity and readability by the next contributor, human or artificial.

## 1. Naming

The principle, after Parasite Eve's CONVENTIONS and Rage Racer's
`docs/names.md`: **only PsyQ names are original.** Sony SDK functions keep
their exact SDK spellings; every other name is a project name chosen by
responsibility, and may be improved as understanding improves. Names describe
what code *does for the game*, not how it does it and not where it was
found. Types, sizes and identified addresses are never encoded into names.
Placeholder names are migration state, not a style — their counts are
ratcheted so they only go down. Record the *evidence* for every name (Rage
Racer keeps a dedicated document) so naming claims are auditable after the
people who made them are gone.

| Kind | Form | Example |
| --- | --- | --- |
| Game function | `Prefix_VerbObject`, PascalCase after a subsystem prefix | `Scene_LoadRoom`, `Inv_InsertItem` |
| PsyQ function | exact SDK spelling | `SpuSetReverb`, `CdControl` |
| Unknown function | `func_XXXXXXXX` (address, upper-case hex) | `func_80192F9C` |
| Global variable | `g_PascalCase` | `g_GameState` |
| Unknown global | `D_XXXXXXXX` | `D_800966EC` |
| File-local data / function | `s_PascalCase` data; `Prefix_Name` functions | `sTitleTimPath` |
| Type (struct, typedef) | PascalCase, no `_t` suffix | `GameState`, `FieldActor` |
| Enum constant / #define | `UPPER_SNAKE` with a subsystem prefix | `INV_CMD_GET_REMAINING_AMMO` |
| Header / C file | named after the *responsibility* of the unit, not its first function | `menu_widget.h` |

## 2. Code organisation and translation units

The repository is a long-lived reconstruction of the original program, not a
collection of independent decompilation puzzles. Directories map to
subsystems with one responsibility and one function prefix each; overlays
live in their own directory per binary; a shared library linked into many
overlays is stored once and listed by each overlay's manifest.

Headers follow a strict ownership rule: **one owner per declaration**, in the
narrowest appropriate header; no per-function headers; no new file-scope
`extern` declarations in C files. Moving a declaration preserves its exact
width, signedness and prototype — centralising is not an invitation to fix
an uncertain ABI.

Translation-unit boundaries are claims about the original source, governed
by an evidence order, strongest first:

1. executable addresses, section layout, relocations, manifest order;
2. known object or archive boundaries;
3. shared data, call relationships, static state;
4. responsibility;
5. existing filenames — **hints, not evidence**.

A merge or split is accepted only when addresses and manifest order survive,
the unit is contiguous (unless object evidence proves otherwise), ownership
is clear, and a clean rebuild stays byte-identical. Large cohesive units are
acceptable; function count and aesthetics alone never justify inventing
boundaries.

## 3. Shiftability

A matching build proves the bytes; **shiftability** proves the source does
not depend on where those bytes sit. It is a first-class goal (Tenchu
maintains a second build lane that relinks through ordinary GNU `ld` with
full relocation support; Parasite Eve runs a shift test that relinks with
padding inserted and classifies every word that did not move).

The practical rules:

* refer to code and data by symbol;
* never write a program address in C — no casts of integers to pointers, no
  tables of addresses typed as integers;
* fixed addresses only for hardware registers, the scratchpad and the loader
  contract, each behind a named macro;
* data the program owns is defined in a translation unit and placed by the
  linker.

The payoff: modding, porting and research builds that relink rather than
patch. LSD itself spawned a host port from the same C.

## 4. Documentation and knowledge management

Documentation is engineered against the same failure mode as everything
else: **staleness**.

* The rules file (this template's `CLAUDE.md`) stays short: rules and the
  loop, never project state or counts. A number written in prose is right
  for one session and wrong for every one after; state lives in tools that
  measure the tree (`make progress`, `make ratchets`).
* Durable lessons go into a cookbook-style doc with the evidence attached.
  Every rule is a hypothesis that has been paid for at least once; when a
  rule and a measurement disagree, the measurement wins and the rule gets
  fixed.
* Comments explain *why*: what the code is for in the game, which evidence
  fixes a boundary, why an odd construct exists for the match — never
  narration, history or scores, which belong in commit messages.
* Process history is archived, not deleted: LSD keeps round logs and
  per-function reports on an `archive/process` branch; Tenchu moves
  superseded investigation logs out of source files verbatim so the code
  reads like source.

## 5. AI-assisted decompilation

Two of the four projects were driven end to end by AI agents (LSD: 1,446/1,446
functions in 106 rounds / ~6,800 commits; Tenchu: one matcher agent per
function in isolated worktrees). Their patterns generalise:

**Foundations**

* The oracle is what makes agents viable: an agent cannot talk its way past
  a SHA1. Every claim is verified by the build, and hooks block the obvious
  escape routes (editing hash files, editing generated code, bypassing the
  verify script).
* Measure, don't transcribe. State lives in tools; a wrong score gets
  corrected the next time anyone measures, but a wrong *diagnosis* is what
  the next round acts on. Wrong diagnoses stood for many rounds before a
  screen caught them.
* Rules grow with the agents: each round writes down what the last one got
  wrong, then the corpus is distilled repeatedly. Discipline does not
  constrain agents — it is what makes them fast.

**Orchestration patterns**

* One function (or one tight family) per agent, in an isolated `git
  worktree`; prompts generated by tooling so facts, twins and guidance stay
  current.
* The orchestrator reviews, **harvests on green**, and folds newly learned
  rules back into the shared cookbook; a reflection pass builds a tool
  whenever friction recurs.
* Model tiering: cheaper models on mechanical work, stronger models on
  matching and naming, the strongest revising the plan between rounds. Track
  economics well enough to know which function classes cost twice as much
  for half the yield — and defer them.
