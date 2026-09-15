import importlib.util
import sys
from pathlib import Path

MAIN_FILE = Path(__file__).resolve().parent / "main-langfuseEval.py"

spec = importlib.util.spec_from_file_location("main_langfuseEval_module", MAIN_FILE)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load module spec for {MAIN_FILE}")

main_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main_module
spec.loader.exec_module(main_module)

try:
    app = main_module.app
except AttributeError as exc:
    raise RuntimeError(f"The FastAPI app object was not found in {MAIN_FILE}") from exc

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
