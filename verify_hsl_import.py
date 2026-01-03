
import sys
import os

# 将当前目录添加到 PYTHONPATH
sys.path.append(os.getcwd())

try:
    from zquant.models.data import HslChoice
    print("SUCCESS: HslChoice imported successfully.")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")
