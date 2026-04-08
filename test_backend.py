import sys
import os

# Move into backend
os.chdir('backend')
sys.path.append(os.getcwd())

print("Current Path:", sys.path)

try:
    from app.main import app
    print("Backend App Loaded Successfully!")
except Exception as e:
    print("Backend App Failed to Load:")
    import traceback
    traceback.print_exc()
