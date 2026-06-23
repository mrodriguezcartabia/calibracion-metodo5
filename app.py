import numpy as np

class Metodo5Calibracion:
    """
    Motor termodinámico estricto para calibración de consolas de muestreo (EPA Método 5).
    Resuelve el factor de calibración del medidor (Y) y el orificio (Delta H@).
    """
    # Constantes termodinámicas estándar (EPA)
    T_STD = 293.15  # K (68 °F)
    P_STD = 760.0   # mm Hg (29.92 in Hg)
    K1 = 0.0319     # Constante para cálculo de dH@ (unidades mixtas imperiales/métricas según norma)

    def __init__(self, pb: float):
        """
        pb: Presión barométrica absoluta (mm Hg). Se asume constante durante el ensayo.
        """
        self.pb = pb

    def calcular_parametros(self,
                            vw: np.ndarray, tw: np.ndarray,
                            vm: np.ndarray, tm: np.ndarray,
                            dh: np.ndarray, theta: np.ndarray) -> dict:
        """
        Cálculo vectorizado de Y y Delta H@.
        Garantizar que todos los vectores de entrada tengan dimensión [N],
        donde N es el número de puntos de calibración (ej. N=5).
       
        vw: Volumen del medidor de referencia (Wet Test Meter)
        tw: Temperatura absoluta del medidor de referencia (K)
        vm: Volumen del medidor de gas seco (Dry Gas Meter)
        tm: Temperatura absoluta del DGM (K)
        dh: Caída de presión en la placa orificio (mm H2O)
        theta: Tiempo de ensayo por corrida (min)
        """
       
        # 1. Presión absoluta en el DGM (pm)
        # 13.6 es la gravedad específica del mercurio respecto al agua
        pm = self.pb + (dh / 13.6)

        # 2. Factor de Calibración del Medidor (Y)
        # Ecuación fundamental de gases ideales comparando patrón vs instrumento
        y_vector = (vw * self.pb * tm) / (vm * pm * tw)

        # 3. Delta H@ (Orifice pressure drop for 0.75 cfm at standard conditions)
        # Requiere extremo rigor en las unidades.
        dh_arroba_vector = (self.K1 * dh * tm * (theta ** 2)) / (self.pb * (y_vector ** 2) * (vm ** 2))

        # 4. Propagación de incertidumbre estándar (ejemplo sobre Y)
        # Derivadas parciales dY/dVw, dY/dTm, etc., asumiendo errores instrumentales máximos EPA.
        # sigma_vw = 0.01 * vw, sigma_tw = 2.0 (K), etc.
        # Aquí se implementaría la sumatoria de varianzas.
        incertidumbre_y = np.std(y_vector, ddof=1) # Simplificación temporal: dispersión de la muestra

        # Control dimensional para la salida: aseguramos la estructura tabular de los resultados.
        # Evitamos discordancias dimensionando explícitamente los arrays antes de empaquetar.
        resultados = np.column_stack((y_vector, dh_arroba_vector))

        return {
            "y_individuales": y_vector.tolist(),
            "y_promedio": float(np.mean(y_vector)),
            "dh_arroba_individuales": dh_arroba_vector.tolist(),
            "dh_arroba_promedio": float(np.mean(dh_arroba_vector)),
            "incertidumbre_y": float(incertidumbre_y),
            "estado_y": "APROBADO" if np.max(np.abs(y_vector - np.mean(y_vector))) <= 0.02 else "RECHAZADO"
        }
