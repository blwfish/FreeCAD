# FreeCAD Source Build

Fork of FreeCAD with local bug fixes.

## Build Commands (pixi)

```bash
pixi run configure-release   # Configure cmake
pixi run build-release       # Build
pixi run install-release     # Install to .pixi env
pixi run freecad-release     # Run FreeCAD
```

For debug builds, replace `-release` with `-debug`.

## Branches

- **`main`** — Tracks upstream `FreeCAD/FreeCAD` main (currently at `weekly-2026.03.11`)
- **`blw-fixes-v3`** — Current local fixes (9 patches, rebased on `weekly-2026.03.11`)
- **`blw-fixes-v2`** — Old branch with 7 patches (preserved for reference, based on `weekly-2026.02.18`)
- **`blw-fixes`** — Original local fixes (preserved for reference, based on older main)

## Local Fixes (blw-fixes-v3)

Nine patches on top of upstream main:

1. **TopoShape.cpp** — Fix `getElementTypeAndIndex` regex to handle TNP hash and dot notation prefixes (e.g. `Part.Face3`, `;#7:1;:G0...F.Face3`). Removes `Data::oldElementName()` call and uses a single regex with optional prefix group. The critical "fuzzy matching" fix.
2. **PartDesign/FeatureBoolean.cpp** — Add `bakeInTransform()` before refine, and `updatePreviewShape()` call in `onChanged`.
3. **MeshPart/AppMeshPartPy.cpp + Mesher.cpp** — Fix crash when BRepMesh throws in keyword method dispatch.
4. **ElementMap.cpp** — Demote duplicate element mapping warning from LOG to TRACE level (was flooding console during normal toponaming).
5. **Sketcher/SketchObject.cpp** — Decode TNP element refs in "missing reference" error messages. Before: `missing reference: Fusion010.;#61cd:4;:H1137,E`. After: `missing reference to Edge in 'Fusion010'`.
6. **Sketcher/SketchObject.cpp** — Improve all external geometry reference error messages.
7. **Gui/OperationCancel.h + MainWindow + Part/Gui/TaskCheckGeometry** — Reliable cancel for Check Geometry long-running operations. `Ctrl+.` shortcut sets global cancel flag; BOPProgressIndicator polls it every 200 ms.
8. **Part/App + Gui** — Make Thickness cancellable via `Ctrl+.` and MCP `cancel_operation`.
9. **Base/ProgressIndicator.h** — Wire OperationCancel into `Base::ProgressIndicator::userBreak()`.
10. **Sketcher/SketchObject.cpp** — Include geometry type in missing external reference errors.

### Dropped patches (were in blw-fixes-v2)

- **ElementMap.cpp child encoding skip logic** — Was breaking large MultiFuse element maps. Reverted to upstream.
- **Pre-flight solid checks** (PR #27760) — Upstream adopted a simplified version (post-failure shape type diagnostic).

## Related Issues

- #26119 — Boolean operations fail on compounds with coincident faces (Draft Array)
- #26327 — Shell.extrude() produces CompSolid with coincident internal faces
- #26400 — makePolygon creates elements with incomplete toponaming element map

## Resync Procedure

When updating to latest upstream:
```bash
git checkout main
git fetch origin
git merge --ff-only origin/main
git checkout -b blw-fixes-vN  # increment version
# Cherry-pick commits from previous blw-fixes branch, resolving conflicts
```

## Notes

- Uses pixi for dependency management (conda-forge packages)
- Build output: `build/release/bin/FreeCAD`
- AICopilot workbench: `~/Library/Application Support/FreeCAD/v1-2/Mod/AICopilot/`
- MCP server repo: `/Volumes/Files/claude/freecad-mcp/`
