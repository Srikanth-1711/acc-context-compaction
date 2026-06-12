import os
from acc.repo.analyzer import build_import_graph
from acc.repo.ranker import rank_files
from acc.repo.compressor import compress_repository

def test_build_import_graph(tmp_path):
    # Setup dummy repo
    d = tmp_path / "src"
    d.mkdir()
    
    # core.py
    (d / "core.py").write_text("def core_func():\n    pass\n")
    
    # models.py imports core
    (d / "models.py").write_text("import src.core\nclass Model:\n    pass\n")
    
    # main.py imports models and core
    (d / "main.py").write_text("from src import models\nimport src.core\nprint('hello')\n")
    
    graph = build_import_graph(str(tmp_path))
    
    assert "src.core" in graph
    assert "src.models" in graph
    assert "src.main" in graph
    
    assert "src.core" in graph["src.models"]
    assert "src.models" in graph["src.main"]
    assert "src.core" in graph["src.main"]

def test_rank_files():
    graph = {
        "src.core": [],
        "src.models": ["src.core"],
        "src.main": ["src.models", "src.core"]
    }
    
    ranked = rank_files(graph)
    # core is imported 2 times, models 1 time, main 0 times
    assert ranked[0][0] == "src.core"
    assert ranked[0][1] == 2
    assert ranked[1][0] == "src.models"
    assert ranked[1][1] == 1
    assert ranked[2][0] == "src.main"
    assert ranked[2][1] == 0

def test_compress_repository(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    
    # Highly imported (Core)
    (d / "core.py").write_text("def core_func():\n    '''Keep my body'''\n    return 42\n")
    
    # Leaf
    (d / "main.py").write_text("import src.core\ndef main():\n    '''Kill my body'''\n    print('hello')\n")
    
    output = compress_repository(str(tmp_path))
    
    assert "Repository Architecture" in output
    assert "core.py" in output
    assert "main.py" in output
    
    # core.py body should be kept because it's core (ranked 1st)
    assert "return 42" in output
    # main.py body should be skeletonized because it's leaf
    assert "print('hello')" not in output
    assert "pass" in output
