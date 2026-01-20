# MOSS Format Specification v2.0
**Micro Operating Specification Script - Proprietary Format**  
**Date**: 2026-01-07  
**Status**: Design Complete - Implementation Phase

## Overview
MOSS is a proprietary human-readable data format with semantic understanding of manual structure, page addressing, and connection chains. It replaces JSON for technical manual specifications.

---

## 1. Comments - Human Readable Documentation

### Full-Line Comments
```moss
# This is a full-line comment
# Comments start with # and continue to end of line
```

### Inline Comments
```moss
pages: [5, 7, 12]   # ACT numbers for Pattern 1
ACT: 7              # Physical PDF page
INT: 2-1            # Printed page identifier
```

### Comment Rules
1. `#` starts a comment anywhere on a line
2. Everything after `#` to end of line is a comment
3. `#` inside quotes is NOT a comment: `"value # not a comment"`
4. Comments are stripped during parsing (do not affect data)
5. Compiler preserves line structure for error reporting
6. Empty lines and comment-only lines are ignored

### Comment Parsing Algorithm
```python
def parse_line_with_comment(line):
    # Check if # is inside quotes
    in_quotes = False
    quote_char = None
    
    for i, char in enumerate(line):
        if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        elif char == '#' and not in_quotes:
            # Found comment start
            content = line[:i].rstrip()
            comment = line[i+1:].strip()
            return content, comment
    
    # No comment found
    return line, None
```

---

## 2. Header Directives

Every MOSS file starts with header directives using `@` prefix.

### Required Headers

#### @MOSS: Manual Name
```moss
@MOSS:InstallationManual
```
- **Required**: YES (every MOSS file)
- **Purpose**: Identifies which manual/system this file belongs to
- **Format**: `@MOSS:` followed by manual name (no spaces in name)
- **Examples**: `@MOSS:OperatorsManual`, `@MOSS:InstallationWorkflow`

#### @R: Root Path (Index MOSS only)
```moss
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\
```
- **Required**: YES for index MOSS files at workspace root
- **Purpose**: Declares absolute path to page folder container
- **Format**: `@R:` followed by absolute Windows path
- **Used by**: Compiler to resolve ACT references to page folders

### Optional Headers

#### @QR: QR Code (Page MOSS only)
```moss
@QR:QR_12345
```
- **Required**: NO (only for pages with QR codes)
- **Purpose**: Links page to physical QR code identifier
- **Format**: `@QR:` followed by QR code string

### Header Example
```moss
@MOSS:InstallationManual
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\
@QR:QR_PATTERN1_PAGE7

# Headers complete, body starts below
```

---

## 3. Semantic Types - R/ACT/INT/ABS

MOSS understands domain-specific types for manual page addressing.

### R (Root) - Directory Path
```moss
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\
```
- **Type**: Absolute filesystem path
- **Purpose**: Container for all page folders
- **Declared**: In header using `@R:` directive
- **Scope**: File-level (applies to entire MOSS file)

### ACT (Actual) - Physical Page Number
```moss
ACT: 7
```
- **Type**: Positive integer (1, 2, 3, ...)
- **Purpose**: Physical PDF page number (1-based)
- **Usage**: Primary key for page lookup
- **Resolves to**: `{R}/OperatorsManual...Page_7/`
- **Must be unique**: Within a manual (enforced by compiler)

### INT (Internal) - Printed Page ID
```moss
INT: 2-1
INT: A-3
INT: 15
INT: null
```
- **Type**: String or null
- **Format**: 
  - Number: `1`, `2`, `15`
  - Section-Page: `2-1`, `4-3`, `10-5`
  - Appendix: `A-1`, `B-3`, `C-2`
  - Cover pages: `null`
- **Purpose**: Page number printed on document
- **Usage**: How humans reference pages ("turn to page 2-1")
- **Must be unique**: Within a manual (enforced by compiler)

### ABS (Absolute) - Bidirectional Mapping Rule
```moss
# Compiler enforces ABS automatically:
# If ACT:7 → INT:2-1
# Then INT:2-1 → ACT:7 (must exist and be unique)
```
- **Type**: Compiler validation rule (not a data field)
- **Purpose**: Ensures ACT ↔ INT is 1:1 bidirectional
- **Enforced**: At compile time
- **Errors**: 
  - Duplicate ACT values
  - Duplicate INT values
  - Orphaned mappings (ACT without INT or vice versa)

