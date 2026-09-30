# app.py - Dashboard Web Predictor Deportivo
import streamlit as st
import mysql.connector
import math
from config import DB_CONFIG

# --- LÓGICA MATEMÁTICA ---
def calcular_poisson(k, lam):
    return ((math.e ** -lam) * (lam ** k)) / math.factorial(k)

def calcular_mercado_ou(lambda_total, linea):
    limite_entero = int(math.floor(linea))
    prob_under = sum(calcular_poisson(k, lambda_total) for k in range(limite_entero + 1))
    return prob_under, 1 - prob_under

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_data
def obtener_equipos_validos():
    """Consulta la base de datos para poblar los menús desplegables y evitar errores de tipeo."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor()
        cursor.execute("SELECT DISTINCT equipo_local FROM partidos_historicos ORDER BY equipo_local")
        equipos = [fila[0] for fila in cursor.fetchall()]
        return equipos
    except Exception as e:
        st.error(f"Error de conexión a MySQL: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_promedio_stat(equipo, es_local, tipo_stat):
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        columna = f"{tipo_stat}_local" if es_local else f"{tipo_stat}_visitante"
        columna_equipo = 'equipo_local' if es_local else 'equipo_visitante'
        
        query = f"SELECT AVG({columna}) as prom FROM partidos_historicos WHERE {columna_equipo} = %s"
        cursor.execute(query, (equipo,))
        resultado = cursor.fetchone()
        return float(resultado['prom']) if resultado and resultado['prom'] else 0
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="Predictor Deportivo UCL", layout="centered")

st.title("⚽ Predictor Estadístico - Champions League")
st.markdown("Modelo basado en la Distribución de Poisson utilizando datos históricos de la API-Sports.")

equipos_disponibles = obtener_equipos_validos()

if not equipos_disponibles:
    st.warning("No se encontraron equipos en la base de datos. Ejecuta tu extractor.py primero.")
else:
    # 1. Zona de Selección (Validación estricta por selectbox)
    st.subheader("Selección de Equipos")
    col1, col2 = st.columns(2)
    with col1:
        equipo_L = st.selectbox("Equipo Local", options=equipos_disponibles, index=0)
    with col2:
        equipo_V = st.selectbox("Equipo Visitante", options=equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0)

    if st.button("Calcular Pronóstico", type="primary"):
        if equipo_L == equipo_V:
            st.error("Por favor, selecciona dos equipos diferentes.")
        else:
            with st.spinner('Analizando datos históricos...'):
                # Extracción de promedios
                goles_L = obtener_promedio_stat(equipo_L, True, 'goles')
                goles_V = obtener_promedio_stat(equipo_V, False, 'goles')
                corners_L = obtener_promedio_stat(equipo_L, True, 'corners')
                corners_V = obtener_promedio_stat(equipo_V, False, 'corners')

                if goles_L == 0 or goles_V == 0:
                    st.error("Datos insuficientes para realizar un pronóstico fiable entre estos equipos.")
                else:
                    # Cálculo Matriz 1X2
                    prob_local = prob_empate = prob_visitante = 0
                    for gL in range(6):
                        for gV in range(6):
                            prob = calcular_poisson(gL, goles_L) * calcular_poisson(gV, goles_V)
                            if gL > gV: prob_local += prob
                            elif gL < gV: prob_visitante += prob
                            else: prob_empate += prob

                    # Cálculo Over/Under
                    total_goles = goles_L + goles_V
                    total_corners = corners_L + corners_V
                    u_goles, o_goles = calcular_mercado_ou(total_goles, 2.5)
                    u_corners, o_corners = calcular_mercado_ou(total_corners, 8.5)

                    # 2. Zona de Resultados Web
                    st.divider()
                    st.subheader("📊 Probabilidades del Partido (1X2)")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"Victoria {equipo_L}", f"{prob_local * 100:.2f}%")
                    c2.metric("Empate", f"{prob_empate * 100:.2f}%")
                    c3.metric(f"Victoria {equipo_V}", f"{prob_visitante * 100:.2f}%")

                    st.progress(prob_local, text=f"Dominio Local ({prob_local * 100:.2f}%)")

                    st.subheader("📈 Mercados Alternativos")
                    col_g, col_c = st.columns(2)
                    with col_g:
                        st.markdown("**Goles Totales (Línea 2.5)**")
                        st.write(f"🟢 OVER (+2.5): **{o_goles * 100:.2f}%**")
                        st.write(f"🔴 UNDER (-2.5): **{u_goles * 100:.2f}%**")
                    with col_c:
                        st.markdown("**Tiros de Esquina (Línea 8.5)**")
                        st.write(f"🟢 OVER (+8.5): **{o_corners * 100:.2f}%**")
                        st.write(f"🔴 UNDER (-8.5): **{u_corners * 100:.2f}%**")