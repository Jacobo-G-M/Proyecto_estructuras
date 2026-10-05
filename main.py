import os
import sys

# Ensure that the root directory is in the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Business.observatory import Observatory
from Presentation.app import SismoLabApp

def main():
    # 1. Initialize the business layer
    observatory = Observatory()
    
    # 2. Initialize and execute the presentation layer
    app = SismoLabApp(observatory)
    app.run()

if __name__ == "__main__":
    main()

