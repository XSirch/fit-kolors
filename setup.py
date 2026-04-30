import os
import subprocess
import sys

def run_cmd(cmd, cwd=None):
    print(f"Running: {cmd} in {cwd or 'current dir'}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)

def setup():
    print("=== Fit-Kolors Setup ===")
    
    # Setup Backend
    print("\n[1/3] Setting up Backend...")
    if not os.path.exists("backend/venv"):
        run_cmd("python -m venv venv", cwd="backend")
    
    # Install backend requirements
    pip_path = "venv\\Scripts\\pip" if os.name == "nt" else "venv/bin/pip"
    run_cmd(f"{pip_path} install -r requirements.txt", cwd="backend")
    
    # Setup Frontend
    print("\n[2/3] Setting up Frontend...")
    run_cmd("npm install", cwd="frontend")
    
    print("\n[3/3] Done!")
    print("\nTo start the application:")
    print("1. Start Backend: cd backend && venv\\Scripts\\python main.py")
    print("2. Start Frontend: cd frontend && npm run dev")
    print("\nNote: Make sure to set GOOGLE_API_KEY in backend/.env")

if __name__ == "__main__":
    setup()
