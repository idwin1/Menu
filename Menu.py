import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import shutil
import json
import threading
import customtkinter as ctk
from datetime import datetime
import time

def obtener_ruta_raiz_real():
    """Detecta la carpeta raíz del proyecto de forma dinámica"""
    if getattr(sys, 'frozen', False):
        ruta = Path(sys.argv[0]).resolve().parent
    else:
        ruta = Path(__file__).resolve().parent
    
    if ruta.name.lower() == "apps":
        return ruta.parent
    return ruta

#docuementacion
def ejecutar_actualizador_con_ui(ruta_actualizador):
    """Muestra la UI de customtkinter y lee el progreso real del actualizador"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ANCHO = 850
    ALTO = 500

    ventana_carga = ctk.CTk()
    ventana_carga.title("Actualizador")
    ventana_carga.resizable(False, False)

    x = (ventana_carga.winfo_screenwidth() // 2) - (ANCHO // 2)
    y = (ventana_carga.winfo_screenheight() // 2) - (ALTO // 2)
    ventana_carga.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")
    ventana_carga.protocol("WM_DELETE_WINDOW", lambda: None) # Desactiva la 'X' para que no rompan el proceso

    # --- PANEL IZQUIERDO ---
    left = ctk.CTkFrame(ventana_carga, width=250, fg_color="#1f6aa5", corner_radius=0)
    left.pack(side="left", fill="y")
    ctk.CTkLabel(left, text="🚀", font=("Segoe UI Emoji", 80)).pack(pady=(70,20))
    ctk.CTkLabel(left, text="Actualizador", font=("Segoe UI",18)).pack(pady=5)
    ctk.CTkLabel(left, text="Buscando versión...", font=("Segoe UI",13)).pack(side="bottom", pady=30)

    # --- PANEL DERECHO ---
    right = ctk.CTkFrame(ventana_carga, corner_radius=0)
    right.pack(side="right", fill="both", expand=True)

    ctk.CTkLabel(right, text="Actualizando aplicación", font=("Segoe UI",28,"bold")).pack(pady=(30,10))
    
    mensaje = ctk.CTkLabel(right, text="Iniciando conexión", font=("Segoe UI",15))
    mensaje.pack()

    barra = ctk.CTkProgressBar(right, width=500, height=18, corner_radius=20)
    barra.pack(pady=(30,5))
    barra.set(0)

    porcentaje = ctk.CTkLabel(right, text="0 %", font=("Segoe UI",15,"bold"))
    porcentaje.pack()

    frame_estado = ctk.CTkFrame(right)
    frame_estado.pack(pady=20)

    lbl1 = ctk.CTkLabel(frame_estado, text="⟳ Buscar actualizaciones", anchor="w", width=300)
    lbl2 = ctk.CTkLabel(frame_estado, text="○ Descargar archivos", anchor="w", width=300)
    lbl3 = ctk.CTkLabel(frame_estado, text="○ Instalar actualización", anchor="w", width=300)
    lbl1.pack(anchor="w", padx=20, pady=3)
    lbl2.pack(anchor="w", padx=20, pady=3)
    lbl3.pack(anchor="w", padx=20, pady=3)

    logs = ctk.CTkTextbox(right, width=520, height=120, font=("Consolas",12))
    logs.pack(pady=10)
    logs.configure(state="disabled")

    def agregar_log(texto):
        hora = datetime.now().strftime("%H:%M:%S")
        logs.configure(state="normal")
        logs.insert("end", f"[{hora}] {texto}\n")
        logs.see("end")
        logs.configure(state="disabled")

    # --- LÓGICA DE INTERCEPTACIÓN ---
    estado_archivos = {"total": 1, "actual": 0}

    def procesar_actualizacion():
        try:
            # Ejecutamos redirigiendo la salida para leerla en tiempo real
            proceso = subprocess.Popen(
                [ruta_actualizador],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=0x08000000
            )

            for linea in iter(proceso.stdout.readline, ''):
                linea = linea.strip()
                if not linea: continue

                if linea.startswith("[UI] TAREAS:"):
                    estado_archivos["total"] = int(linea.split(":")[1])
                    ventana_carga.after(0, lambda: [
                        lbl1.configure(text="✔ Buscar actualizaciones"),
                        lbl2.configure(text="⟳ Descargar archivos")
                    ])
                
                elif linea.startswith("[UI] PROGRESO:"):
                    # Extraer el número y el texto: "[UI] PROGRESO:2|Descargando app.py"
                    _, datos = linea.split(":", 1)
                    paso_str, msg = datos.split("|", 1)
                    
                    estado_archivos["actual"] = int(paso_str)
                    progreso_real = estado_archivos["actual"] / estado_archivos["total"]
                    
                    ventana_carga.after(0, lambda m=msg, p=progreso_real: actualizar_visuales(m, p))
                    ventana_carga.after(0, lambda m=msg: agregar_log(m))
                
                elif linea.startswith("[UI] DONE"):
                    ventana_carga.after(0, finalizar_ui)
                
                else:
                    # Logs generales (errores de github, librerías, etc.)
                    ventana_carga.after(0, lambda l=linea: agregar_log(l))

            proceso.stdout.close()
            proceso.wait()

        except Exception as e:
            ventana_carga.after(0, lambda: agregar_log(f"Error crítico: {e}"))
            ventana_carga.after(3000, ventana_carga.destroy)

    def actualizar_visuales(msg, p):
        barra.set(p)
        porcentaje.configure(text=f"{int(p * 100)} %")
        mensaje.configure(text=msg)

    def finalizar_ui():
        barra.set(1.0)
        porcentaje.configure(text="100 %")
        mensaje.configure(text="¡Actualización completada!")
        lbl2.configure(text="✔ Descargar archivos")
        lbl3.configure(text="✔ Instalación completada")
        agregar_log("Todo está al día. Iniciando sistema...")
        # Espera 2.5 segundos para que el usuario lea que terminó, y cierra la ventana
        ventana_carga.after(2500, ventana_carga.quit)

    # Iniciar el hilo de lectura y arrancar la interfaz
    threading.Thread(target=procesar_actualizacion, daemon=True).start()
    ventana_carga.mainloop()
    ventana_carga.destroy()


def revisar_y_aplicar_actualizacion_menu():
    ruta_raiz = obtener_ruta_raiz_real()
    ruta_nuevo_menu = os.path.join(ruta_raiz, "apps", "Menu_NUEVO.exe")
    ruta_menu_actual = os.path.join(ruta_raiz, "Menu.exe")
    ruta_json = os.path.join(ruta_raiz, "apps", "config.json")
    ruta_actualizador = os.path.join(ruta_raiz, "apps", "actualizador.exe")
    ruta_actualizador_nuevo = os.path.join(ruta_raiz, "apps", "actualizador_NUEVO.exe")

    # --- PASO 1: TU RELEVO ORIGINAL DEL MENÚ (Funciona perfecto) ---
    estado_menu = 0
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
                estado_menu = datos.get("Estado_Menu", 0)
        except Exception:
            pass

    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        try:
            # 1. Copiar el Menu_NUEVO.exe sobre el Menu.exe de la raíz
            shutil.copy2(ruta_nuevo_menu, ruta_menu_actual)
            
            # 2. Cambiar de inmediato el estado en el JSON a 0
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                datos["Estado_Menu"] = 0
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
                
            # 3. Levantar el menú principal definitivo desde la raíz
            subprocess.Popen([ruta_menu_actual], cwd=ruta_raiz)
            
            # 4. Auto-eliminación original (El taskkill que tenías)
            comando_limpieza = f'taskkill /F /PID {os.getpid()} & timeout /t 1 /nobreak & del "{ruta_nuevo_menu}"'
            subprocess.Popen(comando_limpieza, shell=True, creationflags=0x08000000)
            
            os._exit(0)
        except Exception as e:
            print(f"Error crítico en el relevo por JSON: {e}")
            sys.exit(1)

    # --- PASO 2: EJECUCIÓN DE LA INTERFAZ DEL ACTUALIZADOR ---
    if os.path.exists(ruta_actualizador):
        ejecutar_actualizador_con_ui(ruta_actualizador)

    # --- PASO 3: LECTURA POST-ACTUALIZACIÓN ---
    estado_menu = 0
    estado_actualizador = 0
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
                estado_menu = datos.get("Estado_Menu", 0)
                estado_actualizador = datos.get("Estado_Actualizador", 0)
        except Exception:
            pass

    # --- PASO 4: RELEVO DEL ACTUALIZADOR (En silencio) ---
    if estado_actualizador == 1 and os.path.exists(ruta_actualizador_nuevo):
        try:
            shutil.copy2(ruta_actualizador_nuevo, ruta_actualizador) 
            os.remove(ruta_actualizador_nuevo)
            
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
            datos["Estado_Actualizador"] = 0
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    # --- PASO 5: TU LANZAMIENTO ORIGINAL DEL MENÚ ---
    # Si el actualizador detectó un menú nuevo, le pasamos la batuta al Menu_NUEVO.exe
    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        print("Sincronización de menú detectada. Iniciando proceso de relevo...")
        subprocess.Popen([ruta_nuevo_menu], cwd=ruta_raiz, creationflags=0x08000000)
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
                if exe.name.lower() not in ["actualizador.exe", "menu_nuevo.exe","actualizador_nuevo.exe"]
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