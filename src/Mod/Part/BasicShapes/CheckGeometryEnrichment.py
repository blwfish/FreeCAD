# SPDX-License-Identifier: LGPL-2.1-or-later

# CheckGeometryEnrichment.py
# 2024, enrichment module for CheckGeometry diagnostics
# LGPL 2.1 or later

"""
Enriches CheckGeometry error results with human-readable explanations,
coordinates, and suggested fixes.

This module transforms cryptic OCCT error codes into actionable diagnostics
that help users understand what's wrong and how to fix it.

Called from C++ TaskCheckGeometry.cpp to enhance error display.

Architecture Note:
    This module establishes a pattern for diagnostic enrichment modules
    that can be applied across FreeCAD. Functional modules do their work;
    companion diagnostic modules explain what went wrong and how to fix it.
"""

import FreeCAD as App

translate = App.Qt.translate

# =============================================================================
# BRepCheck_Status Error Explanations
# =============================================================================
# These correspond to the BRepCheck_Status enum from OCCT
# Each entry: error_name -> (explanation, suggested_fix, severity)
# Severity: "error" = definitely broken, "warning" = may cause issues

BREP_CHECK_EXPLANATIONS = {
    # Curve/Surface issues
    "Invalid point on curve": (
        "A vertex doesn't lie on its parent edge curve within the required tolerance. "
        "This often happens after boolean operations or imports from other CAD systems.",
        "Try Part → Refine Shape, or re-export from source with tighter tolerances.",
        "error"
    ),
    "Invalid point on curve on surface": (
        "A point on a 2D curve (pcurve) doesn't match its corresponding 3D curve position. "
        "The edge's representation on the face surface is inconsistent.",
        "Try Part → Refine Shape. If importing, check export settings in source application.",
        "error"
    ),
    "Invalid point on surface": (
        "A vertex doesn't lie on its parent face surface within tolerance.",
        "Try Part → Refine Shape or Check Geometry with increased tolerance.",
        "error"
    ),
    "No 3D curve": (
        "An edge exists but has no 3D curve definition. "
        "The edge only exists as a 2D curve on a face (pcurve).",
        "This may be valid for some edge types. If causing issues, try Part → Refine Shape.",
        "warning"
    ),
    "Multiple 3D curves": (
        "An edge has more than one 3D curve definition, which is ambiguous.",
        "Try Part → Refine Shape to consolidate the geometry.",
        "error"
    ),
    "Invalid 3D curve": (
        "The edge's 3D curve is malformed or degenerate.",
        "Try Part → Refine Shape. May need to recreate the geometry.",
        "error"
    ),
    "No curve on surface": (
        "An edge on a face has no pcurve (2D representation on the surface). "
        "This is required for proper face boundary definition.",
        "Try Part → Refine Shape or rebuild the face.",
        "error"
    ),
    "Invalid curve on surface": (
        "The edge's 2D curve on the face surface is malformed.",
        "Try Part → Refine Shape. Check if face was created from valid wires.",
        "error"
    ),
    "Invalid curve on closed surface": (
        "The edge's pcurve on a closed surface (sphere, torus, etc.) is invalid. "
        "Seam edges on closed surfaces require special handling.",
        "Try Part → Refine Shape. May need to recreate on a simpler surface.",
        "error"
    ),

    # Parameter flag issues
    "Invalid same range flag": (
        "The edge's parameter range doesn't match between 3D curve and pcurve.",
        "Try Part → Refine Shape to recalculate edge parameters.",
        "error"
    ),
    "Invalid same parameter flag": (
        "The edge claims its 3D and 2D curves use the same parameterization, but they don't. "
        "This causes incorrect point evaluation along the edge.",
        "Try Part → Check Geometry with 'Run BOP check', then Part → Refine Shape.",
        "error"
    ),
    "Invalid degenerated flag": (
        "An edge is marked as degenerate (zero-length) but isn't, or vice versa. "
        "Degenerate edges occur at poles of spheres, cones, etc.",
        "Try Part → Refine Shape. Usually harmless but may affect booleans.",
        "warning"
    ),

    # Edge/Wire issues
    "Free edge": (
        "An edge is not connected to any face. In a valid solid, all edges must belong to faces.",
        "Check for incomplete boolean operations. May need to rebuild the solid.",
        "error"
    ),
    "Invalid multi-connexity": (
        "An edge is shared by more than two faces (non-manifold geometry). "
        "Valid solids have edges shared by exactly two faces.",
        "Use Part → Boolean Fragments to split into manifold pieces, or simplify the model.",
        "error"
    ),
    "Invalid range": (
        "An edge's parameter range is invalid (e.g., start > end, or zero length).",
        "Try Part → Refine Shape. May need to recreate the edge.",
        "error"
    ),
    "Empty wire": (
        "A wire contains no edges.",
        "Delete the empty wire or check the sketch/operation that created it.",
        "error"
    ),
    "Redundant edge": (
        "A wire contains duplicate or unnecessary edges.",
        "Try Part → Refine Shape to clean up redundant geometry.",
        "warning"
    ),
    "Self-intersecting wire": (
        "Wire edges cross each other, creating an invalid loop. "
        "This often happens with complex sketches or offset operations.",
        "Simplify the sketch geometry, check for overlapping edges, or reduce offset distance.",
        "error"
    ),
    "No surface": (
        "A face has no underlying surface definition.",
        "The face is corrupt. Try recreating it from valid wires.",
        "error"
    ),
    "Invalid wire": (
        "A face boundary wire is not properly closed or oriented.",
        "Check that all face boundaries form closed loops. Try Part → Refine Shape.",
        "error"
    ),
    "Redundant wire": (
        "A face contains duplicate boundary wires.",
        "Try Part → Refine Shape to remove duplicate wires.",
        "warning"
    ),
    "Intersecting wires": (
        "Face boundary wires intersect each other. "
        "Inner and outer boundaries must not cross.",
        "Check sketch geometry for crossing contours. Separate into distinct faces if needed.",
        "error"
    ),
    "Invalid imbrication of wires": (
        "Face boundary wires are incorrectly nested. "
        "Holes must be inside the outer boundary, not overlapping.",
        "Check that holes are fully contained within the outer boundary.",
        "error"
    ),

    # Shell/Solid issues
    "Empty shell": (
        "A shell contains no faces.",
        "Delete the empty shell or check the operation that created it.",
        "error"
    ),
    "Redundant face": (
        "A shell contains duplicate faces.",
        "Try Part → Refine Shape to remove duplicate faces.",
        "warning"
    ),
    "Unorientable shape": (
        "The shape cannot be consistently oriented (like a Möbius strip). "
        "This is invalid for solid modeling.",
        "Check for flipped face normals. May need to rebuild with consistent orientation.",
        "error"
    ),
    "Not closed": (
        "Shell or wire has gaps - edges don't form a complete boundary. "
        "A valid solid requires a fully closed shell.",
        "Check for small gaps between faces. Try Part → Defeaturing or increase tolerance.",
        "error"
    ),
    "Not connected": (
        "The shape consists of disconnected pieces.",
        "Use Part → Compound if pieces should stay separate, or fuse them together.",
        "warning"
    ),
    "Sub-shape not in shape": (
        "A referenced sub-shape (vertex, edge, face) is not part of the parent shape.",
        "Internal inconsistency. Try Part → Refine Shape or recreate the geometry.",
        "error"
    ),
    "Bad orientation": (
        "A sub-shape has incorrect orientation relative to its parent.",
        "Try Part → Refine Shape. May indicate boolean operation issues.",
        "error"
    ),
    "Bad orientation of sub-shape": (
        "A sub-shape's orientation doesn't match the expected relationship with its parent.",
        "Try Part → Refine Shape.",
        "error"
    ),
    "Invalid tolerance value": (
        "A shape has an unreasonable tolerance value (too large or too small).",
        "Try Part → Refine Shape. Check if imported geometry has extreme tolerances.",
        "warning"
    ),
    "Check failed": (
        "The geometry check itself failed - couldn't complete the validation.",
        "The shape may be severely corrupted. Try recreating it.",
        "error"
    ),
}


