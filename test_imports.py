import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import all modules to check for import errors
try:
    from core import (
        config,
        db_helper,
        create_access_token,
        create_refresh_token,
        decode_token,
        hash_password,
        verify_password,
        Base,
        User,
        Task,
    )
    from users.routes import router as users_router
    from tasks.routes import router as tasks_router
    from main import app

    print("✓ All imports successful!")
    print(f"✓ Database URL: {config.database_url[:50]}...")
    print(f"✓ JWT Algorithm: {config.jwt_algorithm}")
    print(f"✓ Users router: {users_router}")
    print(f"✓ Tasks router: {tasks_router}")
    print(f"✓ FastAPI app: {app.title}")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
