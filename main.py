import os
import sys

# Asegurar que el directorio raíz está en el path para los imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Business.observatory import Observatory
from Presentation.app import SismoLabApp

def main():
    # 1. Inicializar la capa de negocio
    observatory = Observatory()
    
    # 2. Inicializar y ejecutar la capa de presentación
    app = SismoLabApp(observatory)
    app.run()

if __name__ == "__main__":
    main()

