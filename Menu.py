import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
import shutil
import json
import threading

def obtener_ruta_raiz_real():
    """Detecta la carpeta raíz del proyecto de forma dinámica"""
    if getattr(sys, 'frozen', False):
        ruta = Path(sys.argv[0]).resolve().parent
    else:
        ruta = Path(__file__).resolve().parent
    
    if ruta.name.lower() == "apps":
        return ruta.parent
    return ruta

def ejecutar_actualizador_con_ui(ruta_actualizador):
    """Muestra una pantalla de carga mientras el actualizador corre en segundo plano"""
    ventana_carga = tk.Tk()
    ventana_carga.title("Buscando actualizaciones")
    ventana_carga.geometry("320x120")
    ventana_carga.resizable(False, False)
    
    # Truco para centrar la ventanita en la pantalla
    ventana_carga.eval('tk::PlaceWindow . center')
    
    lbl_info = tk.Label(ventana_carga, text="Buscando y descargando actualizaciones...\nPor favor, no cierres el programa.", font=("Arial", 10))
    lbl_info.pack(pady=15)
    
    # Barra de progreso en modo 'indeterminate' (movimiento continuo)
    barra = ttk.Progressbar(ventana_carga, mode='indeterminate', length=250)
    barra.pack(pady=5)
    barra.start(15) # Velocidad de la animación
    
    def hilo_actualizador():
        try:
            # Ejecutamos el actualizador (esto tomará su tiempo)
            subprocess.run([ruta_actualizador], creationflags=0x08000000, timeout=50)
        except subprocess.TimeoutExpired:
            print("El actualizador tardó demasiado tiempo en responder.")
        except Exception as e:
            print(f"No se pudo lanzar el actualizador: {e}")
        finally:
            # Cuando el actualizador termine (o falle), cerramos la ventana de carga de forma segura
            ventana_carga.after(0, ventana_carga.destroy)

    # Iniciamos el proceso de actualización en un hilo aparte
    hilo = threading.Thread(target=hilo_actualizador, daemon=True)
    hilo.start()
    
    # Iniciamos el bucle de la ventana para que se vea la animación
    ventana_carga.mainloop()

def revisar_y_aplicar_actualizacion_menu():
    ruta_raiz = obtener_ruta_raiz_real()
    ruta_nuevo_menu = os.path.join(ruta_raiz, "apps", "Menu_NUEVO.exe")
    ruta_menu_actual = os.path.join(ruta_raiz, "Menu.exe")
    ruta_json = os.path.join(ruta_raiz, "apps", "config.json")

    # Leer el estado desde el JSON de forma segura
    estado_menu = 0
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
                estado_menu = datos.get("Estado_Menu", 0)
        except Exception:
            estado_menu = 0

    # --- PASO 1: SI EL ESTADO ES 1, EJECUTAMOS EL RELEVO DE FORMA INMEDIATA ---
    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        try:
            # 1. Copiar el Menu_NUEVO.exe sobre el Menu.exe de la raíz
            shutil.copy2(ruta_nuevo_menu, ruta_menu_actual)
            
            # 2. Cambiar de inmediato el estado en el JSON a 0 para que nadie vuelva a entrar aquí
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                datos["Estado_Menu"] = 0
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
                
            # 3. Levantar el menú principal definitivo desde la raíz
            subprocess.Popen([ruta_menu_actual])
            
            # 4. Forzar la auto-eliminación de Menu_NUEVO.exe de forma asíncrona
            comando_limpieza = f'taskkill /F /PID {os.getpid()} & timeout /t 1 /nobreak & del "{ruta_nuevo_menu}"'
            subprocess.Popen(comando_limpieza, shell=True, creationflags=0x08000000)
            
            os._exit(0) # Terminar el proceso hijo inmediatamente
        except Exception as e:
            print(f"Error crítico en el relevo por JSON: {e}")
            sys.exit(1)

    # --- PASO 2: EJECUCIÓN NORMAL (Solo si Estado_Menu es 0) ---
    ruta_actualizador = os.path.join(ruta_raiz, "apps", "actualizador.exe")
    if os.path.exists(ruta_actualizador):
        ejecutar_actualizador_con_ui(ruta_actualizador)

    # Volvemos a leer el JSON tras la ejecución del actualizador para ver si dejó una orden de cambio (Estado 1)
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
                estado_menu = datos.get("Estado_Menu", 0)
        except Exception:
            estado_menu = 0

    # Si el actualizador dejó un estado 1 y el ejecutable existe, lanzamos el relevo
    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        print("Sincronización de menú detectada en JSON. Iniciando proceso de relevo...")
        subprocess.Popen([ruta_nuevo_menu], creationflags=0x08000000)
        sys.exit(0)