# =============================================================================
# BOPAlgo_CheckStatus Error Explanations
# =============================================================================
# These correspond to BOPAlgo_CheckStatus enum from OCCT
# BOP = Boolean OPeration checks - more stringent than BRepCheck

BOP_CHECK_EXPLANATIONS = {
    "Boolean operation: unknown check": (
        "The boolean operation checker encountered an unknown condition.",
        "Try simplifying the geometry or using different boolean operation settings.",
        "warning"
    ),
    "Boolean operation: bad type": (
        "The shape type is not suitable for boolean operations. "
        "Booleans work best with solids.",
        "Ensure you're operating on valid solids, not shells or compounds of faces.",
        "error"
    ),
    "Boolean operation: self-intersection found": (
        "The shape intersects itself, which prevents clean boolean operations. "
        "This often occurs from: overlapping elements in arrays/patterns (check that "
        "spacing exceeds element size), Shell.extrude() on complex profiles, or "
        "coincident/overlapping faces created by fusions.",
        "For arrays: increase spacing or decrease element size to eliminate overlaps. "
        "Otherwise: try Part → Refine Shape, or Part → Boolean Fragments with "
        "increased 'Fuzzy tolerance'.",
        "error"
    ),
    "Boolean operation: edge too small": (
        "An edge is shorter than the geometric tolerance, making it effectively zero-length. "
        "This causes numerical instability in boolean operations.",
        "Try Part → Defeaturing to remove small features, or increase model scale.",
        "error"
    ),
    "Boolean operation: non-recoverable face": (
        "A face cannot be properly reconstructed during the boolean operation. "
        "The face geometry is too complex or degenerate.",
        "Try simplifying the face or splitting it into multiple simpler faces.",
        "error"
    ),
    "Boolean operation: incompatibility of vertex": (
        "Vertices from different shapes that should merge are too far apart. "
        "The tolerance gap prevents proper joining.",
        "Try increasing 'Fuzzy tolerance' in boolean operation settings.",
        "error"
    ),
    "Boolean operation: incompatibility of edge": (
        "Edges from different shapes that should merge don't align properly.",
        "Try increasing 'Fuzzy tolerance' or ensuring edges are truly coincident.",
        "error"
    ),
    "Boolean operation: incompatibility of face": (
        "Faces from different shapes don't properly align or intersect. "
        "Their surface definitions may be slightly different.",
        "Try increasing 'Fuzzy tolerance'. If faces should be coplanar, ensure they truly are.",
        "error"
    ),
    "Boolean operation: aborted": (
        "The boolean operation was cancelled or failed to complete.",
        "Try with different settings or simplify the input geometry.",
        "error"
    ),
    "Boolean operation: GeomAbs_C0": (
        "The shape has only C0 continuity (position continuous but not tangent). "
        "This can cause issues with some operations expecting smoother geometry.",
        "Usually acceptable. If causing problems, try Part → Refine Shape.",
        "warning"
    ),
    "Boolean operation: invalid curve on surface": (
        "A pcurve (2D curve on surface) is invalid for boolean operations.",
        "Try Part → Refine Shape to rebuild edge representations.",
        "error"
    ),
    "Boolean operation: not valid": (
        "General validity check failed for boolean operations.",
        "Run Part → Check Geometry to identify specific issues, then Part → Refine Shape.",
        "error"
    ),
}


