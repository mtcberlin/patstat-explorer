#!/usr/bin/env python3
"""
Build IPC 2026.01 SQLite Database.

Parses official WIPO IPC 2026.01 release files and creates a local SQLite
database for validation before BigQuery upload.

Usage:
    python build_ipc_2026_database.py
    python build_ipc_2026_database.py --data-dir /path/to/ipc2026.01
    python build_ipc_2026_database.py --output /path/to/output.db

Data source: context/ipc_analysis/ipc2026.01/
Output: context/ipc_analysis/patent-classification-2026.db
"""

import argparse
import csv
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# IPC XML namespace
NS = "http://www.wipo.int/classifications/ipc/masterfiles"
NS_MAP = {"ipc": NS}

# Kinds that represent classifying entries (kept in hierarchy)
CLASSIFYING_KINDS = {"s", "c", "u", "m", "1", "2", "3", "4", "5", "6", "7", "8", "9"}

# Kind → hierarchy level mapping
KIND_TO_LEVEL = {
    "s": 2,  # section
    "c": 3,  # class
    "u": 4,  # subclass
    "m": 5,  # main group
    "1": 6, "2": 7, "3": 8, "4": 9, "5": 10,
    "6": 11, "7": 12, "8": 13, "9": 14,
}

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "context" / "ipc_analysis" / "ipc2026.01"
DEFAULT_OUTPUT = PROJECT_ROOT / "context" / "ipc_analysis" / "patent-classification-2026.db"


# =============================================================================
# Symbol Format Conversion (same as upload_ipc_hierarchy.py)
# =============================================================================

def zeropad_to_patstat(zeropad: str) -> str | None:
    """Convert zero-padded symbol to PATSTAT space-padded format.

    Example: 'A23L0007117000' -> 'A23L   7/117'
    """
    if len(zeropad) < 14:
        return None  # section/class/subclass level, no PATSTAT format

    subclass = zeropad[:4]
    group_int = int(zeropad[4:8])
    subgroup_raw = zeropad[8:14]

    subgroup_str = subgroup_raw.rstrip("0") or "00"
    group_padded = str(group_int).rjust(4)

    return f"{subclass}{group_padded}/{subgroup_str}"


def zeropad_to_short(zeropad: str) -> str | None:
    """Convert zero-padded symbol to short human-readable format.

    Example: 'A23L0007117000' -> 'A23L7/117'
    """
    if len(zeropad) < 14:
        return zeropad  # section/class/subclass are already short

    subclass = zeropad[:4]
    group_int = int(zeropad[4:8])
    subgroup_raw = zeropad[8:14]

    subgroup_str = subgroup_raw.rstrip("0") or "00"

    return f"{subclass}{group_int}/{subgroup_str}"


# =============================================================================
# XML Title Extraction
# =============================================================================

def extract_title(entry) -> str:
    """Extract English title text from an ipcEntry element.

    Collects text from titlePart/text elements and entryReference elements.
    Returns title without cross-references (those go to additional_content later).
    """
    ns = f"{{{NS}}}"
    parts = []

    for text_body in entry.findall(f"{ns}textBody"):
        for title in text_body.findall(f"{ns}title"):
            for title_part in title.findall(f"{ns}titlePart"):
                text_el = title_part.find(f"{ns}text")
                if text_el is not None:
                    # Get direct text content only (not entryReference children)
                    text = text_el.text or ""
                    # Also get tail text after child elements
                    for child in text_el:
                        if child.tail:
                            text += child.tail
                    text = text.strip()
                    if text:
                        parts.append(text)

    title = "; ".join(parts) if parts else ""
    # Clean up whitespace
    title = " ".join(title.split())
    return title


# =============================================================================
# Step 1: Parse Scheme XML
# =============================================================================

