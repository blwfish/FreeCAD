# FreeCAD Local Build — blw-fixes-v5

Branch: `blw-fixes-v5`
Base: `weekly-2026.04.15` (commit `d0dec51851`)

## Build

```bash
cd FC-clone && pixi run build-release
```

## Run

```bash
cd FC-clone && pixi run freecad-release
```

## Testing

### Headless smoke tests (no GUI needed)

Tests live in `src/Mod/Part/parttests/` — a standard Python `unittest` package that is also imported by `TestPartApp.py` so tests run under ctest.

**Run the boolean feature smoke tests:**
```bash
cd FC-clone && pixi run smoke-test-boolean
```

Runs headlessly via `FreeCADCmd` — no display, no GUI, won't interfere with a running FreeCAD instance in the other window.

**Run all Part module tests (slower, includes ctest suite):**
```bash
cd FC-clone && pixi run test-release
```

### When to add a test

Add a test in `parttests/` whenever:
- A new C++ feature class is added — verify registration, properties, basic `execute()`
- Class registration changes (`init()` calls in `AppPart.cpp` etc.) — silent failures here produce confusing geometry errors, not compile errors
- Property inheritance changes (new base class, extension, etc.)
- A bug is fixed that was previously undetected by compile-only checks

**Always run `smoke-test-boolean` before pushing a PR that touches Part boolean features.**

### Adding a new test file

1. Create `src/Mod/Part/parttests/MyFeatureTest.py` following the `BooleanFeatureTest.py` pattern:
   - `setUp` / `tearDown` open and close a fresh document
   - One `test_*` method per behaviour; keep them small and independent
2. Import it in `src/Mod/Part/TestPartApp.py`:
   ```python
   from parttests.MyFeatureTest import MyFeatureTests
   ```
3. If it needs its own quick runner, add a script in `parttests/` and a pixi task in `pixi.toml` (excluded from git via `git update-index --skip-worktree pixi.toml`).

### Key API notes

- `FreeCAD.Base.TypeId.fromName("Part::Foo").isBad()` — check type registration (`not isBad()` means registered)
- `doc.addObject("Part::Fuse", "name")` — create feature objects
- `doc.recompute()` — trigger `execute()` on dirty features
- `feature.Shape.isNull()` / `.Volume` — basic shape validity checks

## Local Patches

This branch carries the following patches on top of upstream. This list is
**authoritative** — before any rebase, verify every patch here is carried
forward. Add an entry for every new local patch; remove entries when a patch
is merged upstream or intentionally dropped.

Patches are listed in apply order (oldest first). The `[pre-commit.ci]`
formatting commits that sit between functional commits are not listed
individually — they are carried with their parent patch.

