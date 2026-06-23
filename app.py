import streamlit as st
import numpy as np
import pandas as pd

class Metodo5Calibracion:
    """
    Motor termodinámico estricto para calibración de consolas de muestreo (EPA Método 5).
    Resuelve el factor de calibración del medidor (Y) y el orificio (Delta H@).
    """
    T_STD = 293.15  # K (68 °F)
    P_STD = 760.0   # mm Hg (29.92 in Hg)
    K1 = 0.0319     # Constante para cálculo de dH@

    def __init__(self, pb: float):
        self.pb = pb

    def calcular_parametros(self, 
                            vw: np.ndarray, tw: np.ndarray, 
                            vm: np.ndarray, tm: np.ndarray, 
                            dh: np.ndarray, theta: np.ndarray) -> dict:
        
        pm = self.pb + (dh / 13.6)
        y_vector = (vw * self.pb * tm) / (vm * pm * tw)
        dh_arroba_vector = (self.K1 * dh * tm * (theta ** 2)) / (self.pb * (y_vector ** 2) * (vm ** 2))
        incertidumbre_y = np.std(y_vector, ddof=1) 
        
        return {
            "y_individuales": y_vector.tolist(),
            "y_promedio": float(np.mean(y_vector)),
            "dh_arroba_individuales": dh_arroba_vector.tolist(),
            "dh_arroba_promedio": float(np.mean(dh_arroba_vector)),
            "incertidumbre_y": float(incertidumbre_y),
            "estado_y": "APROBADO" if np.max(np.abs(y_vector - np.mean(y_vector))) <= 0.02 else "RECHAZADO"
        }

# --- CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Calibración EPA Método 5", layout="wide")

st.title("Calibración de Consolas de Muestreo (EPA Método 5)")
st.write("Introduce los datos de calibración en la tabla para calcular $Y$ y $\Delta H_{@}$.")

# Panel lateral para la presión barométrica
st.sidebar.header("Condiciones Ambientales")
pb_input = st.sidebar.number_input("Presión barométrica absoluta, Pb (mm Hg)", value=760.0, step=0.1, format="%.2f")

# Datos por defecto para que la tabla no aparezca vacía al iniciar
datos_iniciales = {
    "Punto": [1, 2, 3, 4, 5],
    "Vw (Vol. Patrón)": [5.0, 5.0, 5.0, 5.0, 5.0],
    "Tw (Temp. Patrón K)": [293.15, 293.15, 293.15, 293.15, 293.15],
    "Vm (Vol. DGM)": [4.98, 4.99, 5.01, 4.97, 5.00],
    "Tm (Temp. DGM K)": [295.15, 295.15, 296.15, 296.15, 297.15],
    "dH (Presión Orificio mm H2O)": [12.7, 25.4, 38.1, 50.8, 63.5],
    "Theta (Tiempo min)": [10.0, 10.0, 10.0, 10.0, 10.0]
}
df_inicial = pd.DataFrame(datos_iniciales)

st.subheader("1. Entrada de datos del ensayo")
st.info("Podés hacer doble clic en cualquier celda para editar los valores directamente.")

# Tabla editable en Streamlit
df_editado = st.data_editor(df_inicial, num_rows="fixed", use_container_width=True, hide_index=True)

st.subheader("2. Procesamiento de resultados")
if st.button("Calcular Parámetros", type="primary"):
    # Convertir las columnas editadas de la tabla a vectores de NumPy
    vw = df_editado["Vw (Vol. Patrón)"].to_numpy()
    tw = df_editado["Tw (Temp. Patrón K)"].to_numpy()
    vm = df_editado["Vm (Vol. DGM)"].to_numpy()
    tm = df_editado["Tm (Temp. DGM K)"].to_numpy()
    dh = df_editado["dH (Presión Orificio mm H2O)"].to_numpy()
    theta = df_editado["Theta (Tiempo min)"].to_numpy()
    
    # Inicializar el motor matemático y calcular
    motor = Metodo5Calibracion(pb=pb_input)
    res = motor.calcular_parametros(vw, tw, vm, tm, dh, theta)
    
    # Mostrar el estado destacado (Aprobado / Rechazado)
    st.divider()
    if res["estado_y"] == "APROBADO":
        st.success(f"### ESTADO: {res['estado_y']} (Desviación dentro de los límites de tolerancia)")
    else:
        st.error(f"### ESTADO: {res['estado_y']} (Desviación excede el ±0.02 de tolerancia)")
        
    # Mostrar métricas resumidas
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Factor Y Promedio", value=f"{res['y_promedio']:.4f}")
    col2.metric(label="ΔH@ Promedio (mm H2O)", value=f"{res['dh_arroba_promedio']:.4f}")
    col3.metric(label="Incertidumbre Y (Disp.)", value=f"{res['incertidumbre_y']:.4f}")
    
    # Armar una tabla con los resultados individuales por punto
    df_resultados = pd.DataFrame({
        "Punto": df_editado["Punto"],
        "Y calculado": res["y_individuales"],
        "ΔH@ calculado": res["dh_arroba_individuales"]
    })
    
    st.subheader("Resultados desglosados por Punto")
    st.dataframe(df_resultados, use_container_width=True, hide_index=True)
