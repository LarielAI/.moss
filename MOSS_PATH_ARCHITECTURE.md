# MOSS Path Architecture Specification
**Version**: 2.0  
**Date**: 2026-01-07  
**Status**: Design Phase - Proprietary Format

## Purpose
Define how MOSS files navigate, reference, and resolve paths using the R/ACT/INT/ABS semantic system.

---

## Core Concepts

### 1. R (Root) - The Foundation
**R** is the absolute path to the container directory holding all page folders.

```moss
@MOSS:InstallationManual
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

# R is declared once per MOSS file
# All relative paths resolve from R
```

**Rules**:
- R must be an absolute path
- R points to a directory containing page folders
- R is declared in header using `@R:` directive
- Index MOSS files (workspace root) can reference page MOSS files via R

### 2. ACT (Actual) - Physical Page Numbers
**ACT** represents the actual PDF page number (1-based sequential).

```moss
ACT: 7
# This is physical page 7 in the PDF
```

**Rules**:
- ACT is always an integer (1, 2, 3, ...)
- ACT maps to a physical page folder: `{R}/...Page_{ACT}/`
- ACT must be unique within a manual
- ACT is the primary key for page lookup

### 3. INT (Internal) - Printed Page Identifiers
**INT** represents the page number printed on the document.

```moss
INT: 2-1
# This page is labeled "2-1" in the manual
```

**Rules**:
- INT can be: number (1, 2, 3), section-page (2-1, 4-3), appendix (A-1, B-3), or null
- INT must be unique within a manual
- INT is the human-readable reference
- INT is how users refer to pages ("turn to page 2-1")

### 4. ABS (Absolute) - Bidirectional Mapping
**ABS** is the compiler rule: ACT↔INT must be 1:1 bidirectional.

```moss
# If ACT:7 → INT:2-1
# Then INT:2-1 → ACT:7 (must be unique)
# Compiler validates ABS rule automatically
```

**Rules**:
- For every ACT→INT mapping, reverse INT→ACT must exist
- ABS violations are compile-time errors
- Compiler maintains bidirectional index
- No ACT can map to multiple INTs
- No INT can map to multiple ACTs

---

## Path Resolution Rules

### Directory Structure
```
C:\QUARTERHILL\RAG Pipeline\                    ← Workspace Root
├── installation_workflow.moss                  ← Index MOSS (workspace)
├── page_mapping.moss                           ← Index MOSS (workspace)
├── appendices.moss                             ← Index MOSS (workspace)
└── installation manual\                        ← R (Root)
    ├── OperatorsManual...Page_1\               ← ACT:1 folder
    │   └── OperatorsManual...Page_1.moss       ← Page MOSS
    ├── OperatorsManual...Page_5\               ← ACT:5 folder
    │   └── OperatorsManual...Page_5.moss       ← Page MOSS
    ├── OperatorsManual...Page_7\               ← ACT:7 folder
    │   └── OperatorsManual...Page_7.moss       ← Page MOSS (INT:2-1)
    └── ...
```

### Resolution Order

**1. Declare R in Header**
```moss
@MOSS:InstallationManual
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\
```

**2. Resolve ACT to Folder**
```moss
ACT: 7
# Compiler resolves to: {R}/OperatorsManual...Page_7/
```

**3. Map ACT ↔ INT (ABS)**
```moss
ACT: 7
INT: 2-1
# Compiler creates bidirectional index:
# ACT[7] → INT["2-1"]
# INT["2-1"] → ACT[7]
```

**4. Cross-File References**
```moss
# In installation_workflow.moss (workspace root):
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

pages:
  - 7   # References ACT:7, compiler resolves to R/...Page_7/

# In OperatorsManual...Page_7.moss (inside R):
@MOSS:InstallationManual
@QR:QR_12345
ACT: 7
INT: 2-1
```

---

## Path Types

### Absolute Paths
```moss
R: C:\QUARTERHILL\RAG Pipeline\installation manual\
# Full Windows path
```

### R-Relative Paths
```moss
# Reference a page by ACT from any MOSS file:
page: ACT(7)
# Compiler resolves: {R}/OperatorsManual...Page_7/
```

### INT Lookups
```moss
# Reference a page by INT (requires ABS index):
page: INT(2-1)
# Compiler looks up: INT["2-1"] → ACT[7] → {R}/...Page_7/
```

---

## Cross-File Navigation

### Index MOSS → Page MOSS
```moss
# installation_workflow.moss (workspace root)
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

workflow:
  pattern1:
    pages: [5, 7, 12]   # ACT numbers
    # Compiler resolves each to: {R}/...Page_{ACT}/...Page_{ACT}.moss
```

### Page MOSS → Index MOSS
```moss
# OperatorsManual...Page_7.moss (inside R)
@MOSS:InstallationManual
ACT: 7
INT: 2-1

workflow_ref: Pattern1
# Compiler knows this page is referenced by installation_workflow.moss
```

### Page MOSS → Page MOSS
```moss
# OperatorsManual...Page_7.moss
@MOSS:InstallationManual
ACT: 7
INT: 2-1

next_page: ACT(12)
# Compiler resolves: {R}/...Page_12/...Page_12.moss

previous_page: INT(1-1)
# Compiler looks up: INT["1-1"] → ACT[5] → {R}/...Page_5/
```

