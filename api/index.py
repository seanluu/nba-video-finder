from mangum import Mangum
import sys
import os

# Add parent directory to path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Change to parent directory so imports work correctly
os.chdir(parent_dir)

# Import the FastAPI app from api.py
# Use importlib to avoid naming conflict with 'api' directory
try:
    import importlib.util
    api_file_path = os.path.join(parent_dir, "api.py")
    if not os.path.exists(api_file_path):
        raise FileNotFoundError(f"api.py not found at {api_file_path}")
    
    spec = importlib.util.spec_from_file_location("api_module", api_file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {api_file_path}")
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    app = api_module.app
except Exception as e:
    # Fallback: try direct import if PYTHONPATH is set correctly
    try:
        import api as api_module
        app = api_module.app
    except Exception as e2:
        raise ImportError(f"Failed to import api module: {e}, {e2}")

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app, lifespan="off")

