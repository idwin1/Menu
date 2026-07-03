import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

class MenuporAplicaciones:
    def __init__(self, ventana_principal):
        self.root = ventana_principal
        self.root.title("Menú de Aplicaciones")
        self.root.geometry("380x450")
        self.root.resizable(False, False)
        
        # 1. DETECCIÓN ULTRA-PRECISA DE LA UBICACIÓN REAL
        # sys.argv[0] contiene la ruta exacta desde donde el sistema operativo invocó el ejecutable/script
        if getattr(sys, 'frozen', False):
            # Si es el .exe compilado, obtenemos el directorio del archivo ejecutable real
            ruta_base = Path(sys.argv[0]).resolve().parent
        else:
            # Si se corre desde VS Code (.py normal)
            ruta_base = Path(__file__).resolve().parent

        # 2. Definir la ruta de la carpeta 'apps'
        self.carpeta_apps = ruta_base / "apps"
        
        # 3. FORZAR LA CREACIÓN DE LA CARPETA EN LA UBICACIÓN REAL
        try:
            if not self.carpeta_apps.exists():
                self.carpeta_apps.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo crear la carpeta 'apps' en:\n{self.carpeta_apps}\n\nError: {e}")

        # Encabezado de la interfaz
        lbl_titulo = tk.Label(
            self.root, 
            text="Panel de Control", 
            font=("Arial", 14, "bold"), 
            pady=10
        )
        lbl_titulo.pack()

        # Mostrar la ruta completa en la interfaz para que confirmes dónde la está buscando
        self.lbl_ruta = tk.Label(
            self.root, 
            text=f"Carpeta activa: {self.carpeta_apps}", 
            font=("Arial", 8, "italic"), 
            fg="#777777",
            wraplength=340
        )
        self.lbl_ruta.pack(pady=(0, 10))

        # Contenedor para los botones
        self.frame_contenedor = tk.Frame(self.root)
        self.frame_contenedor.pack(fill="both", expand=True, padx=20, pady=10)

        # Cargar los botones de las aplicaciones
        self.cargar_aplicaciones()

    def cargar_aplicaciones(self):
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()

        # Buscar todos los archivos .exe en la carpeta 'apps'
        if not self.carpeta_apps.exists():
            ejecutables = []
        else:
            ejecutables = list(self.carpeta_apps.glob("*.exe"))

        if not ejecutables:
            lbl_vacio = tk.Label(
                self.frame_contenedor, 
                text=f"La carpeta 'apps' está vacía.\nColoca tus archivos .exe dentro de ella.", 
                fg="#777777",
                font=("Arial", 9),
                justify="center"
            )
            lbl_vacio.pack(pady=20)
            
            btn_refrescar = tk.Button(
                self.frame_contenedor,
                text="🔄 Buscar de nuevo",
                command=self.cargar_aplicaciones,
                bg="#9C27B0",
                fg="white",
                font=("Arial", 10)
            )
            btn_refrescar.pack(pady=10)
            return

        # Generar un botón por cada .exe encontrado
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
            self.root.withdraw()  # Ocultar menú
            subprocess.run([str(ruta_exe)], cwd=str(ruta_exe.parent), check=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el programa:\n{e}")
        finally:
            self.root.deiconify()  # Volver a mostrar el menú
            self.cargar_aplicaciones()


if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = MenuporAplicaciones(root)
    root.mainloop()