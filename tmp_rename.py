import os
import shutil
from pathlib import Path

target_dir = os.path.abspath(r'..\SkyHigh')

if not os.path.exists(target_dir):
    print(f"Target directory {target_dir} not found. Must have been renamed already.")
    exit(0)

print(f"Executing mass rebrand on {target_dir}...")

# 1. Recursive String Replacement
for root, dirs, files in os.walk(target_dir):
    # Skip python venv, node_modules, and git
    if 'venv' in root or 'node_modules' in root or '.git' in root or '__pycache__' in root:
        continue
        
    for file in files:
        # Only modify text files
        if file.endswith(('.js', '.jsx', '.py', '.html', '.json', '.bat', '.md', '.txt', '.ps1')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Case sensitive replacements
                new_content = content.replace("SkyHigh", "WingID")
                new_content = new_content.replace("SKYHIGH", "WINGID")
                new_content = new_content.replace("skyhigh", "wingid")
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Refactored contents of: {file}")
            except Exception as e:
                print(f"Failed to read/write {file}: {e}")

# 2. File Renaming
bat_old = os.path.join(target_dir, 'Run_SkyHigh.bat')
bat_new = os.path.join(target_dir, 'Run_WingID.bat')
if os.path.exists(bat_old):
    try:
        os.rename(bat_old, bat_new)
        print("Renamed Run_SkyHigh.bat -> Run_WingID.bat")
    except Exception as e:
        print(f"Could not rename bat file: {e}")

# 3. Directory Renaming
new_dir = os.path.abspath(r'..\WingID')
try:
    os.rename(target_dir, new_dir)
    print(f"SUCCESS: Renamed project directory to {new_dir}")
except PermissionError:
    print("PERMISSION ERROR: Could not rename root directory because files/terminals are explicitly active.")
except Exception as e:
    print(f"Failed to rename root dir: {e}")
