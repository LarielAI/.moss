"""
MOSS v2.0 - Micro Operating Specification Script
Proprietary format for QUARTERHILL RAG Pipeline

Features:
- Inline comments support (#)
- R/ACT/INT/ABS semantic types
- Connection chain parsing (//)
- Path resolution via @R: header
- Backward compatible interface
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List


class MOSSError(Exception):
    """Base exception for MOSS parsing errors"""
    pass


class MOSSCompiler:
    """MOSS file parser and compiler"""
    
    def __init__(self):
        self.connection_pattern = re.compile(r'(.+?)\s*//\s*(.+)')
        self.wire_spec_pattern = re.compile(r'\(([^)]+)\)')
    
    def _strip_comment(self, line: str) -> tuple:
        """Strip inline comment from line, respecting quotes. Returns: (content, comment)"""
        in_quotes = False
        quote_char = None
        
        for i, char in enumerate(line):
            # Handle quote tracking
            if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            # Found comment start outside quotes
            elif char == '#' and not in_quotes:
                content = line[:i].rstrip()
                comment = line[i+1:].strip()
                return content, comment
        
        # No comment found
        return line, None
        
    def load(self, filepath: str, expected_manual: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and compile a MOSS file to Python dict
        
        Args:
            filepath: Path to .moss file
            expected_manual: Optional manual name for validation
            
        Returns:
            Python dictionary (compatible with JSON structure)
            
        Raises:
            MOSSError: If file invalid or manual mismatch
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise MOSSError(f"File not found: {filepath}")
        
        if not filepath.suffix == '.moss':
            raise MOSSError(f"Not a MOSS file: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            raise MOSSError("Empty MOSS file")
        
        # Parse header (v2.0 supports @MOSS:, @R:, @QR:)
        moss_header, qr_header, r_header = None, None, None
        start_line = 0
        
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            stripped, _ = self._strip_comment(line)
            stripped = stripped.strip()
            
            if stripped.startswith('@MOSS:'):
                moss_header = stripped[6:].strip()
                start_line = max(start_line, i + 1)
            elif stripped.startswith('@QR:'):
                qr_header = stripped[4:].strip()
                start_line = max(start_line, i + 1)
            elif stripped.startswith('@R:'):
                r_header = stripped[3:].strip()
                start_line = max(start_line, i + 1)
        
        if not moss_header:
            raise MOSSError("Missing @MOSS: header (required)")
        
        # Validate manual name if expected
        if expected_manual and moss_header != expected_manual:
            raise MOSSError(
                f"Manual mismatch: Expected '{expected_manual}', "
                f"got '{moss_header}'"
            )
        
        # Parse body
        data = self._parse_lines(lines[start_line:])
        
        # Add metadata (v2.0 includes R path)
        data['_moss_manual'] = moss_header
        if qr_header:
            data['_moss_qr'] = qr_header
        if r_header:
            data['_moss_r'] = r_header
        
        return data
    
    def _parse_lines(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MOSS body lines into dict structure"""
        root = {}
        stack = [(root, -1)]  # (current_container, indent_level)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Strip inline comment first
            content, comment = self._strip_comment(line)
            
            # Skip empty lines and comment-only lines
            if not content.strip():
                i += 1
                continue
            
            # Get indentation level
            indent = len(content) - len(content.lstrip())
            content = content.strip()
            
            # Pop stack to correct indentation level
            while len(stack) > 1 and stack[-1][1] >= indent:
                stack.pop()
            
            current_container, current_indent = stack[-1]
            
            # Handle connection operator
            if '//' in content and not content.startswith('- '):
                if isinstance(current_container, dict):
                    self._parse_connection(content, current_container)
                i += 1
                continue
            
            # Handle list item
            if content.startswith('- '):
                list_content = content[2:].strip()
                
                # We need to add to the list that's at the current container level
                if isinstance(current_container, list):
                    # We're already in a list context
                    # Check if this is a simple value or object
                    if ':' in list_content:
                        # Object item - create dict and add to list
                        obj = {}
                        key, value = list_content.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if value:
                            obj[key] = self._parse_value(value)
                        else:
                            # Empty value - might have nested content
                            obj[key] = {}
                        current_container.append(obj)
                        stack.append((obj, indent))
                    else:
                        # Simple value
                        current_container.append(self._parse_value(list_content))
                elif isinstance(current_container, dict):
                    # Adding to a list referenced by last key
                    if current_container:
                        last_key = list(current_container.keys())[-1]
                        if isinstance(current_container[last_key], list):
                            list_ref = current_container[last_key]
                            if ':' in list_content:
                                # Object item
                                obj = {}
                                key, value = list_content.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                if value:
                                    obj[key] = self._parse_value(value)
                                else:
                                    obj[key] = {}
                                list_ref.append(obj)
                                stack.append((obj, indent))
                            else:
                                list_ref.append(self._parse_value(list_content))
                
                i += 1
                continue
            
            # Handle key:value pairs
            if ':' in content:
                key, value = content.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if not value:
                    # Check if next line indicates list or object
                    is_list = False
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        next_content, _ = self._strip_comment(next_line)
                        next_stripped = next_content.strip()
                        
                        if next_stripped:
                            next_indent = len(next_content) - len(next_content.lstrip())
                            if next_indent <= indent:
                                break
                            if next_stripped.startswith('- '):
                                is_list = True
                            break
                        j += 1
                    
                    if is_list:
                        new_list = []
                        if isinstance(current_container, dict):
                            current_container[key] = new_list
                            stack.append((new_list, indent))
                    else:
                        new_dict = {}
                        if isinstance(current_container, dict):
                            current_container[key] = new_dict
                            stack.append((new_dict, indent))
                else:
                    # Has value
                    if isinstance(current_container, dict):
                        current_container[key] = self._parse_value(value)
                    elif isinstance(current_container, list):
                        # Shouldn't happen in well-formed MOSS
                        pass
            
            i += 1
        
        return root
    
    def _parse_connection(self, line: str, current_dict: Dict):
        """Parse // connection operator into structured data"""
        # Initialize connections list if needed
        if 'connections' not in current_dict:
            current_dict['connections'] = []
        
        # Split by //
        parts = [p.strip() for p in line.split('//')]
        
        for i in range(len(parts) - 1):
            from_comp = parts[i]
            to_comp = parts[i + 1]
            
            # Extract wire specs from parentheses
            from_wiring = self._extract_wire_spec(from_comp)
            to_wiring = self._extract_wire_spec(to_comp)
            
            # Clean component names (remove wire specs)
            from_clean = self.wire_spec_pattern.sub('', from_comp).strip()
            to_clean = self.wire_spec_pattern.sub('', to_comp).strip()
            
            connection = {
                'from': from_clean,
                'to': to_clean
            }
            
            # Add wiring info if present
            if from_wiring:
                connection['from_wiring'] = from_wiring
            if to_wiring:
                connection['to_wiring'] = to_wiring
            
            # Combine wiring specs
            wiring_spec = from_wiring or to_wiring
            if wiring_spec:
                connection['wiring'] = wiring_spec
            
            current_dict['connections'].append(connection)
    
    def _extract_wire_spec(self, text: str) -> Optional[str]:
        """Extract wire specification from parentheses"""
        match = self.wire_spec_pattern.search(text)
        return match.group(1) if match else None
    
    def _parse_value(self, value: str) -> Any:
        """Parse value to appropriate Python type"""
        value = value.strip()
        
        # Boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        
        # None/null
        if value.lower() in ('null', 'none'):
            return None
        
        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # String (remove quotes if present and handle escape sequences)
        if value.startswith('"') and value.endswith('"'):
            result = value[1:-1]
            # Handle escape sequences
            result = result.replace('\\"', '"').replace("\\'", "'")
            result = result.replace('\\n', '\n').replace('\\t', '\t')
            result = result.replace('\\\\', '\\')
            return result
        if value.startswith("'") and value.endswith("'"):
            result = value[1:-1]
            # Handle escape sequences
            result = result.replace('\\"', '"').replace("\\'", "'")
            result = result.replace('\\n', '\n').replace('\\t', '\t')
            result = result.replace('\\\\', '\\')
            return result
        
        return value


