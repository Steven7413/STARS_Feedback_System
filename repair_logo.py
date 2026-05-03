import shutil
import os

source = r"C:\Users\gonzo\.gemini\antigravity\brain\e547339f-26f4-44ba-825b-834ae72ea236\uploaded_media_1769309533663.png"
dest = r"C:\Users\gonzo\.gemini\antigravity\scratch\stars-matrix\static\images\stars_certified.png"

try:
    print(f"Attempting to copy from:\n{source}\nto:\n{dest}")
    if not os.path.exists(source):
        print("ERROR: Source file does not exist!")
    else:
        shutil.copy2(source, dest)
        size = os.path.getsize(dest)
        print(f"SUCCESS: File copied. New size: {size} bytes.")
except Exception as e:
    print(f"ERROR: {e}")