| # | Commit | File(s) | Why we have it | Drop when |
|---|--------|---------|----------------|-----------|
| 1 | `a0954db1ce` | `App/ElementMap.cpp` | Demote noisy duplicate-mapping warning from WARN to TRACE — spams the report view on large assemblies. | Merged upstream |
| 2 | `c2843fc2dd` | `Part/App/TopoShape.cpp`, `PartDesign/App/FeatureBoolean.cpp` | TopoShape: extend `getElementTypeAndIndex` regex to handle TNP hash/dot-notation prefixes. FeatureBoolean: trigger preview shape update on change. Note: `bakeInTransform()` deliberately excluded — upstream reverted it (converts planar faces to BSplines, breaks Refine). | Merged upstream |
| 3 | `ee4021d900` | `Gui/MainWindow.cpp/h`, `Gui/OperationCancel.h`, `Part/Gui/TaskCheckGeometry.cpp/h` | Add `Ctrl+.` cancel for Check Geometry long-running operations. Introduces `Gui::OperationCancel` atomic flag. | Merged upstream |
| 4 | `4e9af83359` | `Base/OperationCancel.h`, `Gui/ApplicationPy.cpp/h`, `Part/App/TopoShape.cpp`, `TopoShapeExpansion.cpp`, `ThicknessProgressIndicator.h` | Make Thickness (`BRepOffsetAPI_MakeThickSolid`) cancellable via `Ctrl+.` and MCP `cancel_operation`. Moves cancel flag to `Base/` so App-layer code can check it. | Merged upstream |
| 5 | `991353765a` | `Base/ProgressIndicator.h` | Wire `Base::OperationCancel::isSet()` into `ProgressIndicator::userBreak()` so any OCC operation that polls the progress indicator respects cancel. | Merged upstream |
| 6 | `75d4200b75` | `Sketcher/App/SketchObjectExternal.cpp` | Decode opaque TNP hash refs (e.g. `Fusion010.;#61cd:4;:H1137,E`) into human-readable messages in Report View. Adds `decodeExternalRef()` and `sketchGeoTypeName()`. Applied to `rebuildExternalGeometry()` and `fixExternalGeomReference()`. Upstream issue #27760. | Merged upstream |
| 7 | `b060fc1eb5` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartFuse.cpp` | Pre-flight solid checks before boolean operations — adds `containsSolid()` and `shapeTypeName()` helpers, rejects non-solid inputs with clear error. | Merged upstream (see patch 8 for the user-facing message work) |
| 8 | `d3fe6c0b2c` | `Gui/CommandLink.cpp` | Make Link: honor cross-document selections. Since upstream commit `3076ce66be`, `getCompleteSelection()` only returns the active document's selection, breaking the classic "select in doc A, switch to doc B, click Make Link" workflow. Iterates all open docs instead. Upstream issue #28681. | Upstream fixes #28681 |
| 9 | `00048c366a` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartCommon.cpp`, `FeaturePartFuse.cpp`, `Part/Gui/DlgSettingsGeneral.ui` | Detect and warn when Refine introduces self-intersections. Adds `refineResultIsValid()` helper using `BOPAlgo_ArgumentAnalyzer`, skips the refine result and logs a console warning if the validator trips. Introduces `CheckRefine` preference. Part of PR #29134. | PR #29134 merged upstream |
| 10 | `fc91875468` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartCommon.cpp`, `FeaturePartFuse.cpp` | Improve boolean and refine failure messages for non-expert users — multi-line error strings with troubleshooting steps. Part of PR #29134. | PR #29134 merged upstream |
| 11 | `795bed4b1a` | `Part/App/FeaturePartBoolean.cpp/h`, `FeaturePartCommon.cpp/h`, `FeaturePartFuse.cpp/h` | Make `CheckRefine` a per-feature property seeded from preferences (reviewer request on PR #29134). Adds `getCheckRefineParameter()`; `refineResultIsValid` now takes a `bool`. Part of PR #29134. | PR #29134 merged upstream |
| 12 | `d60cf6b93e` | `Part/App/RefinableFeature.cpp/h`, `Part/App/FeaturePartBoolean.*`, `FeaturePartCommon.*`, `FeaturePartFuse.*`, `CMakeLists.txt` | Introduce `Part::RefinableFeature` base class owning `Refine`, `CheckRefine`, `isRefineResultValid()`, `applyRefine()`. Cleans up duplicated refine logic across boolean feature classes. Part of PR #29134. | PR #29134 merged upstream |
| 13 | `fcdca90bd6` | `Part/App/AppPart.cpp` | Register `Part::RefinableFeature::init()` in module init — without it, `PROPERTY_SOURCE(…, Part::RefinableFeature)` would silently fail type registration. Part of PR #29134. | PR #29134 merged upstream |
| 14 | `c0e99d4dcb` | `Part/App/FeaturePartCommon.cpp`, `FeaturePartFuse.cpp` | Fix double error logging in `MultiFuse`/`MultiCommon` `execute()` — throw `Base::RuntimeError` instead of returning `DocumentObjectExecReturn` so the error surfaces once, not twice. | Merged upstream |
| 15 | `ed16dcbcfe` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartFuse.cpp` | Remove pop-up warning on non-solid boolean input (report-view log is enough); shorten MultiFusion error message per FEA-eng reviewer feedback. | Merged upstream |
| 16 | `641e9384d8` | `Gui/Stylesheets/defaults.qss` | Increase Text Document editor font to 14pt for HiDPI displays. Scoped to `Gui::TextDocumentEditorView` only. | Never (personal preference) |
| 17 | `bc6fcff4ba` | `Part/parttests/BooleanFeatureTest.py`, `run_boolean_smoke_test.py`, `TestPartApp.py` | Headless smoke tests for boolean feature classes. Catch silent registration failures (missing `init()` in `AppPart.cpp`). | Never (infrastructure) |
| 18 | `4ac3d86023` | `.github/workflows/blw_ci.yml` | GitHub Actions workflow for our fork — runs `run_boolean_smoke_test.py` on push to `blw-fixes-*` and `part-*` branches. | Never (fork-specific CI) |
| 19 | `1d312a9903` | `Part/App/FeaturePartFuse.cpp`, `Part/parttests/BooleanFeatureTest.py` | Replace the static `"Not enough shape objects linked"` throw in `MultiFuse::execute()` with three actionable branches: empty `Shapes` list, single non-compound input (names the offending object), and single compound with <2 children (reports child count). Adds two smoke tests for the empty and single-input paths. | Merged upstream |
| 20 | `b36ce8c734` | `Sketcher/App/SketchObjectExternal.cpp` | Extend missing-external-geometry error messages: include sketch Label + full name, list orphaned constraints by type/index, and resolve referenced-object label when the object still exists. Builds on patch 6 (`decodeExternalRef`/`sketchGeoTypeName`). | Merged upstream |
| 21 | `d8a8ba1964` | `Sketcher/SketcherTests/TestSketcherSolver.py` | Regression test (`testMissingExternalGeometryReferenceAfterDelete`) for the `rebuildExternalGeometry()` missing-reference path. Uses correct `BUILD_PART_DESIGN` guard; two pre-existing tests use `BUILD_PARTDESIGN` (silently no-ops). | Merged upstream |

## PR #29134 status

Patches 9–13 (and portions of 14, 15) constitute the open upstream PR #29134
(`RefinableFeature` refactor + refine self-intersection detection + nicer
error messages). Those will all go away when #29134 merges — watch the PR
and collapse the manifest when it lands.

Patches 8 (Make Link) and 16–18 are expected to stay on the fork.