---

## 4. Data Types - Primitives

### Boolean
```moss
enabled: true
disabled: false
```
- **Values**: `true` or `false` (lowercase)
- **Parsed to**: Python `True`/`False`

### Null
```moss
cover_page_int: null
optional_field: null
```
- **Values**: `null` (lowercase)
- **Parsed to**: Python `None`

### Integer
```moss
page_count: 42
ACT: 7
```
- **Format**: Digits only, no quotes
- **Parsed to**: Python `int`

### Float
```moss
version: 1.5
tolerance: 0.001
```
- **Format**: Digits with decimal point
- **Parsed to**: Python `float`

### String
```moss
title: "Installation Manual"
description: 'Single quotes also work'
unquoted_string: Also valid if no special chars
```
- **Format**: 
  - Quoted: `"string"` or `'string'`
  - Unquoted: `value` (if no `:`, `#`, `//`, `||`)
- **Parsed to**: Python `str`
- **Quotes removed**: `"value"` becomes `value`

---

## 5. Data Structures

### Key-Value Pairs
```moss
key: value
title: "Installation Manual"
page_count: 42
enabled: true
```
- **Format**: `key: value`
- **Indentation**: Defines nesting level
- **Whitespace**: Flexible around `:`

### Lists
```moss
pages:
  - 5
  - 7
  - 12

components:
  - Power Supply
  - Control Module
  - Sensor Array
```
- **Format**: `- item` (dash-space-item)
- **Indentation**: Items must be indented under parent key
- **Mixed types**: Allowed

### Nested Objects
```moss
pattern1:
  name: "Safety Checks"
  pages:
    - 5
    - 7
  components:
    power_supply:
      voltage: 24
      current: 2.5
```
- **Indentation**: 2 or 4 spaces (consistent within file)
- **Nesting**: Unlimited depth
- **Mixed**: Objects can contain lists, lists can contain objects

---

## 6. Connection Operators

### // (Chain Operator)
Connects components in sequential order.

```moss
# Simple chain
Power Supply // Control Module // Motor

# With wire specifications
Power Supply (24V OUT) // Control Module (24V IN, CTRL OUT) // Motor (CTRL IN)

# In structured data
connections:
  safety_circuit:
    Power Supply // E-Stop // Safety Relay // Control Module
```

**Compiler behavior**:
- Splits by `//`
- Creates connection chain: A → B → C
- Extracts wire specs from parentheses
- Stores as queryable structure:
  ```python
  {
    "connections": [
      {"from": "Power Supply", "to": "Control Module"},
      {"from": "Control Module", "to": "Motor"}
    ]
  }
  ```

### || (Parallel Operator)
Connects components in parallel (redundant paths).

```moss
# Parallel redundancy
Power Supply // (Safety Relay A || Safety Relay B) // Motor

# Multiple parallel branches
Input // (Path A || Path B || Path C) // Output
```

**Compiler behavior**:
- Groups expressions in parentheses
- Splits by `||`
- Creates multiple parallel chains
- Example: `A // (B || C) // D` creates:
  - A → B → D
  - A → C → D

---

## 7. References and Lookups

### ACT Reference
```moss
# Reference a page by actual number
target_page: ACT(7)
next_page: ACT(12)

# In a list
pages: [ACT(5), ACT(7), ACT(12)]
```

**Compiler resolution**:
- `ACT(7)` → `{R}/OperatorsManual...Page_7/`
- Validates folder exists
- Can load referenced MOSS file

### INT Reference
```moss
# Reference a page by internal ID
user_sees: INT(2-1)
appendix: INT(A-3)

# Requires ABS index lookup
```

**Compiler resolution**:
- `INT(2-1)` → ABS index lookup → `ACT(7)` → folder path
- Requires global ABS index to be built first

---

## 8. Complete Example - Index MOSS

```moss
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

# Installation workflow patterns for operator manual
# Each pattern defines a sequence of pages and connections

pattern1:
  name: "Initial Safety Checks"
  description: "Pre-startup safety verification"
  pages:
    - 5    # INT: 1-1 - Safety overview
    - 7    # INT: 2-1 - E-stop verification
    - 12   # INT: 4-3 - Power verification
  
  connections:
    safety_circuit:
      # Primary safety chain
      Power Supply (24V OUT) // E-Stop (24V IN/OUT) // Safety Relay (COIL) // Control Module (ENABLE IN)
    
    redundancy:
      # Parallel safety relays
      Safety Input // (Relay A || Relay B) // Safety Output

pattern2:
  name: "Power-Up Sequence"
  pages: [12, 15, 18]   # ACT numbers
  
  steps:
    - Verify E-stop released
    - Apply main power
    - Check status LEDs

# Cross-references to page MOSS files
page_index:
  5: INT(1-1)
  7: INT(2-1)
  12: INT(4-3)
  15: INT(5-2)
  18: INT(6-1)
```

