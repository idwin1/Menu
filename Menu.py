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

# Intentamos importar psutil para el hardware, si no está, no rompemos el programa
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def obtener_ruta_raiz_real():
    """Detecta la carpeta raíz del proyecto de forma dinámica"""
    if getattr(sys, 'frozen', False):
        ruta = Path(sys.argv[0]).resolve().parent
    else:
        ruta = Path(__file__).resolve().parent
    
    if ruta.name.lower() == "apps": 
        return ruta.parent
    return ruta

# =========================================================
# PALETA DE COLORES "DEEP ZINC" (Ultra Moderna)
# =========================================================
BG_APP = "#09090b"
BG_SIDEBAR = "#18181b"
BG_CARD = "#27272a"
BG_CARD_HOVER = "#3f3f46"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
BORDER = "#3f3f46"
TEXT_MAIN = "#fafafa"
TEXT_MUTED = "#a1a1aa"

# =========================================================
# ACTUALIZADOR (Diseño Moderno + Lógica Robusta)
# =========================================================
def ejecutar_actualizador_con_ui(ruta_actualizador):
    """Muestra la UI de customtkinter y lee el progreso real del actualizador"""
    ctk.set_appearance_mode("dark")
    ventana_carga = ctk.CTk()
    ventana_carga.title("Sincronización del Sistema")

    ancho = 850
    alto = 500
    ventana_carga.resizable(False, False)
    ventana_carga.configure(fg_color=BG_APP)

    # --- CENTRADO PERFECTO EN UNA SOLA LÍNEA ---
    ventana_carga.update_idletasks()
    x = int((ventana_carga.winfo_screenwidth() / 2) - (ancho / 2))
    y = int((ventana_carga.winfo_screenheight() / 2) - (alto / 2))
    ventana_carga.geometry(f"{ancho}x{alto}+{x}+{y}")
    ventana_carga.protocol("WM_DELETE_WINDOW", lambda: None) # Evita que la cierren

    # --- PANEL IZQUIERDO ---
    left = ctk.CTkFrame(ventana_carga, width=250, fg_color=BG_SIDEBAR, corner_radius=0)
    left.pack(side="left", fill="y")
    ctk.CTkLabel(left, text="🔄", font=("Segoe UI Emoji", 70)).pack(pady=(80,20))
    ctk.CTkLabel(left, text="M E N U", font=("Segoe UI", 18, "bold"), text_color=ACCENT).pack()
    ctk.CTkLabel(left, text="Update Center", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack()
    ctk.CTkLabel(left, text="Buscando versión...", font=("Segoe UI",13), text_color=TEXT_MUTED).pack(side="bottom", pady=30)

    # --- PANEL DERECHO ---
    right = ctk.CTkFrame(ventana_carga, fg_color=BG_APP, corner_radius=0)
    right.pack(side="right", fill="both", expand=True, padx=40, pady=40)

    ctk.CTkLabel(right, text="Actualizando Sistema", font=("Segoe UI", 26, "bold"), text_color=TEXT_MAIN, anchor="w").pack(fill="x", pady=(0, 10))
    
    mensaje = ctk.CTkLabel(right, text="Conectando al servidor...", font=("Segoe UI", 14), text_color=TEXT_MUTED, anchor="w")
    mensaje.pack(fill="x")

    barra = ctk.CTkProgressBar(right, width=500, height=12, corner_radius=10, progress_color=ACCENT, fg_color=BG_CARD)
    barra.pack(pady=(20, 5), fill="x")
    barra.set(0)
    
    porcentaje = ctk.CTkLabel(right, text="0 %", font=("Segoe UI", 14, "bold"), text_color=TEXT_MAIN)
    porcentaje.pack()

    frame_estado = ctk.CTkFrame(right, fg_color="transparent")
    frame_estado.pack(pady=10, fill="x")
    lbl1 = ctk.CTkLabel(frame_estado, text="⟳ Buscar actualizaciones", anchor="w", text_color=TEXT_MUTED)
    lbl2 = ctk.CTkLabel(frame_estado, text="○ Descargar archivos", anchor="w", text_color=TEXT_MUTED)
    lbl3 = ctk.CTkLabel(frame_estado, text="○ Instalar", anchor="w", text_color=TEXT_MUTED)
    lbl1.pack(anchor="w", pady=2); lbl2.pack(anchor="w", pady=2); lbl3.pack(anchor="w", pady=2)

    logs = ctk.CTkTextbox(right, height=100, font=("Consolas", 11), fg_color=BG_CARD, text_color=TEXT_MUTED, border_color=BORDER, border_width=1)
    logs.pack(fill="x", pady=(10,0))
    logs.configure(state="disabled")

    estado_archivos = {"total": 1, "actual": 0}

    def agregar_log(texto):
        hora = datetime.now().strftime("%H:%M:%S")
        logs.configure(state="normal")
        logs.insert("end", f"[{hora}] {texto}\n")
        
        # Mantener solo las últimas 100 líneas en RAM
        lineas_totales = int(logs.index('end-1c').split('.')[0])
        if lineas_totales > 100:
            logs.delete("1.0", f"{lineas_totales - 100}.0")

        logs.see("end")
        logs.configure(state="disabled")

    def actualizar_visuales(msg, p):
        barra.set(p)
        porcentaje.configure(text=f"{int(p * 100)} %")
        mensaje.configure(text=msg)

    def finalizar_ui():
        barra.set(1.0)
        porcentaje.configure(text="100 %", text_color=ACCENT)
        mensaje.configure(text="¡Sistema actualizado!", text_color=TEXT_MAIN)
        lbl2.configure(text="✔ Descargar archivos", text_color=ACCENT)
        lbl3.configure(text="✔ Instalación completada", text_color=ACCENT)
        agregar_log("Todo está al día. Iniciando sistema...")
        ventana_carga.after(2500, ventana_carga.quit)

    def procesar_actualizacion():
        try:
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
                        lbl1.configure(text="✔ Buscar actualizaciones", text_color=ACCENT), 
                        lbl2.configure(text="⟳ Descargar archivos", text_color=TEXT_MAIN)
                    ])
                elif linea.startswith("[UI] PROGRESO:"):
                    _, datos = linea.split(":", 1)
                    paso_str, msg = datos.split("|", 1)
                    estado_archivos["actual"] = int(paso_str)
                    progreso_real = estado_archivos["actual"] / estado_archivos["total"]
                    
                    ventana_carga.after(0, lambda m=msg, p=progreso_real: actualizar_visuales(m, p))
                    ventana_carga.after(0, lambda m=msg: agregar_log(m))
                elif linea.startswith("[UI] DONE"):
                    ventana_carga.after(0, finalizar_ui)
                else:
                    ventana_carga.after(0, lambda l=linea: agregar_log(l))
                    
            proceso.stdout.close()
            proceso.wait()
        except Exception as e:
            ventana_carga.after(0, lambda: agregar_log(f"Error crítico: {e}"))
            ventana_carga.after(3000, ventana_carga.destroy)

    threading.Thread(target=procesar_actualizacion, daemon=True).start()
    ventana_carga.mainloop()
    ventana_carga.destroy()


