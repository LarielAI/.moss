"""
Comprehensive test suite for MOSS compiler
Tests edge cases, nested structures, connections, and parsing
"""

import unittest
import tempfile
from pathlib import Path
from moss import MOSSCompiler, MOSSError


class TestMOSSBasics(unittest.TestCase):
    """Test basic MOSS file parsing"""
    
    def setUp(self):
        self.compiler = MOSSCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def _create_moss_file(self, content: str) -> str:
        """Helper to create a temporary MOSS file"""
        filepath = Path(self.temp_dir.name) / "test.moss"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def test_simple_keyvalue(self):
        """Test basic key:value parsing"""
        content = """@MOSS:test
name: John
age: 30
active: true
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['name'], 'John')
        self.assertEqual(data['age'], 30)
        self.assertEqual(data['active'], True)
    
    def test_quoted_strings(self):
        """Test quoted string handling"""
        content = """@MOSS:test
name: "John Doe"
city: 'New York'
empty: ""
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['city'], 'New York')
        self.assertEqual(data['empty'], '')
    
    def test_escape_sequences(self):
        """Test escaped quotes in strings"""
        content = '''@MOSS:test
quote1: "He said \\"Hello\\""
quote2: 'It\\'s working'
'''
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['quote1'], 'He said "Hello"')
        self.assertEqual(data['quote2'], "It's working")
    
    def test_inline_comments(self):
        """Test inline comment stripping"""
        content = """@MOSS:test
name: John  # This is a comment
age: 30 # Also a comment
active: true
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['name'], 'John')
        self.assertEqual(data['age'], 30)
    
    def test_comment_in_quoted_string(self):
        """Test that # inside quotes is not treated as comment"""
        content = """@MOSS:test
hashtag: "#python"
path: "C:\\#temp\\file.txt"
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['hashtag'], '#python')
        self.assertEqual(data['path'], 'C:\\#temp\\file.txt')
    
    def test_type_coercion(self):
        """Test automatic type conversion"""
        content = """@MOSS:test
integer: 42
float: 3.14
bool_true: true
bool_false: false
null_val: null
none_val: none
string: "text"
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIsInstance(data['integer'], int)
        self.assertIsInstance(data['float'], float)
        self.assertIs(data['bool_true'], True)
        self.assertIs(data['bool_false'], False)
        self.assertIsNone(data['null_val'])
        self.assertIsNone(data['none_val'])
        self.assertIsInstance(data['string'], str)


class TestMOSSNesting(unittest.TestCase):
    """Test nested structure parsing"""
    
    def setUp(self):
        self.compiler = MOSSCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def _create_moss_file(self, content: str) -> str:
        filepath = Path(self.temp_dir.name) / "test.moss"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def test_simple_nesting(self):
        """Test basic nested objects"""
        content = """@MOSS:test
user:
  name: John
  age: 30
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIsInstance(data['user'], dict)
        self.assertEqual(data['user']['name'], 'John')
        self.assertEqual(data['user']['age'], 30)
    
    def test_deep_nesting(self):
        """Test multiple levels of nesting"""
        content = """@MOSS:test
company:
  departments:
    engineering:
      members: 10
      budget: 500000
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['company']['departments']['engineering']['members'], 10)
        self.assertEqual(data['company']['departments']['engineering']['budget'], 500000)
    
    def test_simple_list(self):
        """Test simple list parsing"""
        content = """@MOSS:test
colors:
  - red
  - green
  - blue
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIsInstance(data['colors'], list)
        self.assertEqual(len(data['colors']), 3)
        self.assertEqual(data['colors'][0], 'red')
    
    def test_mixed_nested_structures(self):
        """Test objects containing both key:value and nested objects"""
        content = """@MOSS:test
