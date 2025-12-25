from mangum import Mangum
import sys
import os

# Add parent directory to path to import api module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the FastAPI app from api.py (need to use importlib to avoid naming conflict)
import importlib.util
spec = importlib.util.spec_from_file_location("api_module", os.path.join(parent_dir, "api.py"))
api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_module)
app = api_module.app

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app)

