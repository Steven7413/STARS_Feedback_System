import shutil
import os

source = r"C:\Users\gonzo\.gemini\antigravity\brain\e547339f-26f4-44ba-825b-834ae72ea236\uploaded_media_1769309533663.png"
dest_dir = r"C:\Users\gonzo\.gemini\antigravity\scratch\stars-matrix\static\images"
dest_file = "stars_logo_final.png"
dest_path = os.path.join(dest_dir, dest_file)

try:
    print(f"Copying {source}...")
    shutil.copy2(source, dest_path)
    if os.path.exists(dest_path):
        size = os.path.getsize(dest_path)
        print(f"SUCCESS: {dest_file} created. Size: {size} bytes.")
    else:
        print("ERROR: Destination file not found after copy.")
except Exception as e:
    print(f"ERROR: {e}")
