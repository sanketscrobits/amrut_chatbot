from agents.Workflow.workflow import workflow

mermaid_text = workflow.get_graph().draw_mermaid()
print(mermaid_text)  # Copy-paste into https://mermaid.live/ for interactive PNG/SVG