---

## 9. Complete Example - Page MOSS

```moss
@MOSS:InstallationManual
@QR:QR_PATTERN1_ESTOP

# Page metadata
ACT: 7              # Physical PDF page 7
INT: 2-1            # Printed as "Page 2-1"

# Page content specification
title: "Emergency Stop Verification"
section: "Safety Checks"
pattern: "Pattern 1"

# Components on this page
components:
  - E-Stop Button
  - Safety Relay
  - Status Indicator
  - Test Button

# Connections shown on page
connections:
  primary_circuit:
    24V Power // E-Stop (NO Contact) // Safety Relay (Coil) // Control Enable

  test_circuit:
    Test Button // Safety Relay (Contacts) // Status LED

# Instructions for operator
steps:
  - Press E-stop to verify it latches
  - Attempt to start system (should fail)
  - Release E-stop by twisting clockwise
  - Verify green LED illuminates
  - Press test button to verify relay drops out

# Related pages
previous_page: ACT(5)    # INT: 1-1
next_page: ACT(12)       # INT: 4-3
see_also:
  - INT(A-2)   # Appendix - E-stop specifications
  - INT(B-1)   # Appendix - Safety relay wiring
```

---

## 10. Indentation Rules

### Consistent Spacing
```moss
# GOOD: 2-space indentation
parent:
  child1: value
  child2:
    - item1
    - item2

# GOOD: 4-space indentation
parent:
    child1: value
    child2:
        - item1
        - item2

# BAD: Mixed indentation
parent:
  child1: value
    child2: value   # Error: inconsistent indent
```

**Rules**:
- Use 2 or 4 spaces per level (consistent within file)
- NO TABS (tabs are parse errors)
- Indentation defines structure
- Child items must be indented more than parent

### List Indentation
```moss
# GOOD: Items aligned under parent
components:
  - Power Supply
  - Control Module

# GOOD: Nested lists
patterns:
  - pattern1:
      pages:
        - 5
        - 7

# BAD: Items not indented
components:
- Power Supply   # Error: must indent under parent
```

---

## 11. Error Handling

### Parse Errors

**Missing Header**
```moss
# ERROR: Missing @MOSS: header
key: value
```
→ `MOSSError: Missing @MOSS: header (required)`

**Invalid Indentation**
```moss
parent:
  child: value
 bad_indent: value   # ERROR: inconsistent indent
```
→ `MOSSError: Line 3: Invalid indentation (expected 0 or 2, got 1)`

**Tab Characters**
```moss
key:→value   # Tab character
```
→ `MOSSError: Line 1: Tab characters not allowed (use spaces)`

### Semantic Errors

**Duplicate ACT**
```moss
# File: Page_7.moss
ACT: 7
INT: 2-1

# File: Page_12.moss
ACT: 7   # ERROR: Already used in Page_7.moss
INT: 4-3
```
→ `MOSSError: ABS violation: ACT 7 defined in multiple files`

**Duplicate INT**
```moss
# File: Page_7.moss
ACT: 7
INT: 2-1

# File: Page_12.moss
ACT: 12
INT: 2-1   # ERROR: Already used in Page_7.moss
```
→ `MOSSError: ABS violation: INT '2-1' defined in multiple files`

**Missing R Declaration**
```moss
# Index MOSS file
@MOSS:InstallationWorkflow
# Missing @R:

pages: [5, 7]   # ERROR: Cannot resolve ACT without R
```
→ `MOSSError: Cannot resolve ACT references: @R: not declared`

**Invalid ACT Reference**
```moss
@MOSS:InstallationWorkflow
@R:C:\QUARTERHILL\RAG Pipeline\installation manual\

pages: [999]   # ERROR: Folder not found
```
→ `MOSSError: ACT(999) references non-existent folder`

---

## 12. Compiler Specification

