"""Compatibility entrypoint for WP07 QGIS.

Legacy calls now use the source/year/audit-gated project builder. This module
does not silently accept a QGIS polygon object without provenance.
"""
from pathlib import Path

def create_project(*args, **kwargs):
    raise RuntimeError(
        "WP07 requires boundary GeoPackage, original provenance manifest, "
        "strict 2022 boundary vintage and tested polygon geometry. "
        "Use geo/qgis/build_project.py: build_ideburen_project(...). "
        "The old unverified geometry join has been disabled."
    )