# =========================================================
# LÓGICA PRINCIPAL (5 Pasos de Relevo y Sincronización)
# =========================================================
def revisar_y_aplicar_actualizacion_menu():
    ruta_raiz = obtener_ruta_raiz_real()
    ruta_nuevo_menu = os.path.join(ruta_raiz, "apps", "Menu_NUEVO.exe")
    ruta_menu_actual = os.path.join(ruta_raiz, "Menu.exe")
    ruta_json = os.path.join(ruta_raiz, "apps", "config.json")
    ruta_actualizador = os.path.join(ruta_raiz, "apps", "actualizador.exe")
    ruta_actualizador_nuevo = os.path.join(ruta_raiz, "apps", "actualizador_NUEVO.exe")

    # --- PASO 1: RELEVO ORIGINAL DEL MENÚ ---
    estado_menu = 0
    actualizaciones_activas = True

    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
                estado_menu = datos.get("Estado_Menu", 0)
        except Exception:
            pass

    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        try:
            shutil.copy2(ruta_nuevo_menu, ruta_menu_actual)
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                datos["Estado_Menu"] = 0
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
            except Exception: pass

            subprocess.Popen([ruta_menu_actual], cwd=str(ruta_raiz))
            comando_limpieza = f'taskkill /F /PID {os.getpid()} & timeout /t 1 /nobreak & del "{ruta_nuevo_menu}"'
            subprocess.Popen(comando_limpieza, shell=True, creationflags=0x08000000)
            os._exit(0)
        except Exception as e:
            print(f"Error crítico en el relevo por JSON: {e}")
            sys.exit(1)

    # --- PASO 2: EJECUCIÓN DEL ACTUALIZADOR ---
    if os.path.exists(ruta_actualizador):
        if actualizaciones_activas:
            ejecutar_actualizador_con_ui(ruta_actualizador)
        else:
            print("Las actualizaciones automáticas están desactivadas por config.json")

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

    # --- PASO 4: RELEVO DEL ACTUALIZADOR ---
    if estado_actualizador == 1 and os.path.exists(ruta_actualizador_nuevo):
        try:
            shutil.copy2(ruta_actualizador_nuevo, ruta_actualizador) 
            os.remove(ruta_actualizador_nuevo)
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
            datos["Estado_Actualizador"] = 0
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception: pass

    # --- PASO 5: LANZAMIENTO SI HUBO ACTUALIZACIÓN DE MENÚ ---
    if estado_menu == 1 and os.path.exists(ruta_nuevo_menu):
        subprocess.Popen([ruta_nuevo_menu], cwd=str(ruta_raiz), creationflags=0x08000000)
        sys.exit(0)

