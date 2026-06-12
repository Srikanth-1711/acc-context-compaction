from acc.structured.python_ast import compress_python
from acc.structured.json_minifier import compress_json

def test_python_skeleton():
    code = '''
def process_data(x):
    """
    This is a docstring.
    """
    y = x + 1
    return y
    
class MyClass:
    """Class docstring"""
    def __init__(self):
        self.val = 1
'''
    res = compress_python(code)
    # Docstrings and bodies should be removed
    assert "This is a docstring." not in res
    assert "y = x + 1" not in res
    assert "self.val = 1" not in res
    assert "def process_data(x):" in res
    assert "class MyClass:" in res
    assert "pass" in res

def test_json_minify_truncate():
    data = '''
{
    "status": "ok",
    "deep": {
        "level1": {
            "level2": {
                "level3": "hide me"
            }
        }
    }
}
'''
    res = compress_json(data, max_depth=2)
    assert "hide me" not in res
    assert "truncated" in res
    assert '"status":"ok"' in res # Minified without spaces
