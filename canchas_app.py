import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time
import os

# --- CONFIGURACIÓN Y CARPETAS ---
# Definimos la ruta específica que solicitaste
ruta_reportes = r"C:\Users\Mi PC\Documents\registro canchas"

# Verificamos si la carpeta existe, si no, la creamos
if not os.path.exists(ruta_reportes):
    try:
        os.makedirs(ruta_reportes)
    except Exception as e:
        # Respaldo en caso de error de permisos en Windows
        ruta_reportes = 'reportes'
        if not os.path.exists(ruta_reportes):
            os.makedirs(ruta_reportes)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('gestion_canchas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  cancha TEXT, inicio TEXT, fin TEXT, 
                  total REAL, fecha TEXT)''')
    conn.commit()
    conn.close()

def registrar_venta(cancha, inicio, fin, total):
    conn = sqlite3.connect('gestion_canchas.db')
    c = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO ventas (cancha, inicio, fin, total, fecha) VALUES (?,?,?,?,?)",
              (cancha, inicio, fin, total, fecha_hoy))
    conn.commit()
    conn.close()
    # Guardar automáticamente en la ruta especificada
    actualizar_reporte_diario()

def eliminar_registro(id_registro):
    conn = sqlite3.connect('gestion_canchas.db')
    c = conn.cursor()
    c.execute("DELETE FROM ventas WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()
    actualizar_reporte_diario()

def actualizar_reporte_diario():
    """Guarda automáticamente la contabilidad en la ruta de Documentos"""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('gestion_canchas.db')
    df = pd.read_sql_query(f"SELECT * FROM ventas WHERE fecha='{fecha_hoy}'", conn)
    conn.close()
    if not df.empty:
        # Creamos la ruta completa combinando la carpeta y el nombre del archivo
        nombre_archivo = f"contabilidad_{fecha_hoy}.csv"
        ruta_completa = os.path.join(ruta_reportes, nombre_archivo)
        df.to_csv(ruta_completa, index=False, encoding='utf-8-sig')

# --- INTERFAZ ---
init_db()
st.set_page_config(page_title="Control Canchas Familia Cerón", layout="wide")

st.markdown("""
    <style>
    .estado-disponible { color: #28a745; font-weight: bold; font-size: 20px; }
    .estado-ocupado { color: #dc3545; font-weight: bold; font-size: 20px; }
    .cronometro { font-family: 'Courier New', monospace; font-size: 35px; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; text-align: center; }
    .descuento-alerta { color: #ff4b4b; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏟️ Gestión de Canchas Familia Cerón")
st.info(f"Reportes guardados en: {ruta_reportes}")

TARIF_HORA = 130000

# Inicializamos solo 2 canchas
if 'canchas' not in st.session_state:
    st.session_state.canchas = {f"Cancha {i}": {"activa": False, "inicio": None} for i in range(1, 3)}

# --- PANEL DE CANCHAS (2 Columnas) ---
cols = st.columns(2)

for i, (nombre, datos) in enumerate(st.session_state.canchas.items()):
    with cols[i]:
        st.subheader(nombre)
        container = st.container(border=True)
        
        if not datos["activa"]:
            container.markdown('<p class="estado-disponible">🟢 DISPONIBLE</p>', unsafe_allow_html=True)
            if container.button(f"EMPEZAR JUEGO", key=f"start_{i}", use_container_width=True):
                datos["activa"] = True
                datos["inicio"] = datetime.now()
                st.rerun()
        else:
            container.markdown('<p class="estado-ocupado">🔴 EN USO</p>', unsafe_allow_html=True)
            
            ahora = datetime.now()
            transcurrido = ahora - datos["inicio"]
            segundos = int(transcurrido.total_seconds())
            
            h, r = divmod(segundos, 3600)
            m, s = divmod(r, 60)
            
            cobro_base = (segundos / 3600) * TARIF_HORA
            
            valor_descuento = container.number_input("Descuento ($)", min_value=0, step=1000, key=f"desc_{i}")
            cobro_final = max(0, cobro_base - valor_descuento)
            
            container.markdown(f'<p class="cronometro">{h:02d}:{m:02d}:{s:02d}</p>', unsafe_allow_html=True)
            
            if valor_descuento > 0:
                container.write(f"**Base:** ${cobro_base:,.0f}")
                container.markdown(f'<p class="descuento-alerta">Menos Descuento: -${valor_descuento:,.0f}</p>', unsafe_allow_html=True)
                container.write(f"### Total: ${cobro_final:,.0f}")
            else:
                container.write(f"### Cobro: ${cobro_final:,.0f} COP")
            
            if container.button(f"FINALIZAR Y COBRAR", key=f"stop_{i}", use_container_width=True, type="primary"):
                registrar_venta(nombre, datos["
