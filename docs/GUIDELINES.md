# Guidelines

Code reviews and ratchets enforce these guidelines. The guidelines keep the code clean, durable, and easy to read.

## 1. Naming

Only PsyQ names are original. Keep original SDK names for Sony SDK functions.

Create project names based on subsystem responsibility for all other code. Update names as you learn more about the program. Names describe what code does in the game. Do not encode types, sizes, or addresses into names.

Placeholder names are temporary. Ratchet placeholder counts so they only decrease. Record evidence for each name so other contributors can verify choices.

| Kind | Form | Example |
| --- | --- | --- |
| Game function | `Prefix_VerbObject`, PascalCase after a subsystem prefix | `Scene_LoadRoom`, `Inv_InsertItem` |
| PsyQ function | Exact SDK spelling | `SpuSetReverb`, `CdControl` |
| Unknown function | `func_XXXXXXXX` (address, upper-case hex) | `func_80192F9C` |
| Global variable | `g_PascalCase` | `g_GameState` |
| Unknown global | `D_XXXXXXXX` | `D_800966EC` |
| File-local data / function | `s_PascalCase` data; `Prefix_Name` functions | `sTitleTimPath` |
| Type (struct, typedef) | PascalCase, no `_t` suffix | `GameState`, `FieldActor` |
| Enum constant / #define | `UPPER_SNAKE` with a subsystem prefix | `INV_CMD_GET_REMAINING_AMMO` |
| Header / C file | Named after unit responsibility, not its first function | `menu_widget.h` |

## 2. Code organization and translation units

This repository reconstructs the original program. Directories map to subsystems. Each subsystem has one responsibility and one function prefix. Overlays reside in separate directories for each binary. Store shared library code once, and list it in each overlay manifest.

Headers follow strict ownership. Place each declaration in the narrowest header that fits. Do not write per-function headers. Do not add file-scope `extern` declarations in C files. When you move a declaration, keep its exact width, signedness, and prototype.

Translation-unit boundaries reflect the original source structure. Use this evidence order:

1. Executable addresses, section layout, relocations, and manifest order
2. Known object or archive boundaries
3. Shared data, call relationships, and static state
4. Subsystem responsibility
5. Existing filenames (hints only, not proof)

Accept a boundary change only when addresses and manifest order remain intact. The unit must remain contiguous. The rebuild must match the retail binary. Do not split files based on function count alone.

## 3. Shiftability

A matching build proves byte equality. Shiftability proves that source code does not depend on fixed memory locations.

Follow these rules:

* Reference code and data by symbol name.
* Do not write numeric memory addresses in C code.
* Do not cast integers to pointers.
* Do not store address tables as integers.
* Use macros for hardware registers, scratchpad memory, and loader vectors.
* Place game data inside translation units so the linker positions it.

Shiftable code supports ports, modifications, and relocation.

## 4. Documentation and knowledge management

Keep documentation accurate:

* Keep `AGENTS.md` short. Focus on rules and the loop. Do not put project status numbers in text. Use tools to measure state (`make progress`, `make ratchets`).
* Record durable lessons in reference documents with supporting evidence.
* Comments explain intent. Explain what the code does, why an unusual construct matches, or what evidence sets a boundary.
* Do not write narration, change history, or progress counts in comments. Record history in commit messages.

## 5. AI-assisted decompilation

Use these patterns for AI workflows:

**Foundations**

* The hash oracle prevents false progress. Every change must pass `make verify`. Hooks block edits to hashes, generated files, and verification scripts.
* Measure progress with tools instead of writing numbers in prose.
* Update rules when an agent makes an error.

**Orchestration patterns**

* Assign one function or tight family to each agent in a separate git worktree. Generate prompts with target assembly and sibling code.
* Review and merge code only on green builds.
* Use smaller models for mechanical work. Use larger models for matching, naming, and task planning.
