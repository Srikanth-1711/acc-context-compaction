import json
from acc.structured.conversation import compress_conversation

def test_conversation_compression():
    raw_log = """
USER: Can we update the database?
AGENT: Let me check.
TOOL CALL: run_command('cat db.py')
TOOL OUTPUT: db.connect()
AGENT: I see.
### DECISION: We will migrate to Postgres.
TOOL CALL: edit_file('db.py')
TOOL OUTPUT: success
AGENT: I added the postgres string.
<goal>Add user authentication</goal>
AGENT: Also need to make sure we don't drop the schema.
Constraint: Do not drop public schema.
TODO: Run tests.
    """
    
    out = compress_conversation(raw_log)
    data = json.loads(out)
    
    assert "migrate to Postgres" in data["decisions"][0]
    assert "Add user authentication" in data["goals"][0]
    assert "Do not drop public schema." in data["constraints"][0]
    assert "Run tests." in data["open_tasks"][0]