class MenuporAplicaciones:
    def __init__(self, ventana_principal):
        self.root = ventana_principal
        self.root.title("Menú de Aplicaciones")
        self.root.geometry("380x450")
        self.root.resizable(False, False)
        
        ruta_base = obtener_ruta_raiz_real()
        self.carpeta_apps = ruta_base / "apps"
        
        try:
            if not self.carpeta_apps.exists():
                self.carpeta_apps.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo crear la carpeta 'apps' en:\n{self.carpeta_apps}\n\nError: {e}")

        lbl_titulo = tk.Label(self.root, text="Panel de Control", font=("Arial", 14, "bold"), pady=10)
        lbl_titulo.pack()

        self.lbl_ruta = tk.Label(self.root, text=f"Carpeta activa: {self.carpeta_apps}", font=("Arial", 8, "italic"), fg="#777777", wraplength=340)
        self.lbl_ruta.pack(pady=(0, 10))

        self.frame_contenedor = tk.Frame(self.root)
        self.frame_contenedor.pack(fill="both", expand=True, padx=20, pady=10)

        self.cargar_aplicaciones()

    def cargar_aplicaciones(self):
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()

        if not self.carpeta_apps.exists():
            ejecutables = []
        else:
            todos_los_exe = list(self.carpeta_apps.glob("*.exe"))
            ejecutables = [
                exe for exe in todos_los_exe 
                if exe.name.lower() not in ["actualizador.exe", "menu_nuevo.exe"]
            ]

        if not ejecutables:
            lbl_vacio = tk.Label(self.frame_contenedor, text="La carpeta 'apps' está vacía.\nColoca tus archivos .exe dentro de ella.", fg="#777777", font=("Arial", 9), justify="center")
            lbl_vacio.pack(pady=20)
            
            btn_refrescar = tk.Button(self.frame_contenedor, text="🔄 Buscar de nuevo", command=self.cargar_aplicaciones, bg="#9C27B0", fg="white", font=("Arial", 10))
            btn_refrescar.pack(pady=10)
            return

        for exe_path in ejecutables:
            btn = tk.Button(
                self.frame_contenedor,
                text=f"🚀 {exe_path.stem}",
                command=lambda exe=exe_path: self.ejecutar_programa(exe),
                bg="#2196F3",
                fg="white",
                font=("Arial", 10, "bold"),
                height=2,
                bd=2,
                relief="groove"
            )
            btn.pack(fill="x", pady=5)

    def ejecutar_programa(self, ruta_exe):
        try:
            # Ocultamos la interfaz del menú
            self.root.withdraw()
            
            # CORRECCIÓN DE PROCESO COLGADO: Lanzamos la aplicación de forma totalmente 
            # independiente (0x00000008) para que Windows no encadene los subprocesos.
            proceso = subprocess.Popen(
                [str(ruta_exe)], 
                cwd=str(ruta_exe.parent),
                creationflags=0x00000008
            )
            
            # Esperamos de forma limpia a que el proceso termine sin congelar los hilos del sistema
            proceso.wait()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el programa:\n{e}")
        finally:
            # Regresamos el menú a la pantalla y refrescamos los botones
            self.root.deiconify()
            self.cargar_aplicaciones()


if __name__ == "__main__":
    revisar_y_aplicar_actualizacion_menu()
    
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = MenuporAplicaciones(root)
    root.mainloop()