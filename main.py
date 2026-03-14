import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import WPGetApp

def main():
    try:
        app = WPGetApp()
        app.mainloop()
    except Exception as e:
        print(f"Critical error during startup: {e}")

if __name__ == "__main__":
    main()