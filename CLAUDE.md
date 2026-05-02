# FreeCAD Local Build — blw-fixes-v5

Branch: `blw-fixes-v5`
Base: `weekly-2026.04.29` (commit `a785d40ac4`)

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
| 3 | `25b7718835` | `Gui/MainWindow.cpp/h`, `Gui/OperationCancel.h`, `Part/Gui/TaskCheckGeometry.cpp/h` | Add `Ctrl+.` cancel for Check Geometry long-running operations. Introduces `Gui::OperationCancel` atomic flag. | Merged upstream |
| 4 | `fe7a8ed869` | `Base/OperationCancel.h`, `Gui/ApplicationPy.cpp/h`, `Part/App/TopoShape.cpp`, `TopoShapeExpansion.cpp`, `ThicknessProgressIndicator.h` | Make Thickness (`BRepOffsetAPI_MakeThickSolid`) cancellable via `Ctrl+.` and MCP `cancel_operation`. Moves cancel flag to `Base/` so App-layer code can check it. | Merged upstream |
| 5 | `8a10439d1b` | `Part/App/ProgressIndicator.cpp` | Wire `Base::OperationCancel::isSet()` into `Part::ProgressIndicator::UserBreak()` so Ctrl+. and `Gui.cancelOperation()` cancel booleans, sweeps, and all other operations routed through `Part::ProgressIndicator`. (`Base::ProgressIndicator` was removed upstream in `ef1d1749a9`; previously targeted `Base/ProgressIndicator.h`.) | Merged upstream |
| 6 | `471333dc2c` | `Sketcher/App/SketchObjectExternal.cpp` | Decode opaque TNP hash refs (e.g. `Fusion010.;#61cd:4;:H1137,E`) into human-readable messages in Report View. Adds `decodeExternalRef()` and `sketchGeoTypeName()`. Applied to `rebuildExternalGeometry()` and `fixExternalGeomReference()`. Upstream issue #27760. | Merged upstream |
| 7 | `0af791f015` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartFuse.cpp` | Pre-flight solid checks before boolean operations — adds `containsSolid()` and `shapeTypeName()` helpers, rejects non-solid inputs with clear error. | Merged upstream (see patch 8 for the user-facing message work) |
| 8 | `959fc275b9` | `Gui/CommandLink.cpp` | Make Link: honor cross-document selections. Since upstream commit `3076ce66be`, `getCompleteSelection()` only returns the active document's selection, breaking the classic "select in doc A, switch to doc B, click Make Link" workflow. Iterates all open docs instead. Upstream issue #28681. | Upstream fixes #28681 |
| 9 | `c40070ffe0` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartCommon.cpp`, `FeaturePartFuse.cpp`, `Part/Gui/DlgSettingsGeneral.ui` | Detect and warn when Refine introduces self-intersections. Adds `refineResultIsValid()` helper using `BOPAlgo_ArgumentAnalyzer`, skips the refine result and logs a console warning if the validator trips. Introduces `CheckRefine` preference. Part of PR #29134. | PR #29134 merged upstream |
| 10 | `a4c9e6142c` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartCommon.cpp`, `FeaturePartFuse.cpp` | Improve boolean and refine failure messages for non-expert users — multi-line error strings with troubleshooting steps. Part of PR #29134. | PR #29134 merged upstream |
| 11 | `fb106dd2fe` | `Part/App/FeaturePartBoolean.cpp/h`, `FeaturePartCommon.cpp/h`, `FeaturePartFuse.cpp/h` | Make `CheckRefine` a per-feature property seeded from preferences (reviewer request on PR #29134). Adds `getCheckRefineParameter()`; `refineResultIsValid` now takes a `bool`. Part of PR #29134. | PR #29134 merged upstream |
| 12 | `79bc14a1ab` | `Part/App/RefinableFeature.cpp/h`, `Part/App/FeaturePartBoolean.*`, `FeaturePartCommon.*`, `FeaturePartFuse.*`, `CMakeLists.txt` | Introduce `Part::RefinableFeature` base class owning `Refine`, `CheckRefine`, `isRefineResultValid()`, `applyRefine()`. Cleans up duplicated refine logic across boolean feature classes. Part of PR #29134. | PR #29134 merged upstream |
| 13 | `edc4769149` | `Part/App/AppPart.cpp` | Register `Part::RefinableFeature::init()` in module init — without it, `PROPERTY_SOURCE(…, Part::RefinableFeature)` would silently fail type registration. Part of PR #29134. | PR #29134 merged upstream |
| 14 | `2decf4ede2` | `Part/App/FeaturePartCommon.cpp`, `FeaturePartFuse.cpp` | Fix double error logging in `MultiFuse`/`MultiCommon` `execute()` — throw `Base::RuntimeError` instead of returning `DocumentObjectExecReturn` so the error surfaces once, not twice. | Merged upstream |
| 15 | `2897d3b0f8` | `Part/App/FeaturePartBoolean.cpp`, `FeaturePartFuse.cpp` | Remove pop-up warning on non-solid boolean input (report-view log is enough); shorten MultiFusion error message per FEA-eng reviewer feedback. | Merged upstream |
| 16 | `7ed1d1a8e1` | `Gui/Stylesheets/defaults.qss` | Increase Text Document editor font to 14pt for HiDPI displays. Scoped to `Gui::TextDocumentEditorView` only. | Never (personal preference) |
| 17 | `d731fdbae7` | `Part/parttests/BooleanFeatureTest.py`, `run_boolean_smoke_test.py`, `TestPartApp.py` | Headless smoke tests for boolean feature classes. Catch silent registration failures (missing `init()` in `AppPart.cpp`). | Never (infrastructure) |
| 18 | `e97ec9306e` | `.github/workflows/blw_ci.yml` | GitHub Actions workflow for our fork — runs `run_boolean_smoke_test.py` on push to `blw-fixes-*` and `part-*` branches. | Never (fork-specific CI) |
| 19 | `0cea605543` | `Part/App/FeaturePartFuse.cpp`, `Part/parttests/BooleanFeatureTest.py` | Replace the static `"Not enough shape objects linked"` throw in `MultiFuse::execute()` with three actionable branches: empty `Shapes` list, single non-compound input (names the offending object), and single compound with <2 children (reports child count). Adds two smoke tests for the empty and single-input paths. | Merged upstream |
| 20 | `e77f70903d` | `Sketcher/App/SketchObjectExternal.cpp` | Extend missing-external-geometry error messages: include sketch Label + full name, list orphaned constraints by type/index, and resolve referenced-object label when the object still exists. Builds on patch 6 (`decodeExternalRef`/`sketchGeoTypeName`). | Merged upstream |
| 21 | `94853496db` | `Sketcher/SketcherTests/TestSketcherSolver.py` | Regression test (`testMissingExternalGeometryReferenceAfterDelete`) for the `rebuildExternalGeometry()` missing-reference path. Uses correct `BUILD_PART_DESIGN` guard; two pre-existing tests use `BUILD_PARTDESIGN` (silently no-ops). | Merged upstream |
| 22 | `f90c4012d7` | `Sketcher/SketcherTests/TestSketcherSolver.py` | Two more regression tests around `rebuildExternalGeometry()`: `testMissingExternalGeometryReferenceWithConstraint` (covers the `usedBy` append path with a `PointOnObject` on an external edge that goes missing; note Edge1 projects to a Point so Edge4 is used) and `testMissingExternalGeometriesMultiple` (verifies `geoIdx` tracking with 3 refs to the same Pad — `addExternal` calls group in `ExternalGeometry` but remain distinct in internal `ExternalGeo`). | Merged upstream |
| 23 | `07a1477043` | `Sketcher/App/SketchObjectExternal.cpp` | Add `sketchDiagName()` helper, apply to all 8 `FC_ERR`/`FC_WARN` diagnostics in the file for consistent `sketch "Label" (Doc#Name)` framing (falls back to `sketch Doc#Name` when Label equals internal name). | Merged upstream |
| 24 | `2ccc7106b2` | `Sketcher/SketcherTests/TestSketcherSolver.py`, `TestSketchValidateCoincidents.py` | Fix `BUILD_PARTDESIGN` → `BUILD_PART_DESIGN` typo gating six previously-silent tests. `testRemovedExternalGeometryReference` fails once actually run (expects ExternalGeometry pruned when sub-element disappears while parent persists — needs investigation); left on old flag with a tracking NOTE. | Merged upstream |
| 25 | `49853bbfb1` | `Sketcher/SketcherTests/TestSketcherSolver.py` | Fix `testRemovedExternalGeometryReference` assertion (`== 0` → `== 1`). Investigation: TNP retargets the thread edge reference to a surviving Hole edge (Edge29 → Edge17, no Missing flag) — not an orphan. The `== 0` assertion was introduced in Dec 2024 (`e09e107778`) alongside a Hole refine fix, silently wrong, and hidden by the typo gate added in May 2025. Also promote the gate to an early `skipTest` so the test reports skipped rather than silently passing. | Merged upstream |
| 26 | `a98247b622` | `Part/parttests/BooleanFeatureTest.py` | Smoke tests for the pre-flight solid checks added in patch 7 (`containsSolid()`/`shapeTypeName()`): three cases covering `Part::Fuse` Base + Tool and `Part::MultiFuse` rejection of Shell inputs. Confirms the rejection log message appears as expected. | Never (test coverage for patch 7) |
| 27 | `220d39895d` | `Sketcher/App/SketchObjectExternal.cpp`, `Sketcher/SketcherTests/TestSketcherSolver.py` | Lead missing-external-geometry `FC_ERR` lines with the Sketcher UI subname `ExternalEdge<N>` (matches Elements panel row and 3D selection string) instead of the internal `e<id>`, which has no UI surface. Mapping `ExternalGeo[i] → ExternalEdge<i-1>` for `i ≥ 2`. Applied to the 4 FC_ERR sites that identify a specific slot (rebuild + fix paths). Builds on patches 6/20/23. Adds a `_CaptureStderr` helper (fd-2 redirect, ANSI strip) enabling log-format regression tests; extends the two existing missing-external tests and adds `testMissingExternalGeometryLogFormatForMultipleEntries` pinning the contiguous-numbering invariant. | Merged upstream |

## PR #29134 status

Patches 9–13 (and portions of 14, 15) constitute the open upstream PR #29134
(`RefinableFeature` refactor + refine self-intersection detection + nicer
error messages). Those will all go away when #29134 merges — watch the PR
and collapse the manifest when it lands.

Patches 8 (Make Link) and 16–18 are expected to stay on the fork.

## Withdrawn patches

Patch 1 (`a0954db1ce`, demote duplicate element-mapping warn to TRACE) was
reverted on 2026-04-23 (commit `e556b28269`). Upstream commit `e39e36747c`
(Apr 19 2026, "App: trace resolved duplicate element mappings") supersedes
it more cleanly: removes the level-guard entirely and switches `FC_WARN` to
`FC_TRACE` directly. Picked up at the next weekly rebase.

Patch 2 (`c2843fc2dd`, `TopoShape::getElementTypeAndIndex` regex extension +
`PartDesign::Boolean` `bakeInTransform`) was reverted on 2026-04-23 (commit
`19f7134c4b`). Reasons:

- The TopoShape regex change re-introduced exactly the prefix-aware regex that
  upstream had tried in PR #25913 and reverted in PR #26596 (Jan 2026) due to
  regressions. Our re-introduction silently broke the existing upstream test
  `TestElementTypeWithSubelements` (which asserts `"Part.Body.Pad.Face3"`
  must NOT match). Nobody noticed because our smoke tests don't cover the
  C++ ctest suite.
- The `bakeInTransform()` call was previously documented in this file as
  "deliberately excluded — upstream reverted it (converts planar faces to
  BSplines, breaks Refine)", but the actual commit included it. Either a
  documentation error or a silent regression on planar-face refines.

If the original symptoms recur (originally cited issues #26119, #26327,
#26400), investigate them fresh per-issue with proper tests rather than
re-applying upstream-rejected changes.