# =============================================================================
# TNP (Topological Naming Problem) Error Handling
# =============================================================================
# Integrated from tnp_decoder - decodes cryptic reference errors

class TNPError:
    """Represents a decoded TNP error with human-readable components."""

    def __init__(self, broken_sketch_name, broken_geom_spec,
                 ref_sketch_name, ref_geom_spec, doc=None):
        self.broken_sketch_name = broken_sketch_name
        self.broken_geom_spec = broken_geom_spec
        self.ref_sketch_name = ref_sketch_name
        self.ref_geom_spec = ref_geom_spec
        self.doc = doc or App.activeDocument()

        self.broken_sketch = self.doc.getObject(broken_sketch_name) if self.doc else None
        self.ref_sketch = self.doc.getObject(ref_sketch_name) if self.doc else None

    @property
    def broken_label(self):
        """Get the label of the broken sketch."""
        return self.broken_sketch.Label if self.broken_sketch else self.broken_sketch_name

    @property
    def ref_label(self):
        """Get the label of the referenced sketch."""
        return self.ref_sketch.Label if self.ref_sketch else self.ref_sketch_name

    def get_geom_description(self):
        """Get a human-readable description of the referenced geometry."""
        if not self.ref_sketch or not hasattr(self.ref_sketch, 'Geometry'):
            return None

        try:
            spec = self.ref_geom_spec
            if spec.startswith('e') or spec.startswith('g'):
                # Edge/geometry reference: e7v2 means edge 7, vertex 2
                prefix = spec[0]
                rest = spec[1:]
                geom_num = int(rest.split('v')[0])
                vertex_num = None
                if 'v' in rest:
                    vertex_num = int(rest.split('v')[1])

                geom_list = self.ref_sketch.Geometry
                if geom_num >= len(geom_list):
                    return f"{'edge' if prefix == 'e' else 'geometry'} {geom_num} (OUT OF RANGE - only {len(geom_list)} geometries exist)"

                geom = geom_list[geom_num]
                geom_type = type(geom).__name__
                desc = f"{'edge' if prefix == 'e' else 'geometry'} {geom_num} ({geom_type})"

                # Add geometry-specific details
                if hasattr(geom, 'StartPoint') and hasattr(geom, 'EndPoint'):
                    sp, ep = geom.StartPoint, geom.EndPoint
                    desc += f"\n      From ({sp.x:.2f}, {sp.y:.2f}) to ({ep.x:.2f}, {ep.y:.2f})"
                elif hasattr(geom, 'Center') and hasattr(geom, 'Radius'):
                    c = geom.Center
                    desc += f"\n      Center: ({c.x:.2f}, {c.y:.2f}), Radius: {geom.Radius:.2f}"

                if vertex_num is not None:
                    desc += f", vertex {vertex_num}"

                return desc

        except Exception as e:
            return f"(error decoding: {e})"

        return self.ref_geom_spec

    def format_report(self):
        """Return formatted human-readable error report."""
        lines = [
            "",
            "=" * 75,
            "TNP Error Decoded",
            "=" * 75,
            "",
            "BROKEN REFERENCE in:",
            f"  Sketch: {self.broken_sketch_name} ({self.broken_label})",
            f"  Geometry: {self.broken_geom_spec}",
            "",
            "Was pointing to:",
            f"  Sketch: {self.ref_sketch_name} ({self.ref_label})",
            f"  Geometry: {self.get_geom_description() or self.ref_geom_spec}",
            "",
            "EXPLANATION:",
            f"  The sketch '{self.broken_label}' contains external geometry references",
            f"  to '{self.ref_label}'. When '{self.ref_label}' was edited, its geometry",
            "  indices changed, breaking the reference.",
            "",
            "SUGGESTED FIXES:",
            f"  1. Delete and re-create the external geometry references in '{self.broken_label}'",
            f"  2. Avoid editing '{self.ref_label}' - treat it as a locked master sketch",
            "  3. Consider using SubShapeBinder instead of external geometry for more stable references",
            "",
            "=" * 75,
            ""
        ]
        return "\n".join(lines)


