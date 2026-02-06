#!/usr/bin/env python3
with open('src/Workflow/master_workflow.py', 'r') as f:
    content = f.read()

# Replace the bad escaped quotes
content = content.replace('state.get(\\"query_response\\")', 'state.get("query_response")')

with open('src/Workflow/master_workflow.py', 'w') as f:
    f.write(content)

print("Fixed the syntax error!")