# =========================================================
# Class ToolTip: para agregar mensajes emergentes a cualquier widget de Tkinter
# =========================================================
class ToolTip:
    def __init__(self, widget, text, delay=600):
        self.widget = widget
        self.text = text
        self.delay = delay  # Tiempo en milisegundos (600ms = 0.6 segundos)
        self.tooltip_window = None
        self.timer_id = None
        
        try:
            self.widget.bind("<Enter>", self.al_entrar)
            self.widget.bind("<Leave>", self.al_salir)
            self.widget.bind("<ButtonPress>", self.al_salir)
        except NotImplementedError:
            # Si el widget (como CTkSegmentedButton) bloquea el .bind(),
            # lo vinculamos directamente a su lienzo (_canvas) interno.
            if hasattr(self.widget, "_canvas"):
                self.widget._canvas.bind("<Enter>", self.al_entrar)
                self.widget._canvas.bind("<Leave>", self.al_salir)
                self.widget._canvas.bind("<ButtonPress>", self.al_salir)

    def al_entrar(self, event=None):
        self.cancelar_temporizador() # Asegura que no haya duplicados
        # Programa la aparición de la ventana después de 'delay' milisegundos
        self.timer_id = self.widget.after(self.delay, self.mostrar_tooltip)

    def al_salir(self, event=None):
        self.cancelar_temporizador()
        self.ocultar_tooltip()

    def cancelar_temporizador(self):
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None

    def mostrar_tooltip(self):
        if self.tooltip_window:
            return
            
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        
        # 1. TRUCO DE TRANSPARENCIA MEJORADO
        # Usamos un negro casi puro ("#000001") en lugar de magenta para 
        # que el suavizado de bordes se funda con el tema oscuro sin dejar rastro.
        color_invisible = "#000001"
        self.tooltip_window.configure(bg=color_invisible)
        self.tooltip_window.wm_attributes("-transparentcolor", color_invisible)

        # 2. CONTENEDOR CON BORDES REDONDEADOS
        frame_tooltip = ctk.CTkFrame(self.tooltip_window, 
                                     fg_color="#1e293b",       
                                     corner_radius=10,         
                                     border_width=1,           
                                     border_color="#3b82f6")   
        frame_tooltip.pack(padx=2, pady=2) 

        # 3. TEXTO
        label = ctk.CTkLabel(frame_tooltip, 
                             text=self.text, 
                             text_color="white",
                             fg_color="transparent",
                             font=("Segoe UI", 12),
                             wraplength=250, 
                             justify="left")
        label.pack(padx=12, pady=8)

        # 4. OBTENER TAMAÑO SOLICITADO
        self.tooltip_window.update_idletasks() 
        ancho_tooltip = frame_tooltip.winfo_reqwidth()
        alto_tooltip = frame_tooltip.winfo_reqheight()
        
        ancho_pantalla = self.widget.winfo_screenwidth()
        alto_pantalla = self.widget.winfo_screenheight()
        
        # 5. POSICIÓN (Centrado y ABAJO del componente)
        x = int(self.widget.winfo_rootx() + (self.widget.winfo_width() / 2) - (ancho_tooltip / 2))
        y = int(self.widget.winfo_rooty() + self.widget.winfo_height() + 10)
        
        # 6. CORRECCIÓN DE BORDES
        # Evitar que se salga por los lados
        if x < 0:
            x = 10
        elif (x + ancho_tooltip) > ancho_pantalla:
            x = ancho_pantalla - ancho_tooltip - 10
            
        # Evitar que se salga por abajo (si topa abajo, lo pasa para arriba)
        if (y + alto_tooltip) > alto_pantalla: 
            y = int(self.widget.winfo_rooty() - alto_tooltip - 10)
            
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
    
    def ocultar_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# =========================================================
