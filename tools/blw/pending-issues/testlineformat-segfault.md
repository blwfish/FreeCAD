# Issue draft: TestLineFormat.setQColor* SEGFAULT in ctest

**Status:** drafted 2026-04-23, not yet filed.
**Target repo:** FreeCAD/FreeCAD
**Suggested labels:** `Mod/TechDraw`, `tests`, `bug`

---

## Title

`TestLineFormat.setQColor*` ctest cases SEGFAULT — test misses `tests::initApplication()`

## Body

### Summary

The two `TestLineFormat.setQColor*` ctest cases SEGFAULT when run via `ctest`
or directly via `TechDraw_tests_run`. Reproduces on macOS arm64 against
upstream `weekly-2026.04.15`. The test was added in commit `383b7b5942`
(PR #28626, Mar 29 2026); the segfault is in the `LineFormat` constructor
chain, not in the code under test.

### Reproducer

```bash
cd build/release
ctest -R "TestLineFormat.setQColor"
# or directly:
build/release/tests/TechDraw_tests_run --gtest_filter='TestLineFormat.setQColor*'
```

Output:

```
[ RUN      ] TestLineFormat.setQColorKeepsOpaqueColorsOpaque
*** SegFault
The following tests FAILED:
    1603 - TestLineFormat.setQColorKeepsOpaqueColorsOpaque (SEGFAULT)
    1604 - TestLineFormat.setQColorPreservesAlphaValue (SEGFAULT)
```

### Crash signature (lldb)

```
* thread #1, queue = 'com.apple.main-thread',
  stop reason = EXC_BAD_ACCESS (code=1, address=0x8)
    frame #0: libFreeCADBase.dylib`Base::Handled::ref() const + 8
```

The address `0x8` is the offset of the refcount field on a null `Base::Handled`
instance — i.e. somebody is calling `ref()` on a null pointer.

### Root cause

The test `makeLineFormat()` helper:

```cpp
TechDraw::LineFormat makeLineFormat()
{
    return {Qt::SolidLine, 0.5, Base::Color(0.0F, 0.0F, 0.0F, 1.0F), true};
}
```

invokes the 4-argument `LineFormat` constructor, which initializes
`m_lineNumber` via `LineGenerator::fromQtStyle((Qt::PenStyle)m_style)`. That
function dereferences preferences:

```cpp
// src/Mod/TechDraw/App/LineGenerator.cpp:163
int LineGenerator::fromQtStyle(Qt::PenStyle style)
{
    ...
    if (Preferences::lineStandard() == ANSI) { ... }
    ...
}

// src/Mod/TechDraw/App/Preferences.cpp:458
int Preferences::lineStandard()
{
    int parameterValue = getPreferenceGroup("Standards")->GetInt("LineStandard", 1);
    ...
}

// src/Mod/TechDraw/App/Preferences.cpp:47
Base::Reference<ParameterGrp> Preferences::getPreferenceGroup(const char* Name)
{
    return App::GetApplication().GetUserParameter()
            .GetGroup("BaseApp/Preferences/Mod/TechDraw")->GetGroup(Name);
}
```

`App::GetApplication()` returns the global `App::Application` singleton, but
`tests/src/Mod/TechDraw/App/LineFormat.cpp` uses bare `TEST(...)` macros with
no fixture and never calls `tests::initApplication()` (compare with
`tests/src/Mod/Part/App/TopoShape.cpp`'s `SetUpTestSuite` that does).
The result is that `App::GetApplication()` returns an uninitialised handle,
and the subsequent `Base::Handled::ref()` faults.

### Suggested fix

Either:

1. **Add a test fixture** that calls `tests::initApplication()` in
   `SetUpTestSuite`, mirroring `TopoShapeTest`. Probably the right answer.
2. **Use the no-arg constructor or a non-preference-touching path** in the
   test helper, if the test was meant to be a pure unit test that doesn't
   need an Application.

Option 1 is the smaller change and matches the rest of the test suite.

### Why this hasn't been noticed

The TechDraw module is rarely the focus of fork rebuilds, and CI may not
fail-fast on these specific ctest entries. Found while running full ctest
locally on macOS 24.6.0 (Darwin arm64) against `weekly-2026.04.15`.

### Environment

- macOS 14 / Darwin 24.6.0, arm64
- `weekly-2026.04.15` (commit `d0dec51851`)
- pixi 0.48, OCCT 7.8, Qt 6
- Compiler: clang via conda-forge
