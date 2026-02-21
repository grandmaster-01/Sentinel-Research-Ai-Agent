from src.app_workflow import app
try:
    print("Invoking app...")
    result = app.invoke({"question": "Test query"})
    print("Invocation successful.")
    # print(result)
except Exception as e:
    print(f"Invocation failed: {e}")
    import traceback
    with open("last_invocation_error.txt", "w") as f:
        f.write(str(e))
        traceback.print_exc(file=f)
