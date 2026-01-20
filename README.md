# MOSS - Micro Operating Specification Script

A lightweight, human-readable structured data format designed for technical documentation, RAG pipelines, and semantic data extraction.

## What is MOSS?

MOSS is a modern alternative to JSON that prioritizes readability while maintaining strict semantic structure. It supports inline comments, connection mapping, and hierarchical data organization—perfect for technical specs, documentation, and machine learning training data.

### Key Features

- **Readable Syntax** - YAML-like structure with cleaner semantics
- **Semantic Types** - Built-in support for different data categories (R, ACT, INT, ABS)
- **Connection Mapping** - Define relationships between data elements with `//` connections
- **Inline Comments** - Full comment support with `#`
- **Python Integration** - Drop-in replacement for `json.load()`

## Quick Example

```moss
@MOSS:example_system
@R:C:\data\resources\

devices:
  device_001:
    name: Thermal Monitor
    status: active
    temperature: 98.6
    alert_threshold: 105.0
    manual_reference: installation_guide.moss // devices:device_001:alerts
    type: INT
```

## Installation

1. Clone this repository
2. Copy `moss.py` to your project
3. Import and use:

```python
from moss import MOSSCompiler

# Read MOSS file
compiler = MOSSCompiler()
data = compiler.load('config.moss')

# Access data like a dictionary
print(data['devices']['device_001']['name'])
```

## Files

- **moss.py** - Core compiler (parser and reader)
- **moss_writer.py** - Writer for generating .moss files from Python dictionaries
- **examples/** - Sample MOSS files and use cases
- **MOSS_FORMAT_SPECIFICATION_v2.md** - Complete format specification
- **MOSS_INTEGRATION_GUIDE.md** - Integration examples and best practices

## Usage Examples

### Reading MOSS Files

```python
from moss import MOSSCompiler

compiler = MOSSCompiler()
data = compiler.load('data.moss')
```

### Writing MOSS Files

```python
from moss_writer import MOSSWriter

writer = MOSSWriter()
writer.write_page_data(
    output_dir='./output',
    page_number=1,
    manual_name='MyManual',
    text_file='page_text.txt'
)
```

### Connection Mapping

Define relationships between data elements:

```moss
section_1:
  item_a: "Primary Information"
  item_b: "Related Reference" // section_2:subsection:target

section_2:
  subsection:
    target: "Can be queried from item_b"
```

## Format Specification

For detailed syntax rules, semantic types, and advanced features, see [MOSS_FORMAT_SPECIFICATION_v2.md](MOSS_FORMAT_SPECIFICATION_v2.md).

## Integration Guide

To integrate MOSS into your existing projects, see [MOSS_INTEGRATION_GUIDE.md](MOSS_INTEGRATION_GUIDE.md) for:
- Modifying data extractors
- Batch conversion workflows
- Connection editing workflows

## Testing

The project includes comprehensive unit tests covering:
- Basic key-value parsing
- Quoted strings and escape sequences
- Nested structures (objects and lists)
- Mixed nested data (objects containing lists and vice versa)
- Connection/wiring syntax
- Header validation
- Edge cases and error handling

Run tests with:
```bash
python -m unittest test_moss
```

**Test Coverage:** 20 tests, all passing ✓

## Known Improvements in v2.0

- **Escape sequence support** - Properly handles `\"`, `\'`, `\n`, `\t`
- **Better list-of-objects parsing** - Correctly handles objects as list items
- **Robust indentation parsing** - More reliable nested structure handling
- **Comprehensive validation** - Better error messages and edge case handling

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit pull requests or open issues.