def parse_tnp_error(error_string):
    """
    Parse a TNP error line from FreeCAD report view.

    Args:
        error_string: A line like:
            "External geometry doc#Sketch004.e2 missing reference: Sketch003.;e7v2;SKT"

    Returns:
        TNPError object, or None if parsing failed
    """
    error_string = error_string.strip()
    if "missing reference:" not in error_string:
        return None

    parts = error_string.split("missing reference:")
    if len(parts) != 2:
        return None

    # Parse broken reference: "...Sketch004.e2" or "...#Sketch004.e2"
    broken_part = parts[0].strip()
    if '#' in broken_part:
        broken_part = broken_part.split('#')[-1]

    if '.' not in broken_part:
        return None

    broken_sketch_name, broken_geom = broken_part.rsplit('.', 1)

    # Parse reference: "Sketch003.;e7v2;SKT"
    ref_parts = parts[1].strip().split(';')
    ref_sketch_name = ref_parts[0].strip().rstrip('.')
    ref_geom_spec = ref_parts[1].strip() if len(ref_parts) > 1 else ""

    return TNPError(broken_sketch_name.strip(), broken_geom.strip(),
                    ref_sketch_name, ref_geom_spec)


def decode_tnp(error_string):
    """
    Decode and print a single TNP error message.

    Example:
        decode_tnp("Sketch004.e2 missing reference: Sketch003.;e7v2;SKT")
    """
    error = parse_tnp_error(error_string)
    if error is None:
        print("Could not parse TNP error. Expected format:")
        print("  'SketchXXX.eN missing reference: SketchYYY.;eN;SKT'")
        print(f"Got: {error_string}")
        return None

    print(error.format_report())
    return error


def decode_tnp_batch(error_text):
    """
    Decode multiple TNP errors at once.

    Example:
        decode_tnp_batch('''
            Sketch004.e2 missing reference: Sketch003.;e7v2;SKT
            Sketch006.e1 missing reference: Sketch005.;e2v1;SKT
        ''')
    """
    lines = [l.strip() for l in error_text.strip().split('\n')
             if l.strip() and 'missing reference' in l]

    if not lines:
        print("No TNP error lines found in input")
        return []

    print(f"\nDecoding {len(lines)} TNP error(s)...\n")
    errors = []
    for line in lines:
        error = decode_tnp(line)
        if error:
            errors.append(error)
    return errors


