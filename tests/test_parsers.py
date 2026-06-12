from acc.compaction.parsers import parse_git_status

def test_parse_git_status():
    lines = [" M file1.py", "?? new_file.py"]
    res = parse_git_status(lines)
    assert "M file1.py" in res["modified"]
    assert "new_file.py" in res["untracked"]
