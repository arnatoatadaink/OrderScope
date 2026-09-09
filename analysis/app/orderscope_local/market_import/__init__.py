"""Market-data import contracts for local Corporate Intelligence."""

from .canonical_bars import (
    CANONICAL_BAR_DATASET_SCHEMA_VERSION,
    CanonicalBarDataset,
    generate_fixture_canonical_bars,
)
from .d1_manifest import (
    D1ExportManifest,
    D1_EXPORT_MANIFEST_SCHEMA_VERSION,
    decode_d1_export_manifest,
)
from .fixture_importer import (
    RAW_IMPORT_SCHEMA_VERSION,
    RawImportResult,
    import_fixture_dump,
)

__all__ = [
    "CANONICAL_BAR_DATASET_SCHEMA_VERSION",
    "CanonicalBarDataset",
    "D1ExportManifest",
    "D1_EXPORT_MANIFEST_SCHEMA_VERSION",
    "RAW_IMPORT_SCHEMA_VERSION",
    "RawImportResult",
    "decode_d1_export_manifest",
    "generate_fixture_canonical_bars",
    "import_fixture_dump",
]
