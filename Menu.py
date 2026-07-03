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
        
        # Definir la carpeta donde estarán los ejecutables
        # En este caso, una carpeta llamada 'apps' al lado de este script/ejecutable
        self.carpeta_apps = Path(__file__).parent / "apps"
        
        # Crear la carpeta si no existe
        if not self.carpeta_apps.exists():
            self.carpeta_apps.mkdir(parents=True, exist_ok=True)

        # Encabezado
        lbl_titulo = tk.Label(
            self.root, 
            text="Panel de Control", 
            font=("Arial", 14, "bold"), 
            pady=10
        )
        lbl_titulo.pack()

        lbl_subtitulo = tk.Label(
            self.root, 
            text="Selecciona la aplicación que deseas ejecutar:", 
            font=("Arial", 10, "italic"), 
            fg="#555555"
        )
        lbl_subtitulo.pack(pady=(0, 10))

        # Contenedor con scroll por si tienes muchos .exe
        self.frame_contenedor = tk.Frame(self.root)
        self.frame_contenedor.pack(fill="both", expand=True, padx=20, pady=10)

        # Cargar los botones de las aplicaciones
        self.cargar_aplicaciones()

    def cargar_aplicaciones(self):
        # Limpiar el contenedor por si se refresca
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()

        # Buscar todos los archivos .exe en la carpeta 'apps'
        ejecutables = list(self.carpeta_apps.glob("*.exe"))

        if not ejecutables:
            lbl_vacio = tk.Label(
                self.frame_contenedor, 
                text=f"No se encontraron archivos .exe en:\n/apps", 
                fg="red",
                font=("Arial", 10)
            )
            lbl_vacio.pack(pady=20)
            return

        # Generar un botón por cada .exe encontrado
        for exe_path in ejecutables:
            # Usamos una función lambda con un argumento por defecto (exe=exe_path) 
            # para evitar el problema de que todos los botones apunten al último elemento
            btn = tk.Button(
                self.frame_contenedor,
                text=f"🚀 {exe_path.stem}",  # Muestra el nombre sin el '.exe'
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
            # 1. Ocultar el menú principal
            self.root.withdraw()
            
            # 2. Ejecutar el .exe y ESPERAR a que se cierre (subprocess.run)
            # Pasamos el directorio de trabajo (cwd) para que el .exe encuentre sus dependencias si las tiene
            subprocess.run([str(ruta_exe)], cwd=str(ruta_exe.parent), check=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el programa:\n{e}")
        
        finally:
            # 3. Al cerrarse el .exe (o si falla), regresa y vuelve a mostrar el menú
            self.root.deiconify()


if __name__ == "__main__":
    # Configuración para evitar que se vea borroso en pantallas con escalado (Windows)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = MenuporAplicaciones(root)
    root.mainloop()