def parse_scheme_xml(xml_path: Path) -> list[dict]:
    """Parse EN_ipc_scheme_20260101.xml and extract hierarchy entries.

    Walks the nested XML tree recursively, tracking parent chain.
    Skips non-classifying entries (kind t, n, i, g) but recurses into their children.
    """
    print(f"Parsing scheme XML: {xml_path}")
    print(f"  File size: {xml_path.stat().st_size / 1024 / 1024:.1f} MB")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    entries = []
    ns = f"{{{NS}}}"

    def walk(element, parent_symbol: str):
        """Recursively walk ipcEntry elements."""
        for child in element.findall(f"{ns}ipcEntry"):
            kind = child.get("kind", "")
            symbol = child.get("symbol", "")

            if kind in CLASSIFYING_KINDS and symbol:
                level = KIND_TO_LEVEL.get(kind, 0)
                title_en = extract_title(child)

                entries.append({
                    "symbol": symbol,
                    "kind": kind,
                    "level": level,
                    "parent": parent_symbol,
                    "title_en": title_en,
                })

                # Recurse with this entry as parent
                walk(child, symbol)
            else:
                # Non-classifying entry (t, n, i, g) — skip but recurse
                # Children inherit the same parent
                walk(child, parent_symbol)

    walk(root, "IPC")

    print(f"  Extracted {len(entries):,} classifying entries")

    # Distribution
    from collections import Counter
    kind_counts = Counter(e["kind"] for e in entries)
    for kind in sorted(kind_counts.keys(), key=lambda k: KIND_TO_LEVEL.get(k, 99)):
        print(f"    kind={kind} (level {KIND_TO_LEVEL.get(kind, '?')}): {kind_counts[kind]:,}")

    return entries


# =============================================================================
# SQLite Database Creation
# =============================================================================

