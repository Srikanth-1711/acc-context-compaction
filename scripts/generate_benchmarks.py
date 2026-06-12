import os
import json

BENCHMARKS_DIR = "benchmarks"
CATEGORIES = {
    "pytest": 20,
    "git": 20,
    "docker": 20,
    "kubectl": 20,
    "conversations": 20,
    "repositories": 10,
    "python_code": 10,
    "json_data": 10
}

def create_mock_data(category, index):
    raw_content = ""
    expected_signal = {"errors": [], "warnings": [], "critical_files": [], "decisions": []}
    
    if category == "pytest":
        raw_content = f"============================= test session starts =============================\nplatform linux -- Python 3.10\ncollected {index+5} items\ntest_{index}.py F\n\nFAILURES\n> assert {index} == {index+1}\nE AssertionError: assert {index} == {index+1}\n"
        expected_signal["errors"].append(f"AssertionError: assert {index} == {index+1}")
    elif category == "git":
        raw_content = f"diff --git a/file{index}.py b/file{index}.py\nindex a..b\n--- a/file{index}.py\n+++ b/file{index}.py\n@@ -1,3 +1,4 @@\n def func():\n-    pass\n+    return {index}\n"
        expected_signal["critical_files"].append(f"file{index}.py")
    elif category == "docker":
        raw_content = f"Step 1/5 : FROM python:3.9\nStep 2/5 : RUN pip install -r requirements.txt\nWARNING: Running pip as the 'root' user can result in broken permissions.\nStep 3/5 : COPY . .\n"
        expected_signal["warnings"].append("Running pip as the 'root' user can result in broken permissions.")
    elif category == "kubectl":
        raw_content = f"NAME      READY   STATUS             RESTARTS   AGE\npod-{index}   0/1     CrashLoopBackOff   5          10m\nError: Liveness probe failed: HTTP probe failed with statuscode: 500\n"
        expected_signal["errors"].append("Liveness probe failed: HTTP probe failed with statuscode: 500")
    elif category == "conversations":
        raw_content = f"User: Can we use PostgreSQL for this project?\nAgent: Yes, we can. Let's use it.\nUser: Actually, let's stick to SQLite for phase {index} to keep it simple.\nAgent: Agreed, SQLite it is."
        expected_signal["decisions"].append(f"Use SQLite for phase {index}")
    elif category == "repositories":
        raw_content = f"Project {index} has 500 files.\nEntry point is src/main.py.\nDependencies are in pyproject.toml.\n"
        expected_signal["critical_files"].extend(["src/main.py", "pyproject.toml"])
    elif category == "python_code":
        raw_content = f'def process_data_{index}(x):\n    """\n    This is a long docstring for process_data_{index}.\n    It explains many things.\n    """\n    y = x + 1\n    z = y * 2\n    return z\n\nclass DataManager_{index}:\n    def __init__(self):\n        self.data = []\n'
        expected_signal["critical_files"].extend([f"def process_data_{index}(x):", f"class DataManager_{index}:"])
    elif category == "json_data":
        raw_content = '{\n  "status": "success",\n  "data": {\n    "items": [\n      {"id": 1, "name": "A"},\n      {"id": 2, "name": "B"}\n    ]\n  }\n}'
        expected_signal["critical_files"].append('"status":"success"')
        
    return raw_content, expected_signal

def generate():
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)
    for cat, count in CATEGORIES.items():
        cat_dir = os.path.join(BENCHMARKS_DIR, cat)
        os.makedirs(cat_dir, exist_ok=True)
        
        for i in range(1, count + 1):
            sample_dir = os.path.join(cat_dir, f"sample_{i:03d}")
            os.makedirs(sample_dir, exist_ok=True)
            
            raw, signal = create_mock_data(cat, i)
            
            with open(os.path.join(sample_dir, "raw_input.txt"), "w") as f:
                f.write(raw)
                
            with open(os.path.join(sample_dir, "expected_signal.json"), "w") as f:
                json.dump(signal, f, indent=2)

if __name__ == "__main__":
    generate()
    print("Generated all benchmark datasets successfully!")
