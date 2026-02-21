import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    # Pre-import to avoid weird loading issues
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
    from src.app_workflow import workflow, AgentState
    print("Graph imported successfully.")
    
    app = workflow.compile()
    print("Graph compiled successfully.")
    
    print("Verification PASSED.")
except Exception as e:
    print(f"Verification FAILED: {e}")
    import traceback
    traceback.print_exc()