### Initialization Phase
1. **Scan workspace**: Find all `.moss` files
2. **Categorize files**:
   - Index MOSS (workspace root)
   - Page MOSS (inside R directories)
3. **Parse headers**: Extract `@MOSS:`, `@R:`, `@QR:` from all files
4. **Build directory index**: Map R paths to page folders
5. **Build ABS index**: Create bidirectional ACT ↔ INT mapping
6. **Validate ABS**: Check for duplicates and orphans

### Parse Phase
1. **Read file**: Load lines from `.moss` file
2. **Strip comments**: Process each line:
   - Detect `#` outside quotes
   - Split into content and comment
   - Keep content, discard comment
3. **Parse header**: Extract directives (`@MOSS:`, `@R:`, `@QR:`)
4. **Parse body**: 
   - Indentation-based structure
   - Key-value pairs
   - Lists (- items)
   - Connection operators (//, ||)
   - Type detection (bool, null, int, float, str)
5. **Resolve references**: 
   - `ACT(n)` → folder path
   - `INT(id)` → ABS lookup → ACT → folder path
6. **Return dict**: Python dictionary compatible with `json.load()`

### Validation Phase
1. **ABS rule enforcement**:
   - No duplicate ACT values
   - No duplicate INT values
   - Every ACT has corresponding INT (or INT is null for covers)
   - Every INT (non-null) has corresponding ACT
2. **Reference validation**:
   - All `ACT(n)` references exist in R
   - All `INT(id)` references exist in ABS index
   - All R paths are valid directories
3. **Structure validation**:
   - Consistent indentation
   - Valid data types
   - Proper nesting

### Output Format
```python
{
  "_moss_manual": "InstallationManual",
  "_moss_qr": "QR_12345",          # Optional
  "_moss_r": "C:\\QUARTERHILL\\...",  # If declared
  "ACT": 7,
  "INT": "2-1",
  "key": "value",
  # ... rest of parsed data
}
```

---

## 13. Migration from v1.0

### Changes from v1.0
1. ✅ **Inline comments now supported**: `key: value # comment`
2. ✅ **Semantic types added**: R/ACT/INT/ABS as first-class concepts
3. ✅ **ABS validation**: Compiler enforces bidirectional mapping
4. ✅ **Path resolution**: `@R:` directive and ACT/INT references
5. ✅ **Parallel operator**: `||` for redundant connections
6. ⚠️ **Breaking change**: Comment parsing algorithm changed

### Migration Steps
1. **Add R declaration** to index MOSS files:
   ```moss
   @MOSS:InstallationWorkflow
   @R:C:\QUARTERHILL\RAG Pipeline\installation manual\
   ```

2. **Update inline comments** (now properly supported):
   ```moss
   # v1.0 - broken
   - 7 # INT: 2-1   # This broke the parser
   
   # v2.0 - works
   - 7   # INT: 2-1   # Properly parsed
   ```

3. **Add ACT/INT** to page MOSS files:
   ```moss
   @MOSS:InstallationManual
   ACT: 7
   INT: 2-1
   ```

4. **Test ABS validation**: Run compiler to catch duplicates
5. **Update references**: Use `ACT(n)` or `INT(id)` syntax if needed

---

## 14. Reserved Keywords

### Header Directives
- `@MOSS:` - Manual name (required)
- `@R:` - Root path (required for index MOSS)
- `@QR:` - QR code (optional)

### Semantic Fields
- `ACT` - Actual page number (use in page MOSS)
- `INT` - Internal page ID (use in page MOSS)
- `R` - Root path (use `@R:` in header, not as key)

### Metadata Fields (Generated by Compiler)
- `_moss_manual` - Manual name from `@MOSS:`
- `_moss_qr` - QR code from `@QR:`
- `_moss_r` - Root path from `@R:`
- `_moss_act` - Copy of ACT field
- `_moss_int` - Copy of INT field

### Type Keywords
- `true`, `false` - Boolean values
- `null` - Null value

---

## 15. Best Practices

### Commenting
```moss
# GOOD: Meaningful comments
pages:
  - 5    # INT: 1-1 - Safety overview
  - 7    # INT: 2-1 - E-stop verification

# BAD: Redundant comments
key: value   # This is a value
```

### Naming Conventions
```moss
# Use snake_case for keys
power_supply: value
e_stop_button: value

# Use descriptive names
pattern1_name: "Safety Checks"   # GOOD
p1n: "Safety Checks"             # BAD
```

### Indentation
```moss
# GOOD: Consistent 2-space indent
parent:
  child:
    grandchild: value

# GOOD: Consistent 4-space indent
parent:
    child:
        grandchild: value
```

### Connection Chains
```moss
# GOOD: Readable with line breaks
connections:
  primary:
    Power Supply // 
    E-Stop // 
    Safety Relay // 
    Control Module

# GOOD: Compact for simple chains
safety: E-Stop // Relay // Controller

# BAD: Unreadable long line
connections: Power Supply (24V 2A OUT FUSED) // E-Stop Button (NC Contact Rated 24V 5A) // Safety Relay (Coil 24VDC Contact 250VAC 5A) // Control Module (Enable Input Active High 24V)
```

---

## 16. Syntax Summary

| Feature | Syntax | Example |
|---------|--------|---------|
| Full-line comment | `# comment` | `# This is a comment` |
| Inline comment | `value # comment` | `key: value # inline` |
| Header directive | `@DIRECTIVE:value` | `@MOSS:ManualName` |
| Key-value | `key: value` | `title: "Manual"` |
| List | `- item` | `- Power Supply` |
| Boolean | `true` / `false` | `enabled: true` |
| Null | `null` | `cover_int: null` |
| Integer | `123` | `ACT: 7` |
| Float | `12.34` | `version: 1.5` |
| String | `"text"` or `text` | `name: "Manual"` |
| Connection chain | `A // B // C` | `Supply // Relay // Motor` |
| Parallel | `A \|\| B` | `(Relay A \|\| Relay B)` |
| ACT reference | `ACT(n)` | `page: ACT(7)` |
| INT reference | `INT(id)` | `page: INT(2-1)` |

---

## 17. Formal Grammar (EBNF-like)

```ebnf
file          = header+ body

header        = '@MOSS:' identifier newline
              | '@R:' path newline
              | '@QR:' identifier newline

body          = (statement | comment | blank)*

statement     = key ':' value
              | '-' value
              | connection

key           = identifier

value         = boolean | null | number | string | list | object | reference
              | connection_expr

boolean       = 'true' | 'false'
null          = 'null'
number        = integer | float
string        = quoted_string | unquoted_string
list          = '- ' value (newline '- ' value)*
object        = key ':' newline (indent statement)+

reference     = 'ACT(' integer ')'
              | 'INT(' string ')'

connection    = component ('//' component)+
component     = identifier ('(' wire_spec ')')?
parallel      = '(' component ('||' component)+ ')'

comment       = '#' [^newline]*
blank         = newline

identifier    = [a-zA-Z_][a-zA-Z0-9_]*
path          = [^\n]+
integer       = [0-9]+
float         = [0-9]+ '.' [0-9]+
```

---

## 18. File Extension and MIME Type

- **Extension**: `.moss`
- **MIME type**: `text/x-moss` (proposed)
- **Character encoding**: UTF-8
- **Line endings**: CRLF (Windows) or LF (Unix) - both accepted
- **File size**: No hard limit (sub-millisecond parsing expected for <100KB files)

---

## 19. Tooling Recommendations

### Syntax Highlighting
- Comments: Gray/green
- Keywords (`true`, `false`, `null`): Blue
- Strings: Red/orange
- Numbers: Purple
- Headers (`@MOSS:`): Bold blue
- Semantic types (`ACT`, `INT`, `R`): Bold green
- Operators (`//`, `||`): Yellow

### Linting
- Validate indentation consistency
- Check for tab characters
- Verify header presence
- Flag potentially ambiguous references

### Formatting
- Auto-indent nested structures
- Align list items
- Format connection chains for readability

---

## 20. Version History

### v2.0 (2026-01-07) - Current
- ✅ Inline comment support
- ✅ Semantic types (R/ACT/INT/ABS)
- ✅ Path resolution system
- ✅ ABS validation
- ✅ Parallel operator (`||`)
- ✅ ACT/INT reference syntax

### v1.0 (Previous)
- Basic YAML-like syntax
- Connection chains (`//`)
- Header directives
- ❌ No inline comments
- ❌ No semantic types
- ❌ No ABS validation

---

**PROPRIETARY**: This format specification is proprietary to QUARTERHILL RAG Pipeline. All rights reserved. MOSS is designed for technical manual specification and documentation with semantic understanding of manual structure and page addressing.
