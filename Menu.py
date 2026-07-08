import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import shutil

def obtener_ruta_raiz_real():
    """Detecta con precisión la carpeta donde reside el ejecutable real o el script"""
    if getattr(sys, 'frozen', False):
        return Path(sys.argv[0]).resolve().parent
    else:
        return Path(__file__).resolve().parent

def revisar_y_aplicar_actualizacion_menu():
    ruta_raiz = obtener_ruta_raiz_real()
    ruta_nuevo_menu = os.path.join(ruta_raiz, "apps", "Menu_NUEVO.exe")
    ruta_menu_actual = os.path.join(ruta_raiz, "Menu.exe")

    # --- PASO 2: Si fuimos invocados desde la carpeta apps para hacer el reemplazo ---
    if "--reemplazar" in sys.argv:
        try:
            idx = sys.argv.index("--reemplazar")
            ruta_origen_nuevo = sys.argv[idx + 1]
            
            shutil.copy2(ruta_origen_nuevo, ruta_menu_actual)
            
            # Volvemos a iniciar el menú de la raíz de manera normal
            subprocess.Popen([ruta_menu_actual])
            sys.exit(0)
        except Exception as e:
            print(f"Error al reemplazar el Menú: {e}")
            sys.exit(1)

    # --- PASO 1: Ejecución normal del Menú ---
    ruta_actualizador = os.path.join(ruta_raiz, "apps", "actualizador.exe")
    if os.path.exists(ruta_actualizador):
        try:
            subprocess.run([ruta_actualizador], creationflags=0x08000000, timeout=15)
        except subprocess.TimeoutExpired:
            print("El actualizador tardó demasiado, continuando inicio...")
        except Exception as e:
            print(f"No se pudo lanzar el actualizador: {e}")

    if os.path.exists(ruta_nuevo_menu):
        print("Detectada actualización del menú principal. Reiniciando por relevo...")
        subprocess.Popen([ruta_nuevo_menu, "--reemplazar", ruta_nuevo_menu], creationflags=0x00000008)
        sys.exit(0)


class MenuporAplicaciones:
    def __init__(self, ventana_principal):
        self.root = ventana_principal
        self.root.title("Menú de Aplicaciones")
        self.root.geometry("380x450")
        self.root.resizable(False, False)
        
        # Uso unificado de la función de detección ultra-precisa
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
            # Traemos todos los .exe y FILTRAMOS los del sistema de actualización
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
            self.root.withdraw()
            subprocess.run([str(ruta_exe)], cwd=str(ruta_exe.parent), check=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el programa:\n{e}")
        finally:
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