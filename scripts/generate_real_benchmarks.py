import os
import json
import random

def generate_pytest(base_dir):
    cat_dir = os.path.join(base_dir, "pytest", "sample_001")
    os.makedirs(cat_dir, exist_ok=True)
    
    lines = []
    # 50,000 lines of pytest output
    for i in range(50000):
        if i == 25000:
            lines.append("FAILED tests/test_critical.py::test_auth - AssertionError: 401 != 200")
            lines.append("Traceback (most recent call last):")
            lines.append("  File 'tests/test_critical.py', line 45, in test_auth")
            lines.append("    assert response.status_code == 200")
            lines.append("AssertionError")
        elif i == 45000:
            lines.append("FAILED tests/test_db.py::test_connection - sqlalchemy.exc.OperationalError: Connection refused")
            lines.append("Traceback (most recent call last):")
            lines.append("  File 'tests/test_db.py', line 12, in test_connection")
            lines.append("    db.connect()")
            lines.append("sqlalchemy.exc.OperationalError")
        else:
            lines.append(f"tests/test_generic_{i%1000}.py::test_{i} PASSED [ {(i%100)}%]")
            
    raw_text = "\n".join(lines)
    with open(os.path.join(cat_dir, "raw_input.txt"), "w", encoding="utf-8") as f:
        f.write(raw_text)
        
    expected = {
        "errors": [
            "FAILED tests/test_critical.py::test_auth - AssertionError: 401 != 200",
            "FAILED tests/test_db.py::test_connection - sqlalchemy.exc.OperationalError: Connection refused"
        ]
    }
    with open(os.path.join(cat_dir, "expected_signal.json"), "w", encoding="utf-8") as f:
        json.dump(expected, f, indent=2)

def generate_docker(base_dir):
    cat_dir = os.path.join(base_dir, "docker", "sample_001")
    os.makedirs(cat_dir, exist_ok=True)
    
    lines = []
    for i in range(30000):
        if i == 29990:
            lines.append("npm ERR! code ERESOLVE")
            lines.append("npm ERR! ERESOLVE unable to resolve dependency tree")
            lines.append("npm ERR! Found: react@18.2.0")
            lines.append("npm ERR! node_modules/react")
        else:
            hash_str = f"{random.getrandbits(64):016x}"
            lines.append(f"Get:{i} http://archive.ubuntu.com/ubuntu jammy/main amd64 package_{i} [10{i} kB]")
            lines.append(f"Fetched 10{i} kB in 0s (100{i} kB/s)")
            
    raw_text = "\n".join(lines)
    with open(os.path.join(cat_dir, "raw_input.txt"), "w", encoding="utf-8") as f:
        f.write(raw_text)
        
    expected = {
        "errors": [
            "npm ERR! code ERESOLVE",
            "npm ERR! ERESOLVE unable to resolve dependency tree"
        ]
    }
    with open(os.path.join(cat_dir, "expected_signal.json"), "w", encoding="utf-8") as f:
        json.dump(expected, f, indent=2)

def generate_conversations(base_dir):
    cat_dir = os.path.join(base_dir, "conversations", "sample_001")
    os.makedirs(cat_dir, exist_ok=True)
    
    lines = []
    lines.append("USER: We need to implement the new billing system.")
    lines.append("AGENT: I will check the codebase.")
    
    # Tool call bloat
    for i in range(10000):
        lines.append(f"TOOL CALL: grep_search('billing_v{i}')")
        lines.append(f"TOOL OUTPUT: No results found for 'billing_v{i}'")
        lines.append("AGENT: Let me try something else.")
        
    lines.append("AGENT: Ah, I found it in `src/payments.py`.")
    lines.append("### DECISION: We will migrate `src/payments.py` to use Stripe v3 API.")
    lines.append("TOOL CALL: replace_file_content('src/payments.py')")
    lines.append("TOOL OUTPUT: Success")
    lines.append("AGENT: The code is updated. However, the database schema still needs a migration.")
    lines.append("<goal>Migrate user table to add stripe_customer_id</goal>")
    lines.append("USER: Sounds good, but remember we must not drop the old paypal_id column yet.")
    lines.append("AGENT: Understood. Constraint added: Do not drop paypal_id.")
    
    for i in range(10000):
        lines.append(f"TOOL CALL: run_command('npm run test_{i}')")
        lines.append("TOOL OUTPUT: PASS")
        
    lines.append("AGENT: Tests passed. Next step is to run the alembic migration.")
    lines.append("TODO: Run `alembic upgrade head` in production.")
    
    raw_text = "\n".join(lines)
    with open(os.path.join(cat_dir, "raw_input.txt"), "w", encoding="utf-8") as f:
        f.write(raw_text)
        
    expected = {
        "decisions": ["migrate `src/payments.py` to use Stripe v3 API"],
        "goals": ["Migrate user table to add stripe_customer_id"],
        "constraints": ["Do not drop paypal_id"],
        "open_tasks": ["Run `alembic upgrade head` in production"]
    }
    with open(os.path.join(cat_dir, "expected_signal.json"), "w", encoding="utf-8") as f:
        json.dump(expected, f, indent=2)

if __name__ == "__main__":
    base = os.path.join("benchmarks", "real_benchmarks")
    os.makedirs(base, exist_ok=True)
    generate_pytest(base)
    generate_docker(base)
    generate_conversations(base)
    print("Generated real_benchmarks datasets.")
