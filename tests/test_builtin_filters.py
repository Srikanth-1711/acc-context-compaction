import pytest
from acc.compaction.pipeline import FilterPipeline

def test_git_status_clean():
    raw = "On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean\n"
    pipeline = FilterPipeline.for_command("git status")
    result = pipeline.run(raw)
    assert "[git status: clean]" in result

def test_cargo_build_compiling_only():
    raw = "Compiling foo v1.0.0\nCompiling bar v2.0.0\nFinished dev [unoptimized + debuginfo] target(s) in 0.5s\n"
    pipeline = FilterPipeline.for_command("cargo build")
    result = pipeline.run(raw)
    assert "Compiling" not in result
    assert "Finished" not in result
    # Should be empty or very short
    assert len(result.splitlines()) <= 5

def test_pytest_all_pass():
    raw = "============================= test session starts ==============================\nplatform linux -- Python 3.12\nrootdir: /project\ncollected 10 items\n\n tests/test_foo.py .........                                               [ 90%]\n tests/test_bar.py .                                                       [100%]\n\n============================== 10 passed in 0.5s ===============================\n"
    pipeline = FilterPipeline.for_command("pytest")
    result = pipeline.run(raw)
    assert "passed" in result or len(result) < len(raw)