---

## Compiler Responsibilities

### 1. Path Resolution
- Parse `@R:` directive from header
- Build absolute paths for all ACT references
- Validate folder existence: `{R}/...Page_{ACT}/`
- Locate page MOSS files: `{R}/...Page_{ACT}/...Page_{ACT}.moss`

### 2. ABS Index Building
- Scan all page MOSS files in R
- Extract ACT and INT from each file
- Build bidirectional index:
  ```python
  act_to_int = {7: "2-1", 5: "1-1", 12: "4-3", ...}
  int_to_act = {"2-1": 7, "1-1": 5, "4-3": 12, ...}
  ```
- Validate ABS rule: no duplicates, full bidirectional

### 3. ABS Validation
- Check for ACT duplicates (error)
- Check for INT duplicates (error)
- Verify bidirectional mapping (ACT→INT and INT→ACT)
- Report violations as compile-time errors

### 4. Reference Resolution
- `ACT(7)` → direct folder lookup via R
- `INT(2-1)` → ABS index lookup → ACT → folder lookup
- Connection chains across files: `ACT(5) // ACT(7) // ACT(12)`

---

## MOSS File Types

### Index MOSS (Workspace Root)
**Location**: `C:\QUARTERHILL\RAG Pipeline\*.moss`  
**Purpose**: Cross-manual indexes, workflows, mappings  
**R Usage**: Declares R to reference page MOSS files

```moss
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

pattern1:
  pages: [5, 7, 12]   # ACT references to page MOSS files
```

### Page MOSS (Inside R)
**Location**: `{R}/...Page_{ACT}/...Page_{ACT}.moss`  
**Purpose**: Individual page specifications  
**R Usage**: Inherits R from directory structure

```moss
@MOSS:InstallationManual
@QR:QR_12345
ACT: 7
INT: 2-1

components:
  - Power Supply Board
  - Control Module
```

---

## Error Handling

### Missing R Declaration
```moss
# ERROR: Index MOSS file must declare @R: to reference pages
@MOSS:InstallationWorkflow
# Missing @R:

pages: [5, 7]   # Compiler error: Cannot resolve ACT without R
```

### ABS Violation - Duplicate ACT
```moss
# Page_7.moss
ACT: 7
INT: 2-1

# Page_12.moss  
ACT: 7   # ERROR: ACT:7 already exists in Page_7.moss
INT: 4-3
```

### ABS Violation - Duplicate INT
```moss
# Page_7.moss
ACT: 7
INT: 2-1

# Page_12.moss
ACT: 12
INT: 2-1   # ERROR: INT:2-1 already exists in Page_7.moss
```

### Invalid ACT Reference
```moss
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

pages: [999]   # ERROR: ACT:999 folder not found in R
```

### Invalid INT Reference
```moss
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

page: INT(99-99)   # ERROR: INT:99-99 not found in ABS index
```

---

## Implementation Notes

### Compiler Initialization
1. Parse all MOSS files in workspace
2. Identify index MOSS (workspace root) vs page MOSS (inside R)
3. Extract R declarations from index MOSS files
4. Scan R directories for page folders
5. Build global ABS index (ACT↔INT bidirectional map)
6. Validate ABS rules (no duplicates, full bidirectional)

### Load-Time Resolution
1. When loading index MOSS: resolve `@R:` to absolute path
2. When encountering ACT reference: resolve `{R}/...Page_{ACT}/`
3. When encountering INT reference: lookup ABS index → ACT → folder
4. When parsing connections: resolve all node references

### Cross-File Linking
- Index MOSS can reference multiple page MOSS files via ACT list
- Page MOSS can reference other pages via ACT() or INT()
- Connection chains can span multiple pages: `ACT(5) // ACT(7) // ACT(12)`

---

## Path Syntax Summary

| Syntax | Meaning | Example | Resolution |
|--------|---------|---------|------------|
| `@R:` | Root path declaration | `@R:C:\...\installation manual\` | Header directive |
| `ACT: n` | Actual page number | `ACT: 7` | Maps to page folder |
| `INT: id` | Internal page ID | `INT: 2-1` | Human-readable reference |
| `ACT(n)` | Reference by actual | `ACT(7)` | `{R}/...Page_7/` |
| `INT(id)` | Reference by internal | `INT(2-1)` | ABS lookup → ACT → folder |
| `ABS` | Bidirectional rule | automatic | Compiler validates |

---

## Next Steps

1. ✅ **Path Architecture Defined** (this document)
2. ⏳ **Define MOSS Format Specification v2.0** (syntax, operators, types)
3. ⏳ **Implement Compiler** (moss.py rewrite with R/ACT/INT/ABS)
4. ⏳ **Add Inline Comment Support** (parse # properly)
5. ⏳ **Add || Parallel Operator** (connection chains)
6. ⏳ **Build ABS Validation** (enforce bidirectional mapping)
7. ⏳ **Test with Existing Files** (47+ MOSS files)
8. ⏳ **Migrate Format** (update all files to v2.0)

---

**PROPRIETARY**: This path architecture is proprietary to QUARTERHILL RAG Pipeline MOSS format. All rights reserved.