config:
  app_name: MyApp
  settings:
    debug: true
    timeout: 30
  version: 1.0
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['config']['app_name'], 'MyApp')
        self.assertEqual(data['config']['settings']['debug'], True)
        self.assertEqual(data['config']['version'], 1.0)
    
    def test_list_of_objects(self):
        """Test list containing objects"""
        content = """@MOSS:test
users:
  - name: John
    age: 30
  - name: Jane
    age: 25
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(len(data['users']), 2)
        self.assertEqual(data['users'][0]['name'], 'John')
        self.assertEqual(data['users'][1]['age'], 25)


class TestMOSSConnections(unittest.TestCase):
    """Test connection/wiring syntax"""
    
    def setUp(self):
        self.compiler = MOSSCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def _create_moss_file(self, content: str) -> str:
        filepath = Path(self.temp_dir.name) / "test.moss"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def test_simple_connection(self):
        """Test basic // connection syntax"""
        content = """@MOSS:test
device_a: "Component A"
device_b: "Component B" // device_a
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIn('connections', data)
        self.assertEqual(len(data['connections']), 1)
        self.assertEqual(data['connections'][0]['from'], 'device_b: "Component B"')
        self.assertEqual(data['connections'][0]['to'], 'device_a')
    
    def test_connection_chain(self):
        """Test chained connections with multiple //"""
        content = """@MOSS:test
a: "First" // b // c // d
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIn('connections', data)
        # Should create multiple connection pairs
        self.assertGreaterEqual(len(data['connections']), 1)


class TestMOSSHeaders(unittest.TestCase):
    """Test MOSS header validation"""
    
    def setUp(self):
        self.compiler = MOSSCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def _create_moss_file(self, content: str) -> str:
        filepath = Path(self.temp_dir.name) / "test.moss"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def test_missing_moss_header(self):
        """Test error on missing @MOSS: header"""
        content = """name: John
age: 30
"""
        filepath = self._create_moss_file(content)
        
        with self.assertRaises(MOSSError) as cm:
            self.compiler.load(filepath)
        
        self.assertIn("@MOSS:", str(cm.exception))
    
    def test_manual_validation(self):
        """Test manual name validation"""
        content = """@MOSS:MyManual
data: test
"""
        filepath = self._create_moss_file(content)
        
        # Should pass with correct name
        data = self.compiler.load(filepath, expected_manual='MyManual')
        self.assertEqual(data['_moss_manual'], 'MyManual')
        
        # Should fail with wrong name
        with self.assertRaises(MOSSError):
            self.compiler.load(filepath, expected_manual='WrongManual')
    
    def test_all_headers(self):
        """Test parsing @MOSS:, @R:, and @QR: headers"""
        content = """@MOSS:TestManual
@R:C:\\resources\\
@QR:SKU12345

data: value
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['_moss_manual'], 'TestManual')
        self.assertEqual(data['_moss_r'], 'C:\\resources\\')
        self.assertEqual(data['_moss_qr'], 'SKU12345')


class TestMOSSEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.compiler = MOSSCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def _create_moss_file(self, content: str) -> str:
        filepath = Path(self.temp_dir.name) / "test.moss"
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def test_empty_dict_value(self):
        """Test empty dict syntax"""
        content = """@MOSS:test
empty_obj:
  nested: value
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertIsInstance(data['empty_obj'], dict)
        self.assertEqual(data['empty_obj']['nested'], 'value')
    
    def test_whitespace_handling(self):
        """Test proper whitespace handling"""
        content = """@MOSS:test
name:     John     
  
age:30
active  :  true
"""
        filepath = self._create_moss_file(content)
        data = self.compiler.load(filepath)
        
        self.assertEqual(data['name'], 'John')
        self.assertEqual(data['age'], 30)
        self.assertEqual(data['active'], True)
    
    def test_non_moss_file(self):
        """Test error on non-.moss file"""
        temp_file = Path(self.temp_dir.name) / "test.txt"
        temp_file.write_text("@MOSS:test\ndata: value")
        
        with self.assertRaises(MOSSError) as cm:
            self.compiler.load(str(temp_file))
        
        self.assertIn("Not a MOSS file", str(cm.exception))
    
    def test_file_not_found(self):
        """Test error on missing file"""
        with self.assertRaises(MOSSError) as cm:
            self.compiler.load("/nonexistent/path/file.moss")
        
        self.assertIn("File not found", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
