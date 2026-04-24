import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

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

def eliminar_registro(id_registro):
    conn = sqlite3.connect('gestion_canchas.db')
    c = conn.cursor()
    c.execute("DELETE FROM ventas WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()

# --- INTERFAZ ---
init_db()
st.set_page_config(page_title="Control Canchas familia ceron", layout="wide")

st.markdown("""
    <style>
    .estado-disponible { color: #28a745; font-weight: bold; font-size: 20px; }
    .estado-ocupado { color: #dc3545; font-weight: bold; font-size: 20px; }
    .cronometro { font-family: 'Courier New', monospace; font-size: 35px; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; text-align: center; }
    .descuento-alerta { color: #ff4b4b; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏟️ Gestión de Canchas familia ceron - Tarifa: $130.000/hr")

TARIF_HORA = 130000

if 'canchas' not in st.session_state:
    st.session_state.canchas = {f"Cancha {i}": {"activa": False, "inicio": None} for i in range(1, 5)}

# --- PANEL DE CANCHAS ---
cols = st.columns(4)

for i, (nombre, datos) in enumerate(st.session_state.canchas.items()):
    with cols[i]:
        st.subheader(nombre)
        container = st.container(border=True)
        
        if not datos["activa"]:
            container.markdown('<p class="estado-disponible">🟢 DISPONIBLE</p>', unsafe_allow_html=True)
            if container.button(f"EMPEZAR JUEGO", key=f"start_{i}"):
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
            
            # Cálculo base del cobro
            cobro_base = (segundos / 3600) * TARIF_HORA
            
            # --- NUEVA OPCIÓN: DESCUENTO EN PESOS ---
            # Agregamos un campo para ingresar el valor en pesos a descontar
            valor_descuento = container.number_input("Descuento ($)", min_value=0, step=1000, key=f"desc_pesos_{i}")
            
            # Calculamos el cobro final (asegurando que no sea menor a cero)
            cobro_final = max(0, cobro_base - valor_descuento)
            
            container.markdown(f'<p class="cronometro">{h:02d}:{m:02d}:{s:02d}</p>', unsafe_allow_html=True)
            
            if valor_descuento > 0:
                container.write(f"**Base:** ${cobro_base:,.0f}")
                container.markdown(f'<p class="descuento-alerta">Menos Descuento: -${valor_descuento:,.0f}</p>', unsafe_allow_html=True)
                container.write(f"### Total: ${cobro_final:,.0f}")
            else:
                container.write(f"**Cobro:** ${cobro_final:,.0f} COP")
            
            if container.button(f"FINALIZAR Y COBRAR", key=f"stop_{i}"):
                registrar_venta(nombre, datos["inicio"].strftime("%H:%M:%S"), ahora.strftime("%H:%M:%S"), round(cobro_final, 0))
                datos["activa"] = False
                datos["inicio"] = None
                st.rerun()

st.divider()

# --- CONTADURÍA ---
st.header("📊 Contabilidad del Día")

conn = sqlite3.connect('gestion_canchas.db')
fecha_actual = datetime.now().strftime("%Y-%m-%d")
df = pd.read_sql_query(f"SELECT * FROM ventas WHERE fecha='{fecha_actual}'", conn)
conn.close()

if not df.empty:
    m1, m2 = st.columns(2)
    m1.metric("Veces utilizadas hoy", len(df))
    m2.metric("Dinero conseguido hoy", f"${df['total'].sum():,.0f} COP")
    
    with st.expander("⚙️ Administrar registros"):
        for index, row in df.iterrows():
            r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1, 2, 2, 2, 1])
            r_col1.write(f"#{row['id']}")
            r_col2.write(f"**{row['cancha']}**")
            r_col3.write(f"{row['inicio']} - {row['fin']}")
            r_col4.write(f"${row['total']:,.0f}")
            if r_col5.button("🗑️", key=f"del_{row['id']}"):
                eliminar_registro(row['id'])
                st.rerun()
else:
    st.info("No hay movimientos registrados para hoy.")

# Auto-actualización cada segundo para que el cronómetro se mueva
time.sleep(1)
st.rerun()