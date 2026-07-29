# FreeCAD Local Build — blw-fixes-v7

Branch: `blw-fixes-v7`
Base: `weekly-2026.07.29` (commit `63af5cb2f3`)
Version: `26.3.0-dev` (upstream renumbered from `1.2` to calendar-based `26.3` between 06.10 and 06.24; the dev series jumped 1.1 → 26.3, skipping 1.2)

## Build

```bash
cd FC-clone && pixi run build-release
```

## Run

```bash
cd FC-clone && pixi run freecad-release
```

## Updating the Base (rebasing onto a newer weekly)

A "rebase" here means **two steps**, not one. Rebasing only the superproject
leaves the submodule working trees pinned at whatever was last checked out —
this is how OndselSolver silently sat at an Oct-2025 commit for six months
while the committed pointer moved ahead. Always:

```bash
git fetch origin --tags
git rebase weekly-YYYY.MM.DD            # moves the committed submodule pointers
git submodule update --init --recursive # syncs the on-disk submodules to match
```

`submodule.recurse=true` is set locally (`git config submodule.recurse true`)
so checkout/rebase/pull/switch auto-sync submodules going forward — the second
line is belt-and-suspenders. Submodules: `src/3rdParty/OndselSolver` (assembly
dynamics — the one that moves), `src/3rdParty/GSL`, `src/Mod/AddonManager`,
`src/3rdParty/coin`, `src/3rdParty/pivy` (added between 07.01 and 07.15 —
upstream now bundles and builds Coin3D/Pivy from source via `SetupCoinPivy()`
instead of pulling `coin3d`/`pivy` from pixi/conda-forge; `pixi.toml` dropped
those two deps and added `expat`, `libopengl-devel`, `mesa-libglu-devel`. First
build after this point compiles Coin3D+Pivy from source — expect a
meaningfully longer build than prior weeklies).

After updating, sanity-check `version.json` and the base line above, then
`pixi run build-release`. If you hit stale-solver link errors, a submodule
pointer changed and CMake needs a reconfigure.

**Version-renumber note:** the on-disk user-data dir is version-stamped
(`v{major}-{minor}`), so it moved from `v1-2` to `v26-3`. First launch of a
26.x build shows FreeCAD's `DlgVersionMigrator`, offering to Copy / Share /
start Fresh from the old `v1-2` config (prefs + installed addons + macros).

## Local Patches

Minimal personal-use patch set. Not intended for upstream contribution.

| # | Commit | File(s) | Why we have it | Drop when |
|---|--------|---------|----------------|-----------|
| 3 | `e53a4d6359` | `Gui/MainWindow.cpp/h`, `Gui/OperationCancel.h`, `Part/Gui/TaskCheckGeometry.cpp/h` | Add `Ctrl+.` cancel for Check Geometry long-running operations. Introduces `Gui::OperationCancel` atomic flag. | Merged upstream |
| 4 | `a79b37a651` | `Base/OperationCancel.h`, `Gui/ApplicationPy.cpp/h`, `Part/App/TopoShape.cpp`, `TopoShapeExpansion.cpp`, `ThicknessProgressIndicator.h` | Make Thickness (`BRepOffsetAPI_MakeThickSolid`) cancellable via `Ctrl+.` and MCP `cancel_operation`. Moves cancel flag to `Base/` so App-layer code can check it. | Merged upstream |
| 5 | `88967893cd` | `Part/App/ProgressIndicator.cpp` | Wire `Base::OperationCancel::isSet()` into `Part::ProgressIndicator::UserBreak()` so Ctrl+. and `Gui.cancelOperation()` cancel booleans, sweeps, and all other operations routed through `Part::ProgressIndicator`. | Merged upstream |
| 8 | `b7c10850f8` | `Gui/CommandLink.cpp` | Make Link: honor cross-document selections. Since upstream commit `3076ce66be`, `getCompleteSelection()` only returns the active document's selection, breaking the classic "select in doc A, switch to doc B, click Make Link" workflow. Iterates all open docs instead. Upstream issue #28681. | Upstream fixes #28681 |
| 16 | `39a5a9dd19` | `Gui/Stylesheets/defaults.qss` | Increase Text Document editor font to 14pt for HiDPI displays. Scoped to `Gui::TextDocumentEditorView` only. | Never (personal preference) |
