# SismoLab AVL · Observatorio Sismológico

Sistema de monitoreo, indexación y análisis sismológico en tiempo real implementado en Python y CustomTkinter, fundamentado en una estructura de datos de **Árbol AVL balanceado** con clave lexicográfica:

$$K = (\text{Prioridad } P, \text{Magnitud } M, \text{Identificador } ID)$$

---

## 🚀 Requisitos e Instalación

1. **Clonar o descargar el repositorio** e ingresar al directorio raíz:
   ```powershell
   cd SismoLabAVL
   ```

2. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación interactiva (GUI):**
   ```powershell
   python main.py
   ```

4. **Ejecutar las pruebas automatizadas (`unittest`):**
   ```powershell
   # Ejecutar todas las pruebas del proyecto (111 tests de negocio + GUI)
   python -m unittest discover -s Tests -t .

   # Ejecutar específicamente las pruebas de interfaz gráfica
   python -m unittest Tests/Presentation/test_gui_scenarios.py
   ```

---

## 🧪 Guía Rápida de Verificación: Casos de Prueba (Sección 16)

Todos los conjuntos de datos reproducibles se encuentran organizados en la carpeta:
📁 **`saved_versions/casos_de_prueba/`**

### ¿Cómo cargarlos en la Interfaz Gráfica?
1. Ejecuta `python main.py`.
2. En la esquina superior derecha de la barra superior (Topbar), haz clic en el botón **`▾ Demo Activo`**.
3. Pasa el cursor por el submenú **`🧪 Casos De Prueba ▶`** y selecciona el escenario deseado.

---

### Resumen de los 6 Casos de Prueba

| Caso | Archivo en Menú | Vista de Verificación | Acción del Usuario | Resultado Esperado |
| :---: | :--- | :---: | :--- | :--- |
| **1** | `caso1_limites_empates` | **Árboles** y **Mapa** | Cargar escenario e inspeccionar nodos. | • **EV-50** en borde $X=300$ clasifica en zona poblada ($P=3$, halo cian).<br>• **EV-10** fuera de zona clasifica rural ($P=2$, ámbar).<br>• **EV-35** y **EV-20** (ambos $M=5.0, P=2$) desempatan por ID: EV-35 se ubica a la **derecha** de EV-20. |
| **2** | `caso2_correccion_reporte_antiguo_inicial` | **Eventos** | 1. Clic en `▶ Paso a Paso`.<br>2. Clic en `▶ Paso a Paso` de nuevo. | • **Paso 1:** Reporte v2 ($M=6.2$) es aceptado; EV-100 asciende a $P=3$ con clave $(3, 6.2, 100)$.<br>• **Paso 2:** Reporte v1 antiguo es **descartado** sin mutar el sismo ni revertir su clave. |
| **3** | `caso3_reporte_tardio_antes` | **Mapa** y **Eventos** | 1. Ver líneas en Mapa.<br>2. En Eventos, clic en `▶ Paso a Paso`. | • Llega EV-3 (ocurrido a las 09:55 con $M=6.1$).<br>• **Reclustering determinista:** EV-3 pasa a ser el sismo principal; EV-1 y EV-2 se convierten en sus réplicas y las líneas vectoriales convergen hacia EV-3. |
| **4** | `caso4_estres_desbalanceado` | **Barra Superior** y **Árboles** | Clic en el botón naranja `Recuperar Equilibrio AVL`. | • Al cargar: Switch marca `Estrés: Activo` y se ve rama degenerada ($FB > 1$).<br>• Al recuperar: Modal con desglose de rotaciones, árbol rebalanceado in-situ ($FB \in \{-1,0,1\}$) y switch vuelve a `Inactivo`. |
| **5** | `caso5_archivo_subarboles` | **Eventos** y **Barra Superior** | 1. Clic en `Ejecutar Archivo de Rama`.<br>2. Clic en `↩ Deshacer`. | • Rama A (raíz 12, 3 nodos $P=1$) es **Elegible** ($> 72\text{ h}$).<br>• Rama B (raíz 62) es **Descalificada** por tener nodo con $P=2$.<br>• Se archiva la Rama A; `↩ Deshacer` la restaura al árbol activo. |
| **6** | `caso6_error_*` | **Cualquiera** | Intentar cargar cualquiera de los 4 archivos de error. | • **Rechazo Atómico:** Ventana modal de error (`messagebox.showerror`) describiendo la violación (BST, IDs duplicados, alturas o desbalance sin estrés).<br>• El estado del observatorio permanece intacto. |

> **Nota:** La secuencia de inserciones elementales para validar rotaciones sucesivas (LL, RR, LR, RL) está disponible en `caso4_rotaciones_secuencia.json` y se comprueba automáticamente en la suite de pruebas.

---

## 📁 Estructura del Proyecto

```text
SismoLabAVL/
├── Business/                 # Capa de lógica de negocio, observatorio y reglas
│   ├── Rules/                # Algoritmos de consultas, podas y reclustering
│   ├── Structures/           # Árbol AVL, BST, cola de reportes y pila undo
│   ├── geographical_map.py   # Gestión espacial, zonas y estaciones
│   ├── observatory.py        # Fachada maestra del observatorio
│   └── scenario_persistence.py # Serialización, exportación y validación atómica JSON
├── Models/                   # Entidades (Event, Node, Report, Station, Zone, etc.)
├── Presentation/             # Capa gráfica CustomTkinter (arquitectura atómica)
│   ├── Components/           # Botones, tarjetas, modales, topbar y sidebar
│   ├── Views/                # DashboardView, TreeView, MapView, EventsView, QueriesView
│   └── app.py                # Ventana principal y ruteo modular
├── saved_versions/           # Versiones guardadas y catálogo de pruebas
│   └── casos_de_prueba/      # Conjunto oficial de los 14 archivos JSON de prueba
├── Tests/                    # Suite automatizada de pruebas unitarias y de GUI
│   ├── Business/             # Pruebas de reglas de negocio y validación de escenarios
│   ├── Presentation/         # Pruebas de integración sobre la interfaz gráfica
│   └── scenarios/            # Script 'generate_all.py' para reconstrucción de datos
├── requirements.txt          # Dependencias de Python
└── main.py                   # Punto de entrada de la aplicación
```

---

> ℹ️ **Documentación Técnica Completa:**  
> Los diagramas de clases UML, especificaciones formales de interfaz, contratos de complejidad asintótica $O(N)$ / $O(\log N)$ y el diseño arquitectónico profundo se detallan en el **Manual Técnico del Sistema**.