# =============================================================================
# Main Enrichment API - Called from C++ or Python
# =============================================================================

def get_error_enrichment(error_type, error_name):
    """
    Get enrichment data for a geometry error.

    Args:
        error_type: "BRepCheck" or "BOPAlgo"
        error_name: The error string (e.g., "Self-intersecting wire")

    Returns:
        dict with keys:
            - explanation: Human-readable description of the error
            - suggested_fix: What the user should try
            - severity: "error" or "warning"
        Returns None if error_name not found.
    """
    if error_type == "BRepCheck":
        data = BREP_CHECK_EXPLANATIONS.get(error_name)
    elif error_type == "BOPAlgo":
        data = BOP_CHECK_EXPLANATIONS.get(error_name)
    else:
        return None

    if data is None:
        return None

    return {
        "explanation": data[0],
        "suggested_fix": data[1],
        "severity": data[2]
    }


def format_enriched_error(error_type, error_name, shape_name="", coordinates=None):
    """
    Format a complete enriched error message for display.

    Args:
        error_type: "BRepCheck" or "BOPAlgo"
        error_name: The error string
        shape_name: Name of the shape element (e.g., "Edge12")
        coordinates: Optional (x, y, z) tuple or bounding box

    Returns:
        Formatted multi-line string for display
    """
    enrichment = get_error_enrichment(error_type, error_name)

    lines = []
    lines.append(f"{'─' * 60}")
    lines.append(f"Error: {error_name}")
    if shape_name:
        lines.append(f"Location: {shape_name}")

    if coordinates:
        if len(coordinates) == 3:
            lines.append(f"At: ({coordinates[0]:.2f}, {coordinates[1]:.2f}, {coordinates[2]:.2f})")
        elif len(coordinates) == 6:
            # Bounding box: xmin, ymin, zmin, xmax, ymax, zmax
            cx = (coordinates[0] + coordinates[3]) / 2
            cy = (coordinates[1] + coordinates[4]) / 2
            cz = (coordinates[2] + coordinates[5]) / 2
            lines.append(f"Near: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

    if enrichment:
        lines.append("")
        lines.append(f"What this means:")
        lines.append(f"  {enrichment['explanation']}")
        lines.append("")
        lines.append(f"Suggested fix:")
        lines.append(f"  {enrichment['suggested_fix']}")
    else:
        lines.append("")
        lines.append("(No additional information available for this error type)")

    lines.append(f"{'─' * 60}")

    return "\n".join(lines)


def enrich_check_geometry_results(results):
    """
    Enrich a list of CheckGeometry results with explanations.

    Args:
        results: List of dicts with keys: error_type, error_name, shape_name, coordinates

    Returns:
        List of enriched result dicts with added: explanation, suggested_fix, severity
    """
    enriched = []
    for result in results:
        enrichment = get_error_enrichment(
            result.get("error_type", ""),
            result.get("error_name", "")
        )
        enriched_result = result.copy()
        if enrichment:
            enriched_result.update(enrichment)
        enriched.append(enriched_result)
    return enriched


# =============================================================================
# Convenience function for FreeCAD console
# =============================================================================

def explain(error_name):
    """
    Quick lookup of an error explanation from the FreeCAD console.

    Example:
        from BasicShapes.CheckGeometryEnrichment import explain
        explain("Self-intersecting wire")
    """
    # Try BRepCheck first
    enrichment = get_error_enrichment("BRepCheck", error_name)
    if not enrichment:
        # Try BOPAlgo
        enrichment = get_error_enrichment("BOPAlgo", error_name)

    if not enrichment:
        # Try partial match
        for name in list(BREP_CHECK_EXPLANATIONS.keys()) + list(BOP_CHECK_EXPLANATIONS.keys()):
            if error_name.lower() in name.lower():
                print(f"Did you mean: '{name}'?")
        print(f"No explanation found for '{error_name}'")
        return

    print(f"\n{error_name}")
    print("=" * len(error_name))
    print(f"\n{enrichment['explanation']}")
    print(f"\nSuggested fix: {enrichment['suggested_fix']}")
    print(f"Severity: {enrichment['severity']}\n")