# MENÚ PRINCIPAL: EL DASHBOARD "M E N U"
# =========================================================
class MenuporAplicaciones:
    def __init__(self, ventana_principal):
        self.root = ventana_principal
        self.root.title("Panel de Control - M E N U")

        # --- VENTANA COMPACTA ---
        ancho_ventana = 850
        alto_ventana = 550
        self.root.minsize(750, 450)
        self.root.configure(fg_color=BG_APP)

        # --- CENTRADO PERFECTO EN UNA SOLA LÍNEA ---
        self.root.update_idletasks()
        x = int((self.root.winfo_screenwidth() / 2) - (ancho_ventana / 2))
        y = int((self.root.winfo_screenheight() / 2) - (alto_ventana / 2))
        self.root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

        self.carpeta_apps = obtener_ruta_raiz_real() / "apps"
        
        # --- NUEVO: Leer configuración de tamaño guardada ---
        self.archivo_config = self.carpeta_apps / "config.json"
        self.tamano_vista = "Grande" # Tamaño por defecto
        if self.archivo_config.exists():
            try:
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    self.tamano_vista = json.load(f).get("Tamano_Vista", "Grande")
            except Exception: pass
        
        
        # --- SEGURIDAD AL CREAR DIRECTORIO ---
        try:
            if not self.carpeta_apps.exists():
                self.carpeta_apps.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo crear la carpeta 'apps' en:\n{self.carpeta_apps}\n\nError: {e}")

        self.apps_disponibles = []

        self.construir_dashboard()
        self.iniciar_reloj()

        # Iniciar lectura de hardware (RAM/CPU)
        if HAS_PSUTIL:
            psutil.cpu_percent() # Primera lectura en vacío para calibrar
        self.iniciar_monitoreo_sistema()

        self.cargar_datos_aplicaciones()

    def construir_dashboard(self):
        # ---------------- SIDEBAR (MENÚ LATERAL) ----------------
        self.sidebar = ctk.CTkFrame(self.root, width=200, fg_color=BG_SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="⚡", font=("Segoe UI Emoji", 38)).pack(pady=(25, 5))
        ctk.CTkLabel(self.sidebar, text="M E N U", font=("Segoe UI", 20, "bold"), text_color=ACCENT).pack()
        ctk.CTkLabel(self.sidebar, text="Control Center", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(pady=(0, 30))

        self.frame_reloj = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_reloj.pack(side="bottom", pady=25)
        self.lbl_hora = ctk.CTkLabel(self.frame_reloj, text="00:00:00", font=("Segoe UI", 22, "bold"), text_color=TEXT_MAIN)
        self.lbl_hora.pack()
        self.lbl_fecha = ctk.CTkLabel(self.frame_reloj, text="Lunes, 1 Enero", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.lbl_fecha.pack()

        # ---------------- ÁREA PRINCIPAL (DERECHA) ----------------
        self.main_area = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # 1. HEADER ROW
        self.header_row = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.header_row.pack(fill="x", pady=(0, 15))

        self.lbl_saludo = ctk.CTkLabel(self.header_row, text=self.obtener_saludo(), font=("Segoe UI", 24, "bold"), text_color=TEXT_MAIN)
        #ToolTip(self.lbl_saludo, "Saludo dinámico según la hora del día")
        self.lbl_saludo.pack(side="left")

        # --- NUEVO: Botón selector de tamaño ---
        self.seg_tamano = ctk.CTkSegmentedButton(
            self.header_row, 
            values=["Pequeño", "Mediano", "Grande"],
            command=self.cambiar_tamano_vista,
            fg_color=BG_CARD,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER
        )
        self.seg_tamano.set(self.tamano_vista)
        self.seg_tamano.pack(side="left", padx=20)
        #ToolTip(self.seg_tamano, "Cambiar tamaño de vista de las aplicaciones")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filtrar_aplicaciones)
        self.search_entry = ctk.CTkEntry(
            self.header_row, textvariable=self.search_var, placeholder_text="🔍 Buscar aplicación...",
            width=220, height=40, font=("Segoe UI", 13), fg_color=BG_CARD, border_color=BORDER, border_width=1, corner_radius=10
        )
        self.search_entry.pack(side="right")

        # 2. STATS ROW
        self.stats_row = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(0, 20))

        self.crear_stat_box(self.stats_row, "📦 Apps Instaladas", "Cargando...", "lbl_total_apps")
        self.crear_stat_box(self.stats_row, "🟢 Rendimiento", "Calculando...", "lbl_sistema")
        self.crear_stat_box(self.stats_row, "📂 Directorio", self.carpeta_apps.name, None)

        # 3. ÁREA DE CUADRÍCULA
        self.frame_scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.frame_scroll.pack(fill="both", expand=True)
        self.frame_scroll.grid_columnconfigure((0, 1, 2), weight=1)

    def cambiar_tamano_vista(self, valor_seleccionado):
        """Guarda la preferencia en config.json y redibuja la pantalla"""
        self.tamano_vista = valor_seleccionado
        
        try:
            datos = {}
            if self.archivo_config.exists():
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            
            datos["Tamano_Vista"] = self.tamano_vista
            
            with open(self.archivo_config, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando tamaño: {e}")
            
        # Redibujar la cuadrícula aplicando el filtro actual
        self.filtrar_aplicaciones()

    def crear_stat_box(self, parent, titulo, valor, attr_name):
        box = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10, height=65)
        box.pack(side="left", fill="x", expand=True, padx=4)
        box.pack_propagate(False)
        ctk.CTkLabel(box, text=titulo, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 0))
        lbl_valor = ctk.CTkLabel(box, text=valor, font=("Segoe UI", 14, "bold"), text_color=TEXT_MAIN)
        lbl_valor.pack(anchor="w", padx=12)
        if attr_name: setattr(self, attr_name, lbl_valor)

    def iniciar_monitoreo_sistema(self):
        """Actualiza en tiempo real el consumo de CPU y RAM"""
        if HAS_PSUTIL:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                self.lbl_sistema.configure(text=f"CPU {cpu}% | RAM {ram}%")
            except Exception:
                self.lbl_sistema.configure(text="Error de lectura")
        else:
            self.lbl_sistema.configure(text="Falta 'psutil'")
        self.root.after(2000, self.iniciar_monitoreo_sistema)

    def obtener_saludo(self):
        hora = datetime.now().hour
        if 5 <= hora < 12: return "☀️ Buenos días,"
        elif 12 <= hora < 20: return "🌤️ Buenas tardes,"
        else: return "🌙 Buenas noches,"

    def iniciar_reloj(self):
        ahora = datetime.now()
        self.lbl_hora.configure(text=ahora.strftime("%H:%M:%S"))
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        str_fecha = f"{dias[ahora.weekday()]}, {ahora.day} {meses[ahora.month-1]}"
        self.lbl_fecha.configure(text=str_fecha)
        self.root.after(1000, self.iniciar_reloj)

    def obtener_icono_por_nombre(self, nombre_archivo):
        nombre = nombre_archivo.lower()
        if any(w in nombre for w in ["calc", "math", "numero"]): return "🧮"
        if any(w in nombre for w in ["juego", "game"]): return "🎮"
        if any(w in nombre for w in ["web", "net", "chrome"]): return "🌐"
        if any(w in nombre for w in ["texto", "word", "ni"]): return "📄"
        if any(w in nombre for w in ["file","merge"]): return "📦"
        if any(w in nombre for w in ["evidencias"]): return "📁"
        if any(w in nombre for w in ["foto", "imagen", "diseño"]): return "🎨"
        if any(w in nombre for w in ["datos", "sql", "excel"]): return "📊"
        if any(w in nombre for w in ["limpiar", "clean", "hash", "md5"]): return "🔐"
        if any(w in nombre for w in ["tomarcaptura"]): return "📸"
        if any(w in nombre for w in ["insertdata"]): return "📈"
        return "✨"

    def cargar_datos_aplicaciones(self):
        if self.carpeta_apps.exists():
            self.apps_disponibles = [exe for exe in self.carpeta_apps.glob("*.exe") 
                                     if exe.name.lower() not in ["actualizador.exe", "menu_nuevo.exe", "actualizador_nuevo.exe"]]
        else: 
            self.apps_disponibles = []

        self.lbl_total_apps.configure(text=str(len(self.apps_disponibles)))
        self.mostrar_cuadricula(self.apps_disponibles)

    def filtrar_aplicaciones(self, *args):
        query = self.search_var.get().lower()
        filtradas = [exe for exe in self.apps_disponibles if query in exe.stem.lower()]
        self.mostrar_cuadricula(filtradas)

    def mostrar_cuadricula(self, lista_apps):
        for widget in self.frame_scroll.winfo_children(): 
            widget.destroy()

        if not lista_apps:
            ctk.CTkLabel(self.frame_scroll, text="📦 No hay aplicaciones en la carpeta\no no coinciden con la búsqueda.", font=("Segoe UI", 15), text_color=TEXT_MUTED).grid(row=0, column=1, pady=(60, 20))
            btn_refrescar = ctk.CTkButton(self.frame_scroll, text="🔄 Refrescar", font=("Segoe UI", 13, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, width=120, command=self.cargar_datos_aplicaciones)
            btn_refrescar.grid(row=1, column=1)
            return

        # --- LÓGICA DE ESCALADO DINÁMICO ---
        if self.tamano_vista == "Pequeño":
            columnas = 5
            w_card, h_card = 120, 135
            f_icon, f_title = 32, 11
            btn_h, btn_w = 26, 90
            pad_y_icon = (10, 5)
        elif self.tamano_vista == "Mediano":
            columnas = 4
            w_card, h_card = 140, 155
            f_icon, f_title = 36, 12
            btn_h, btn_w = 28, 100
            pad_y_icon = (12, 5)
        else: # Grande (Original)
            columnas = 3
            w_card, h_card = 160, 180
            f_icon, f_title = 42, 13
            btn_h, btn_w = 30, 120
            pad_y_icon = (15, 5)

        # Centrar las columnas dinámicamente
        for i in range(6): self.frame_scroll.grid_columnconfigure(i, weight=0)
        self.frame_scroll.grid_columnconfigure(tuple(range(columnas)), weight=1)

        fila, col = 0, 0

        for exe_path in lista_apps:
            icono = self.obtener_icono_por_nombre(exe_path.stem)

            tarjeta = ctk.CTkFrame(self.frame_scroll, fg_color=BG_CARD, corner_radius=12, width=w_card, height=h_card, border_width=2, border_color=BG_CARD)
            descripcion = self.buscar_descripcion(exe_path.stem)
            ToolTip(tarjeta, descripcion )


            tarjeta.grid_propagate(False)
            tarjeta.pack_propagate(False)
            tarjeta.grid(row=fila, column=col, padx=8, pady=8)

            lbl_icono = ctk.CTkLabel(tarjeta, text=icono, font=("Segoe UI Emoji", f_icon))
            lbl_icono.pack(pady=pad_y_icon)

            nombre_mostrar = exe_path.stem if len(exe_path.stem) < 15 else exe_path.stem[:12] + "..."
            lbl_nombre = ctk.CTkLabel(tarjeta, text=nombre_mostrar, font=("Segoe UI", f_title, "bold"), text_color=TEXT_MAIN)
            lbl_nombre.pack(pady=(0, 5))

            btn_abrir = ctk.CTkButton(
                tarjeta, text="Ejecutar", font=("Segoe UI", f_title-1, "bold"),
                fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, height=btn_h, width=btn_w,
                command=lambda e=exe_path: self.ejecutar_programa(e)
            )
            btn_abrir.pack(side="bottom", pady=(0, 10 if self.tamano_vista == "Pequeño" else 15))

            def hover_in(event, t=tarjeta): t.configure(border_color=ACCENT)
            def hover_out(event, t=tarjeta): t.configure(border_color=BG_CARD)

            tarjeta.bind("<Enter>", hover_in)
            tarjeta.bind("<Leave>", hover_out)
            lbl_icono.bind("<Enter>", hover_in)
            lbl_nombre.bind("<Enter>", hover_in)
            

            col += 1
            if col >= columnas:
                col = 0
                fila += 1

    def buscar_descripcion(self, exe_name):
        """Busca un archivo config.json con la misma base que el exe para mostrar descripción de cada aplicación"""
        ruta_raiz = obtener_ruta_raiz_real()
        ruta_json = os.path.join(ruta_raiz, "apps", "config.json")
        if os.path.exists(ruta_json):
                try:
                    with open(ruta_json, "r", encoding="utf-8") as f:
                        datos = json.load(f)
                        return datos.get("Descripcion", {}).get(exe_name.lower(), "") 
                except Exception:
                    pass
        
        

    def ejecutar_programa(self, ruta_exe):
        try:
            self.root.withdraw()
            self.root.update()
            # Lanzamos de forma independiente tal como estaba en la lógica principal (0x00000008)
            proceso = subprocess.Popen([str(ruta_exe)], cwd=str(ruta_exe.parent), creationflags=0x00000008)
            proceso.wait()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar:\n{e}")
        finally:
            self.search_var.set("") 
            self.cargar_datos_aplicaciones()
            self.root.deiconify()


if __name__ == "__main__":
    # 1. Aplicamos la lógica de revisión y actualización antes de arrancar la interfaz
    revisar_y_aplicar_actualizacion_menu()

    # 2. Arreglo para que se vea nítido en pantallas de alta resolución (DPI Aware)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass

    # 3. Lanzamos el Menú
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    app = MenuporAplicaciones(root)
    root.mainloop()
    