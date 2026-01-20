# Integrating MOSS Format into Your Extractor

## Overview
Your PDF extractor currently saves data as JSON. This guide shows how to modify it to save as MOSS format instead, with manual `//` connection support for schematics.

## Files You Have
- `moss.py` - MOSS compiler (reads .moss files → Python dict)
- `moss_writer.py` - MOSS writer (writes Python dict → .moss files)

## Integration Steps

### 1. Import MOSS Writer in Your Extractor

```python
from moss_writer import MOSSWriter

# At the start of your extraction code
moss_writer = MOSSWriter()
```

### 2. Replace JSON Save with MOSS Save

**Before (JSON):**
```python
# Your current code probably looks like:
import json

page_data = {
    'page_number': page_num,
    'page_dir': page_folder,
    'text_file': text_file_path,
    'figures': figure_list,
    # ... more data
}

# Save to JSON
with open(f'{page_folder}/metadata.json', 'w') as f:
    json.dump(page_data, f, indent=2)
```

**After (MOSS):**
```python
# Replace with:
moss_file = moss_writer.write_page_data(
    output_dir=page_folder,
    page_number=page_num,
    manual_name="OperatorsManual3902-00213-00108_G-1",  # Your PDF name
    act=actual_pdf_page,  # Actual PDF page number
    int_id=f"P{page_num}",  # Internal sequential ID
    resource_folder=os.path.basename(page_folder),
    text_file=os.path.basename(text_file_path),
    page_screenshot="Page {}.png".format(page_num),
    figures=figures_list,  # List of dicts (see below)
    all_files=all_extracted_files,  # List of filenames
    extracted_text=True,
    extracted_images=True,
    qr_code_path=f"qr_codes/{manual_name}.png"  # Optional
)

print(f"✓ Created MOSS file: {moss_file}")
```

### 3. Figure Data Structure

Your `figures_list` should be a list of dictionaries:

```python
figures_list = [
    {
        'filename': 'Figure_11_1.png',
        'type': 'Figure',  # or 'Table', 'Diagram', 'Schematic'
        'index': 1,
        'description': 'System Overview'  # From GPT-4o Vision
    },
    {
        'filename': 'Figure_11_2.png',
        'type': 'Table',
        'index': 2,
        'description': 'Component Specifications'
    }
]
```

### 4. Full Example Integration

```python
"""
Your PDF Extractor - Modified for MOSS Output
"""
import os
from pathlib import Path
from moss_writer import MOSSWriter

def extract_pdf_page(pdf_path, page_num, output_base_dir, manual_name):
    """Extract single page and save as MOSS"""
    
    # Your existing extraction logic
    page_folder = Path(output_base_dir) / f"{manual_name}_Page_{page_num}"
    page_folder.mkdir(exist_ok=True)
    
    # Extract text (your existing code)
    text_content = extract_text_from_page(pdf_path, page_num)
    text_file = page_folder / f"{manual_name}_Page_{page_num}_text.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    # Extract images (your existing code)
    extracted_images = extract_images_from_page(pdf_path, page_num, page_folder)
    
    # Use GPT-4o Vision to name images (your existing code)
    figures = []
    for i, img_path in enumerate(extracted_images, 1):
        # Your Vision API call
        description = get_image_description_from_gpt(img_path, text_content)
        
        figures.append({
            'filename': os.path.basename(img_path),
            'type': detect_image_type(description),  # Figure/Table/Diagram
            'index': i,
            'description': description
        })
    
    # Get all files in folder
    all_files = [f.name for f in page_folder.iterdir() if f.is_file()]
    
    # Save as MOSS instead of JSON
    moss_writer = MOSSWriter()
    moss_file = moss_writer.write_page_data(
        output_dir=str(page_folder),
        page_number=page_num,
        manual_name=manual_name,
        act=page_num,  # Actual PDF page
        int_id=f"P{page_num}",
        resource_folder=page_folder.name,
        text_file=text_file.name,
        page_screenshot=f"Page {page_num}.png",
        figures=figures,
        all_files=all_files,
        extracted_text=True,
        extracted_images=len(extracted_images) > 0,
        qr_code_path=f"qr_codes/{manual_name}.png"
    )
    
    return moss_file


def extract_full_pdf(pdf_path, manual_name, output_dir):
    """Extract entire PDF"""
    pdf = open_pdf(pdf_path)  # Your PDF opening code
    
    for page_num in range(1, pdf.page_count + 1):
        print(f"Processing page {page_num}...")
        moss_file = extract_pdf_page(pdf_path, page_num, output_dir, manual_name)
        print(f"  ✓ {moss_file}")
    
    print(f"\n✓ Complete! All pages saved as .moss files")
    print(f"  Location: {output_dir}")
    print(f"  You can now manually add // connections to schematic pages")


if __name__ == "__main__":
    extract_full_pdf(
        pdf_path=r"C:\path\to\manual.pdf",
        manual_name="OperatorsManual3902-00213-00108_G-1",
        output_dir=r"C:\QUARTERHILL\RAG Pipeline\installation manual"
    )
```