# Module-level convenience function (drop-in for json.load)
_compiler = MOSSCompiler()

def load(filepath: str, expected_manual: Optional[str] = None) -> Dict[str, Any]:
    """
    Load MOSS file (drop-in replacement for json.load)
    
    Usage:
        import moss
        data = moss.load('schematic.moss')
        # or with validation
        data = moss.load('schematic.moss', expected_manual='OperatorsManual')
    """
    return _compiler.load(filepath, expected_manual)


if __name__ == "__main__":
    # Test with example file
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = r"C:\QUARTERHILL\RAG Pipeline\installation manual\schematic_illuminator_example.moss"
    
    print(f"Testing MOSS compiler with: {test_file}\n")
    print("="*80)
    
    try:
        data = load(test_file)
        
        print("✓ MOSS file compiled successfully!\n")
        print(f"Manual: {data.get('_moss_manual')}")
        print(f"QR Code: {data.get('_moss_qr')}")
        
        if 'connections' in data:
            print(f"\nConnections found: {len(data['connections'])}")
            print("\nFirst 3 connections:")
            for i, conn in enumerate(data['connections'][:3], 1):
                print(f"  {i}. {conn['from']} → {conn['to']}")
                if 'wiring' in conn:
                    print(f"     Wiring: {conn['wiring']}")
        
        # Show Figure objects if present
        figure_count = sum(1 for k in data.keys() if k.startswith('Figure'))
        if figure_count:
            print(f"\nFigures found: {figure_count}")
        
        print("\n" + "="*80)
        print("Full compiled data structure:")
        print("="*80)
        import json
        print(json.dumps(data, indent=2))
        
    except MOSSError as e:
        print(f"✗ MOSS Error: {e}")
        sys.exit(1)