def create_database(db_path: Path, entries: list[dict]):
    """Create SQLite database with ipc table from parsed entries."""
    print(f"\nCreating SQLite database: {db_path}")

    if db_path.exists():
        db_path.unlink()
        print("  Removed existing database")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create ipc table — full schema with placeholders for later enrichment steps
    cur.execute("""
        CREATE TABLE ipc (
            symbol TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            level INTEGER NOT NULL,
            parent TEXT NOT NULL,
            symbol_short TEXT,
            parent_short TEXT,
            symbol_patstat TEXT,
            title_en TEXT,
            title_full TEXT,
            ipc_version TEXT DEFAULT '20260101',
            latest_version_date TEXT,
            introduced_date TEXT,
            additional_content TEXT,
            section_title TEXT,
            class_title TEXT,
            subclass_title TEXT
        )
    """)

    # Insert entries with derived symbol formats
    rows = []
    for e in entries:
        symbol = e["symbol"]
        parent = e["parent"]

        symbol_short = zeropad_to_short(symbol)
        parent_short = zeropad_to_short(parent) if parent != "IPC" else "IPC"
        symbol_patstat = zeropad_to_patstat(symbol)

        rows.append((
            symbol,
            e["kind"],
            e["level"],
            parent,
            symbol_short,
            parent_short,
            symbol_patstat,
            e["title_en"],
        ))

    cur.executemany("""
        INSERT INTO ipc (symbol, kind, level, parent, symbol_short, parent_short,
                         symbol_patstat, title_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    # Create indexes
    cur.execute("CREATE INDEX idx_ipc_level ON ipc(level)")
    cur.execute("CREATE INDEX idx_ipc_parent ON ipc(parent)")
    cur.execute("CREATE INDEX idx_ipc_kind ON ipc(kind)")
    cur.execute("CREATE INDEX idx_ipc_symbol_short ON ipc(symbol_short)")
    cur.execute("CREATE INDEX idx_ipc_symbol_patstat ON ipc(symbol_patstat)")

    # Create metadata table
    cur.execute("""
        CREATE TABLE ipc_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    metadata = [
        ("ipc_version", "2026.01"),
        ("ipc_edition", "20260101"),
        ("ipc_language", "EN"),
        ("source_file", "EN_ipc_scheme_20260101.xml"),
        ("total_entries", str(len(rows))),
    ]
    cur.executemany("INSERT INTO ipc_metadata VALUES (?, ?)", metadata)

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM ipc")
    count = cur.fetchone()[0]
    print(f"  Inserted {count:,} rows into ipc table")

    # Quick validation
    cur.execute("SELECT level, COUNT(*) FROM ipc GROUP BY level ORDER BY level")
    print("  Level distribution:")
    for level, cnt in cur.fetchall():
        print(f"    level {level}: {cnt:,}")

    # Sample entries
    print("  Sample entries:")
    cur.execute("SELECT symbol, symbol_short, symbol_patstat, kind, level, parent_short, title_en FROM ipc LIMIT 5")
    for row in cur.fetchall():
        print(f"    {row[1] or row[0]:20s} kind={row[3]} level={row[4]} parent={row[5]:10s} {(row[6] or '')[:50]}")

    cur.execute("SELECT symbol, symbol_short, symbol_patstat, kind, level, parent_short, title_en FROM ipc WHERE level >= 7 LIMIT 3")
    for row in cur.fetchall():
        print(f"    {row[1] or row[0]:20s} kind={row[3]} level={row[4]} parent={row[5]:10s} {(row[6] or '')[:50]}")

    conn.close()
    print(f"  Database size: {db_path.stat().st_size / 1024:.0f} KB")


# =============================================================================
# Step 2: Cross-check with Title List
# =============================================================================

def enrich_from_title_list(db_path: Path, data_dir: Path):
    """Cross-check and fill title gaps from EN_ipc_title_list files.

    The title list files are tab-separated: symbol<tab>title
    They include cross-references in parentheses which the scheme XML may omit.
    """
    title_dir = data_dir / "EN_ipc_title_list_20260101"
    if not title_dir.exists():
        print(f"\nSkipping title list: directory not found: {title_dir}")
        return

    print(f"\nStep 2: Cross-checking with title list files")

    # Parse all 8 section files
    title_map = {}
    for section_file in sorted(title_dir.glob("EN_ipc_section_*_title_list_20260101.txt")):
        with open(section_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if "\t" in line:
                    symbol, title = line.split("\t", 1)
                    symbol = symbol.strip()
                    title = title.strip()
                    if symbol and title:
                        title_map[symbol] = title

    print(f"  Loaded {len(title_map):,} titles from title list files")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Find entries with empty titles in DB
    cur.execute("SELECT symbol FROM ipc WHERE title_en IS NULL OR title_en = ''")
    empty_symbols = {row[0] for row in cur.fetchall()}
    print(f"  Entries with empty title_en in DB: {len(empty_symbols):,}")

    # Fill gaps
    filled = 0
    for symbol in empty_symbols:
        if symbol in title_map:
            cur.execute("UPDATE ipc SET title_en = ? WHERE symbol = ?",
                        (title_map[symbol], symbol))
            filled += 1

    # Count mismatches (different title in DB vs title list)
    cur.execute("SELECT symbol, title_en FROM ipc WHERE title_en IS NOT NULL AND title_en != ''")
    mismatches = 0
    for symbol, db_title in cur.fetchall():
        if symbol in title_map and title_map[symbol] != db_title:
            mismatches += 1

    conn.commit()
    conn.close()

    print(f"  Filled {filled:,} empty titles from title list")
    print(f"  Title mismatches (DB vs title list): {mismatches:,}")


# =============================================================================
# Step 3: Add latest_version_date from Valid Symbols XML
# =============================================================================

def enrich_from_valid_symbols(db_path: Path, data_dir: Path):
    """Add latest_version_date from ipc_valid_symbols_20260101.xml."""
    xml_path = data_dir / "ipc_valid_symbols_20260101" / "ipc_valid_symbols_20260101.xml"
    if not xml_path.exists():
        print(f"\nSkipping valid symbols: file not found: {xml_path}")
        return

    print(f"\nStep 3: Adding latest_version_date from valid symbols XML")

    ns = f"{{{NS}}}"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    updates = []
    for sym_el in root.iter(f"{ns}IPCSymbol"):
        symbol = sym_el.get("symbol", "")
        version_date = sym_el.get("latestVersionIndicator", "")
        if symbol and version_date:
            updates.append((version_date, symbol))

    print(f"  Parsed {len(updates):,} symbols with version dates")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany(
        "UPDATE ipc SET latest_version_date = ? WHERE symbol = ?",
        updates,
    )

    # Count how many actually matched
    cur.execute("SELECT COUNT(*) FROM ipc WHERE latest_version_date IS NOT NULL")
    matched = cur.fetchone()[0]

    conn.commit()
    conn.close()

    print(f"  Updated {matched:,} entries with latest_version_date")


# =============================================================================
# Step 4: Build ipc_everused Table + Add introduced_date
# =============================================================================

def build_everused_table(db_path: Path, data_dir: Path):
    """Parse ever-used symbols CSV and create ipc_everused table.

    CSV format: symbol;introduced_date;deprecated_date
    deprecated_date is '-' for active symbols.
    """
    csv_path = data_dir / "20260101_inventory_of_IPC_ever_used_symbols.csv"
    if not csv_path.exists():
        print(f"\nSkipping ever-used: file not found: {csv_path}")
        return

    print(f"\nStep 4: Building ipc_everused table from CSV")

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(";")
            if len(parts) != 3:
                continue

            symbol = parts[0].strip()
            introduced = parts[1].strip()
            deprecated = parts[2].strip()

            is_active = deprecated == "-"
            deprecated_date = None if is_active else deprecated
            symbol_patstat = zeropad_to_patstat(symbol)

            rows.append((symbol, symbol_patstat, introduced, deprecated_date, is_active))

    print(f"  Parsed {len(rows):,} ever-used symbols")
    active = sum(1 for r in rows if r[4])
    deprecated = len(rows) - active
    print(f"    Active: {active:,}")
    print(f"    Deprecated: {deprecated:,}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ipc_everused (
            symbol TEXT PRIMARY KEY,
            symbol_patstat TEXT,
            introduced_date TEXT,
            deprecated_date TEXT,
            is_active INTEGER
        )
    """)

    cur.executemany("""
        INSERT OR REPLACE INTO ipc_everused
        (symbol, symbol_patstat, introduced_date, deprecated_date, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_everused_patstat ON ipc_everused(symbol_patstat)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_everused_active ON ipc_everused(is_active)")

    # Also update introduced_date in the main ipc table
    cur.execute("""
        UPDATE ipc SET introduced_date = (
            SELECT introduced_date FROM ipc_everused WHERE ipc_everused.symbol = ipc.symbol
        )
        WHERE EXISTS (
            SELECT 1 FROM ipc_everused WHERE ipc_everused.symbol = ipc.symbol
        )
    """)

    cur.execute("SELECT COUNT(*) FROM ipc WHERE introduced_date IS NOT NULL")
    matched = cur.fetchone()[0]

    conn.commit()
    conn.close()

    print(f"  Created ipc_everused table with {len(rows):,} rows")
    print(f"  Updated introduced_date for {matched:,} ipc entries")


# =============================================================================
# Step 5: Extract Definitions into additional_content
# =============================================================================

def enrich_from_definitions(db_path: Path, data_dir: Path):
    """Extract plain text from definitions XML into additional_content column."""
    xml_path = data_dir / "ipc_definitions_20260101" / "EN_ipc_definitions_20260101.xml"
    if not xml_path.exists():
        print(f"\nSkipping definitions: file not found: {xml_path}")
        return

    print(f"\nStep 5: Extracting definitions into additional_content")

    ns = f"{{{NS}}}"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    updates = []
    for defn in root.iter(f"{ns}IPC-DEFINITION"):
        ipc_code = defn.get("IPC", "")
        if not ipc_code:
            continue

        parts = []

        # Extract glossary terms
        glossary = defn.find(f"{ns}GLOSSARYOFTERMS")
        if glossary is not None:
            text = " ".join(glossary.itertext()).strip()
            text = " ".join(text.split())  # normalize whitespace
            if text:
                parts.append(f"Glossary: {text}")

        # Extract limiting references
        lref = defn.find(f"{ns}REFERENCES/{ns}LIMITINGREFERENCES")
        if lref is not None:
            text = " ".join(lref.itertext()).strip()
            text = " ".join(text.split())
            if text:
                parts.append(f"Limiting references: {text}")

        # Extract application-oriented references
        aref = defn.find(f"{ns}REFERENCES/{ns}APPLICATIONORIENTEDREFERENCES")
        if aref is not None:
            text = " ".join(aref.itertext()).strip()
            text = " ".join(text.split())
            if text:
                parts.append(f"Application references: {text}")

        # Extract notes
        for note in defn.findall(f".//{ns}NOTE"):
            text = " ".join(note.itertext()).strip()
            text = " ".join(text.split())
            if text:
                parts.append(f"Note: {text}")

        if parts:
            combined = " | ".join(parts)
            updates.append((combined, ipc_code))

    print(f"  Extracted definitions for {len(updates):,} symbols")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany(
        "UPDATE ipc SET additional_content = ? WHERE symbol = ?",
        updates,
    )

    cur.execute("SELECT COUNT(*) FROM ipc WHERE additional_content IS NOT NULL")
    matched = cur.fetchone()[0]

    conn.commit()
    conn.close()

    print(f"  Updated additional_content for {matched:,} ipc entries")


# =============================================================================
# Step 6: Build ipc_catchword Table
# =============================================================================

def build_catchword_table(db_path: Path, data_dir: Path):
    """Parse catchword index XML and create ipc_catchword table.

    Flattens hierarchical keyword entries into one row per keyword-symbol pair.
    """
    xml_path = data_dir / "ipc_catchwordindex_20260101" / "EN_ipc_catchwordindex_20260101.xml"
    if not xml_path.exists():
        print(f"\nSkipping catchword index: file not found: {xml_path}")
        return

    print(f"\nStep 6: Building ipc_catchword table from catchword index XML")

    ns = f"{{{NS}}}"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    rows = []

    def walk_catchwords(element, parent_keyword: str | None):
        """Recursively extract keyword-symbol pairs."""
        for entry in element.findall(f"{ns}CWEntry"):
            indication = entry.find(f"{ns}CWIndication")
            keyword = ""
            if indication is not None and indication.text:
                keyword = indication.text.strip()

            # Get symbol references
            refs_el = entry.find(f"{ns}CWReferences")
            if refs_el is not None:
                for sref in refs_el.findall(f"{ns}sref"):
                    symbol = sref.get("ref", "")
                    if symbol and keyword:
                        symbol_short = zeropad_to_short(symbol)
                        symbol_patstat = zeropad_to_patstat(symbol)
                        rows.append((keyword, symbol, symbol_short, symbol_patstat,
                                     parent_keyword))

            # Recurse into children
            walk_catchwords(entry, keyword or parent_keyword)

    walk_catchwords(root, None)

    print(f"  Extracted {len(rows):,} keyword-symbol pairs")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ipc_catchword (
            catchword TEXT NOT NULL,
            symbol TEXT NOT NULL,
            symbol_short TEXT,
            symbol_patstat TEXT,
            parent_catchword TEXT
        )
    """)

    cur.executemany("""
        INSERT INTO ipc_catchword
        (catchword, symbol, symbol_short, symbol_patstat, parent_catchword)
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_catchword_word ON ipc_catchword(catchword)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catchword_symbol ON ipc_catchword(symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catchword_patstat ON ipc_catchword(symbol_patstat)")

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM ipc_catchword")
    count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT catchword) FROM ipc_catchword")
    distinct_kw = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT symbol) FROM ipc_catchword")
    distinct_sym = cur.fetchone()[0]

    conn.close()

    print(f"  Created ipc_catchword table: {count:,} rows")
    print(f"    Distinct keywords: {distinct_kw:,}")
    print(f"    Distinct symbols: {distinct_sym:,}")


# =============================================================================
# Step 7: Build ipc_concordance Table
# =============================================================================

def build_concordance_table(db_path: Path, data_dir: Path):
    """Parse concordance list XML and create ipc_concordance table."""
    xml_path = data_dir / "ipc_concordancelist_20260101.xml"
    if not xml_path.exists():
        print(f"\nSkipping concordance: file not found: {xml_path}")
        return

    print(f"\nStep 7: Building ipc_concordance table from concordance list XML")

    ns = f"{{{NS}}}"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    from_version = root.get("from-version", "20250101")
    to_version = root.get("to-version", "20260101")

    rows = []
    for conc in root.findall(f"{ns}concordance"):
        from_symbol = conc.get("from-symbol", "")
        from_mod = conc.get("modification", "")
        revision_project = conc.get("revision-project", "")

        for to_el in conc.findall(f"{ns}concordance-to"):
            to_symbol = to_el.get("to-symbol", "")
            to_mod = to_el.get("modification", "")
            default_reclass = to_el.get("default-reclassification", "")

            from_patstat = zeropad_to_patstat(from_symbol)
            to_patstat = zeropad_to_patstat(to_symbol)

            rows.append((
                from_symbol, from_patstat,
                to_symbol, to_patstat,
                from_version, to_version,
                from_mod, default_reclass, revision_project,
            ))

    print(f"  Parsed {len(rows):,} concordance mappings")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ipc_concordance (
            from_symbol TEXT NOT NULL,
            from_symbol_patstat TEXT,
            to_symbol TEXT NOT NULL,
            to_symbol_patstat TEXT,
            from_version TEXT NOT NULL,
            to_version TEXT NOT NULL,
            modification TEXT,
            default_reclassification TEXT,
            revision_project TEXT
        )
    """)

    cur.executemany("""
        INSERT INTO ipc_concordance
        (from_symbol, from_symbol_patstat, to_symbol, to_symbol_patstat,
         from_version, to_version, modification, default_reclassification,
         revision_project)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_conc_from ON ipc_concordance(from_symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_conc_to ON ipc_concordance(to_symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_conc_from_patstat ON ipc_concordance(from_symbol_patstat)")

    conn.commit()

    # Stats
    from collections import Counter
    cur.execute("SELECT modification, COUNT(*) FROM ipc_concordance GROUP BY modification")
    print("  Modification types:")
    for mod, cnt in cur.fetchall():
        print(f"    {mod}: {cnt:,}")

    conn.close()

    print(f"  Created ipc_concordance table with {len(rows):,} rows")


# =============================================================================
# Step 8: Derive title_full, section_title, class_title, subclass_title
# =============================================================================

def derive_title_chains(db_path: Path):
    """Derive title_full breadcrumb chain and ancestor title columns.

    - title_full: "Hand tools > Spades; Shovels > with teeth" (from main group down)
    - section_title: title of the level-2 ancestor (e.g. "HUMAN NECESSITIES")
    - class_title: title of the level-3 ancestor
    - subclass_title: title of the level-4 ancestor
    """
    print(f"\nStep 8: Deriving title_full and ancestor titles")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Load all entries into memory for fast parent walks
    cur.execute("SELECT symbol, level, parent, title_en FROM ipc")
    lookup = {}
    for symbol, level, parent, title_en in cur.fetchall():
        lookup[symbol] = {
            "level": level,
            "parent": parent,
            "title_en": title_en or "",
        }

    print(f"  Loaded {len(lookup):,} entries for parent walking")

    def build_title_full(symbol: str) -> str:
        """Build breadcrumb from main group (level 5) downward."""
        chain = []
        current = symbol
        while current in lookup:
            entry = lookup[current]
            if entry["level"] < 5:  # stop above main group
                break
            if entry["title_en"]:
                chain.append(entry["title_en"])
            current = entry["parent"]
        chain.reverse()
        return " > ".join(chain) if chain else lookup.get(symbol, {}).get("title_en", "")

    def find_ancestor_title(symbol: str, target_level: int) -> str:
        """Walk up to find ancestor at target_level and return its title."""
        current = symbol
        while current in lookup:
            entry = lookup[current]
            if entry["level"] == target_level:
                return entry["title_en"]
            if entry["level"] < target_level:
                return ""  # overshot
            current = entry["parent"]
        return ""

    updates = []
    for symbol in lookup:
        title_full = build_title_full(symbol)
        section_title = find_ancestor_title(symbol, 2)
        class_title = find_ancestor_title(symbol, 3)
        subclass_title = find_ancestor_title(symbol, 4)
        updates.append((title_full, section_title, class_title, subclass_title, symbol))

    cur.executemany("""
        UPDATE ipc SET
            title_full = ?,
            section_title = ?,
            class_title = ?,
            subclass_title = ?
        WHERE symbol = ?
    """, updates)

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM ipc WHERE title_full IS NOT NULL AND title_full != ''")
    with_full = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ipc WHERE section_title IS NOT NULL AND section_title != ''")
    with_section = cur.fetchone()[0]

    # Samples
    print(f"  Updated {with_full:,} entries with title_full")
    print(f"  Updated {with_section:,} entries with section_title")
    print("  Samples:")
    cur.execute("""
        SELECT symbol_short, title_en, title_full, section_title, class_title, subclass_title
        FROM ipc WHERE level >= 7 LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"    {row[0]:20s} title_full: {(row[2] or '')[:80]}")
        print(f"    {'':20s} section: {(row[3] or '')[:40]} | class: {(row[4] or '')[:40]}")

    conn.close()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Build IPC 2026.01 SQLite database from WIPO release files"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Path to ipc2026.01 data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output SQLite database path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Skip step 1 (scheme XML parsing) and enrich existing database",
    )

    args = parser.parse_args()

    if not args.skip_rebuild:
        # Validate data directory
        scheme_xml = args.data_dir / "ipc_scheme_20260101" / "EN_ipc_scheme_20260101.xml"
        if not scheme_xml.exists():
            print(f"Error: Scheme XML not found: {scheme_xml}")
            sys.exit(1)

        # Step 1: Parse scheme XML
        entries = parse_scheme_xml(scheme_xml)
        create_database(args.output, entries)
    else:
        if not args.output.exists():
            print(f"Error: Database not found: {args.output}")
            sys.exit(1)
        print(f"Skipping rebuild, enriching existing database: {args.output}")

    # Step 2: Cross-check with title list
    enrich_from_title_list(args.output, args.data_dir)

    # Step 3: Add latest_version_date from valid symbols
    enrich_from_valid_symbols(args.output, args.data_dir)

    # Step 4: Build ipc_everused table + introduced_date
    build_everused_table(args.output, args.data_dir)

    # Step 5: Extract definitions into additional_content
    enrich_from_definitions(args.output, args.data_dir)

    # Step 6: Build ipc_catchword table
    build_catchword_table(args.output, args.data_dir)

    # Step 7: Build ipc_concordance table
    build_concordance_table(args.output, args.data_dir)

    # Step 8: Derive title chains and ancestor titles
    derive_title_chains(args.output)

    print(f"\nAll steps complete! Database: {args.output}")
    print(f"  Final size: {args.output.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