## Manual Connection Addition

After extraction, for schematic pages, you manually edit the .moss file to add connections:

### Before:
```moss
@MOSS:OperatorsManual3902-00213-00108_G-1

ACT: 15
INT: P15
R: OperatorsManual3902-00213-00108_G-1_Page_15
pdf_name: OperatorsManual3902-00213-00108_G-1

Figure1:
  filename: Illuminator_Wiring_Diagram.png
  type: Schematic
  index: 1
  description: Illuminator power supply wiring to 3 units
```

### After (add connections):
```moss
@MOSS:OperatorsManual3902-00213-00108_G-1

ACT: 15
INT: P15
R: OperatorsManual3902-00213-00108_G-1_Page_15
pdf_name: OperatorsManual3902-00213-00108_G-1

# System connections (manually added)
AC Power Input (L/N/Ground) // ILLUMINATOR POWER SUPPLY 3401-00291-001
ILLUMINATOR POWER SUPPLY 3401-00291-001 Output 1 (+/- RED/BLK) // ILLUMINATOR Unit 1
ILLUMINATOR POWER SUPPLY 3401-00291-001 Output 2 (+/- RED/BLK) // ILLUMINATOR Unit 2
ILLUMINATOR POWER SUPPLY 3401-00291-001 Output 3 (+/- RED/BLK) // ILLUMINATOR Unit 3

Figure1:
  filename: Illuminator_Wiring_Diagram.png
  type: Schematic
  index: 1
  description: Illuminator power supply wiring to 3 units
  connections:
    - AC Input (L/N/Ground) // Power Supply
    - Power Supply Output 1 (+/- RED/BLK) // Unit 1
    - Power Supply Output 2 (+/- RED/BLK) // Unit 2
    - Power Supply Output 3 (+/- RED/BLK) // Unit 3
```

## Reading MOSS Files Back

In your RAG system, replace `json.load()` with `moss.load()`:

**Before:**
```python
import json

with open('page_metadata.json', 'r') as f:
    data = json.load(f)
```

**After:**
```python
import moss

# Simple drop-in replacement
data = moss.load('page_metadata.moss')

# With validation
data = moss.load('page_metadata.moss', expected_manual='OperatorsManual3902-00213-00108_G-1')

# Now data is a Python dict, exactly like JSON
print(data['ACT'])  # 15
print(data['connections'])  # List of connection objects
```

## Connection Query Example

```python
import moss

# Load schematic page
data = moss.load('schematic_page.moss')

# Query connections
if 'connections' in data:
    print(f"Found {len(data['connections'])} connections")
    
    # Find what connects to power supply
    for conn in data['connections']:
        if 'POWER SUPPLY' in conn['to']:
            print(f"  {conn['from']} → {conn['to']}")
            if 'wiring' in conn:
                print(f"    Wiring: {conn['wiring']}")

# Output:
# Found 4 connections
#   AC Power Input → ILLUMINATOR POWER SUPPLY 3401-00291-001
#     Wiring: L/N/Ground
#   ILLUMINATOR POWER SUPPLY 3401-00291-001 Output 1 → ILLUMINATOR Unit 1
#     Wiring: +/- RED/BLK
```

## Benefits

✅ **Human-readable** - Easy to edit manually  
✅ **Fast parsing** - No JSON overhead  
✅ **Connection tracking** - `//` operator creates queryable graph  
✅ **Validation** - `@MOSS:` header prevents file mix-ups  
✅ **QR integration** - Link physical manuals to digital files  
✅ **Drop-in replacement** - Works with existing dict-based code  

## Migration Plan

1. **Keep JSON temporarily** - Run both formats in parallel
2. **Test MOSS output** - Verify all data preserved
3. **Add connections manually** - Edit schematic .moss files
4. **Update RAG code** - Replace `json.load()` with `moss.load()`
5. **Delete JSON** - Once MOSS validated

## Extractor Checklist

When modifying your extractor:

- [ ] Import `from moss_writer import MOSSWriter`
- [ ] Create writer instance: `moss_writer = MOSSWriter()`
- [ ] Replace JSON save with `moss_writer.write_page_data()`
- [ ] Pass all required parameters (see Full Example above)
- [ ] Verify .moss files created in each page folder
- [ ] Test loading with `moss.load()`
- [ ] Manually add `//` connections to schematic pages
- [ ] Update RAG pipeline to use `moss.load()`

---

**You now have:**
- ✅ `moss.py` - Compiler (reads .moss → dict)
- ✅ `moss_writer.py` - Writer (dict → .moss)
- ✅ Example MOSS files (converted from your JSON)
- ✅ Integration guide (this file)

**Next step:** Modify your extractor code to call `moss_writer.write_page_data()` instead of `json.dump()`
