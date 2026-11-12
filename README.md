# OptiLab

A desktop app: a [pywebview](https://pywebview.flowrl.com/) shell around a Vue 3 + Tailwind frontend, backed by a Python API that does numeric work with NumPy/SciPy.

## Architecture

- **Backend** (`src/optilab/`) — `app.py` creates the pywebview window and exposes an `Api` class to the frontend as `window.pywebview.api`. Computation (stats, etc.) lives here, not in JS.
- **Frontend** (`frontend/`) — Vue 3 (`<script setup>` SFCs) + Tailwind CSS v4, built with Vite. Talks to the backend only through the pywebview JS bridge.
- **Dev vs. prod loading** — `app.py` points the webview at the Vite dev server (`http://localhost:5173`) when `OPTILAB_DEV=1` or no production build exists at `frontend/dist`; otherwise it loads the built `index.html` directly.

## Prerequisites

- Python >= 3.11
- Node.js (for the `frontend/` npm project)
- [`just`](https://github.com/casey/just) as the task runner
- Windows: see the step-by-step [Windows user manual](#manual-de-usuario-windows) below (the `just` recipes assume Linux/macOS paths, so on Windows use the plain commands listed there)
- Linux: system packages for the GTK webview backend — `python-gobject` and `webkit2gtk-4.1` (these are **not** pip-installable, which is why the venv is created with `--system-site-packages`)

## Quickstart

```sh
just install   # create venv (system-site-packages) + install Python/frontend deps
just dev       # run Vite dev server + pywebview app together (hot reload)
```

## Common commands

| Command | Does |
| --- | --- |
| `just install` | Create `.venv` and install Python (`.[dev]`) + frontend (`npm install`) deps |
| `just dev` | Run Vite dev server and the pywebview app together, pointed at `localhost:5173` |
| `just build` | Build the production frontend bundle into `frontend/dist` |
| `just run` | Run the app against the built frontend (run `just build` first) |
| `just test` | Run the pytest suite |
| `just lint` | `ruff check` over `src` and `tests` |
| `just format` | `ruff format` over `src` and `tests` |
| `just check` | `lint` + `test`, mirrors CI |
| `just clean` | Remove venv, caches, and build artifacts |

Run `just` with no args to list all recipes.

## Manual de usuario (Windows)

Guía paso a paso para abrir OptiLab en Windows 10 u 11 (64 bits), sin necesidad de `just`. Todos los comandos se escriben en **PowerShell** (menú Inicio → escribir "PowerShell" → Enter).

### 1. Instalar lo necesario (una sola vez)

| Programa | Qué descargar | Notas |
| --- | --- | --- |
| Python 3.12 o 3.13 (64 bits) | <https://www.python.org/downloads/windows/> | En el instalador, **marcar "Add python.exe to PATH"** antes de pulsar *Install Now*. Sirve cualquier versión 3.11 o superior. |
| Node.js LTS | <https://nodejs.org/> | Instalar con las opciones por defecto. |
| WebView2 Runtime | <https://developer.microsoft.com/microsoft-edge/webview2/> | Viene instalado en Windows 11 y en casi todo Windows 10 actualizado. Solo descargarlo ("Evergreen Standalone Installer") si la ventana de la app no abre. |

Cerrar y volver a abrir PowerShell después de instalar, y comprobar:

```powershell
python --version    # debe mostrar Python 3.11 o superior
node --version
npm --version
```

Si `python` no se reconoce, Python se instaló sin "Add to PATH": reinstalarlo marcando esa casilla. Si `npm` falla con un mensaje sobre "la ejecución de scripts está deshabilitada", ejecutar `npm.cmd` en lugar de `npm` en los pasos siguientes.

### 2. Obtener el proyecto

Opción A — con Git:

```powershell
git clone https://github.com/USTA-OptiLab/OptiLab.git
cd OptiLab
git checkout development
```

Opción B — sin Git: en GitHub, botón verde **Code → Download ZIP** (rama `development`), descomprimir y entrar a la carpeta desde PowerShell:

```powershell
cd C:\ruta\donde\quedo\OptiLab
```

### 3. Instalar las dependencias (una sola vez, requiere internet)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .

cd frontend
npm install
npm run build
cd ..
```

- `python -m venv .venv` crea un entorno aislado; no hace falta "activarlo", los comandos de abajo llaman directamente a su Python.
- `npm run build` genera `frontend\dist`. **Este paso es obligatorio**: sin esa carpeta la app intenta conectarse a un servidor de desarrollo y se abre en blanco.
- La instalación descarga NumPy y SciPy, por lo que puede tardar unos minutos.

### 4. Abrir la aplicación

Desde la carpeta `OptiLab`:

```powershell
.\.venv\Scripts\python.exe -m optilab.app
```

Se abre la ventana de OptiLab con la portada y los 7 métodos. Desde ahí:

- Elegir un método con las tarjetas, con el cuadro rotativo ("Abrir método →") o con el buscador (**Ctrl + K**).
- **Inicio** (o **Esc**) vuelve a la portada.
- Cada método trae un ejemplo precargado o un botón "Cargar ejemplo" / "Ejemplo" para probarlo rápido, y luego **Resolver**.

Para volver a usarla otro día solo se repite el paso 4.

### 5. Si algo falla

| Síntoma | Solución |
| --- | --- |
| `python` o `pip` "no se reconoce como comando" | Reinstalar Python marcando **Add python.exe to PATH**, o usar `py -3.12` en lugar de `python`. |
| `.\.venv\Scripts\python.exe` no existe | El paso `python -m venv .venv` falló o se hizo en otra carpeta. Verificar con `cd` que se está dentro de `OptiLab` y repetirlo. |
| Error al instalar `pythonnet` o `pywebview` | Usar Python 3.12 o 3.13 de 64 bits y repetir el `pip install -e .`. |
| La ventana abre en blanco o no abre | Comprobar que existe `frontend\dist\index.html` (repetir `npm run build`) e instalar WebView2 Runtime. |
| `npm` bloqueado por la política de ejecución | Usar `npm.cmd install` y `npm.cmd run build`, o ejecutar `Set-ExecutionPolicy -Scope Process Bypass` en esa misma ventana. |
| Después de actualizar el código la app se ve igual | Repetir `npm run build` dentro de `frontend`. |

### Modo desarrollo en Windows (opcional)

Solo para quien edite el código. Abrir dos ventanas de PowerShell:

```powershell
# Ventana 1 (dentro de OptiLab\frontend)
npm run dev

# Ventana 2 (dentro de OptiLab)
$env:OPTILAB_DEV = "1"
.\.venv\Scripts\python.exe -m optilab.app
```

Para ejecutar las pruebas: `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` y luego `.\.venv\Scripts\python.exe -m pytest`.

## Repository layout

```
src/optilab/              Python package (pywebview app + Api exposed to JS)
src/optilab/app.py        Api class — the single bridge between frontend and Python
src/optilab/<method>/     one subpackage per optimization method (algorithm + entry point)
tests/                    pytest suite, one test module per method
frontend/                 Vue 3 + Tailwind + Vite app
frontend/src/App.vue      top-level Vue component, wires methods into the UI
frontend/src/<method>/    one folder per optimization method's Vue components
frontend/src/components/  shared components reused by 2+ methods
justfile                  task runner — source of truth for dev commands
pyproject.toml            Python package/deps config (ruff + pytest config lives here too)
```

## Adding a new optimization method

See [AGENTS.md](AGENTS.md#adding-a-new-optimization-method) for the step-by-step convention (backend subpackage → `Api` method → frontend folder → tests). `feat/doubolfeis-metod` is the branch to use as a reference example.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions, the PR process, and code style expectations. Agent-specific instructions (Claude Code, Codex, Gemini CLI) live in [AGENTS.md](AGENTS.md).
