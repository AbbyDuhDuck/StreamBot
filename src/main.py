import sys
import importlib
from pathlib import Path

from bot import UserSettings

# Add project root (one level above src/) to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class bot:
    def run(self):
        print('bot in main')

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <user>")
        sys.exit(1)

    user = sys.argv[1]

    # Ensure usr/ is importable
    sys.path.append(str(Path(__file__).resolve().parent.parent / "usr"))

    try:
        user_module = importlib.import_module(f"{user}")
    except ModuleNotFoundError as e:
        # print(e)
        print(f"No such user module: {user}")
        sys.exit(1)

    if hasattr(user_module, "SETTINGS"):
        settings:UserSettings = user_module.SETTINGS
        settings.run()
    else:
        print(f"User module '{user}' has no User Settings.")

if __name__ == "__main__":
    main()
