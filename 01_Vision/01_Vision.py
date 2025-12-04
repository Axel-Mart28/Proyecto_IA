import cv2
import mediapipe as mp
import time
import math
import numpy as np
import serial 

# --- CONFIGURACIÓN DEL PUERTO SERIAL (ARDUINO) ---
try:
    print("Conectando a Arduino en COM8...")
    ser = serial.Serial('COM8', 9600, timeout=1) 
    time.sleep(2) 
    print("Conexión Exitosa.")
except:
    print("ADVERTENCIA: Arduino no conectado. Modo Simulación.")
    ser = None

# --- PARÁMETROS DE CALIBRACIÓN ---
UMBRAL_EAR = 0.21        
UMBRAL_RATIO_CABECEO = 0.3  
FACTOR_LINEA = 150.0 

# --- VARIABLES DE ESTADO ---
tiempo_inicio_anomalia = None
estado_actual = "NORMAL"

# Variables de Control de Flujo Serial
ultimo_byte_enviado = None 
contador_frames_envio = 0 # Para el "Heartbeat"

# Variables de Calibración
ratio_normal = 1.5 
calibrado = False

# --- INICIALIZACIÓN DE MEDIAPIPE ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Índices de los ojos
OJO_IZQUIERDO = [362, 385, 387, 263, 373, 380]
OJO_DERECHO = [33, 160, 158, 133, 153, 144]

def distancia_euclidiana(punto1, punto2):
    x1, y1 = punto1
    x2, y2 = punto2
    return math.hypot(x2 - x1, y2 - y1)

def calcular_ear(landmarks, indices, w, h):
    coords = []
    for i in indices:
        pt = landmarks[i]
        coords.append((int(pt.x * w), int(pt.y * h)))
    
    A = distancia_euclidiana(coords[1], coords[5])
    B = distancia_euclidiana(coords[2], coords[4])
    C = distancia_euclidiana(coords[0], coords[3])
    return (A + B) / (2.0 * C), coords

def calcular_ratio_cabeza(landmarks, w, h):
    y_gla = landmarks[168].y * h
    y_nariz = landmarks[1].y * h
    y_barbilla = landmarks[152].y * h
    
    dist_sup = y_nariz - y_gla
    dist_inf = y_barbilla - y_nariz
    
    if dist_inf < 0.1: dist_inf = 0.1
    ratio = dist_sup / dist_inf
    return ratio, (landmarks[1].x * w, y_nariz) 

# --- BUCLE PRINCIPAL ---
cap = cv2.VideoCapture(0)

print("INSTRUCCIONES: Presiona 'C' para calibrar mirando al frente.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = face_mesh.process(frame_rgb)
    h, w, _ = frame.shape
    
    # Panel superior
    cv2.rectangle(frame, (0,0), (w, 30), (50, 50, 50), -1)
    if calibrado:
        msg_cal = f"CALIBRADO (Ref: {ratio_normal:.2f})"
        col_cal = (0, 255, 0)
    else:
        msg_cal = "NO CALIBRADO (Presiona 'C')"
        col_cal = (0, 0, 255)
    
    cv2.putText(frame, msg_cal, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_cal, 1)

    byte_actual = None 

    if resultados.multi_face_landmarks:
        for face_landmarks in resultados.multi_face_landmarks:
            # 1. Ojos
            ear_izq, coords_izq = calcular_ear(face_landmarks.landmark, OJO_IZQUIERDO, w, h)
            ear_der, coords_der = calcular_ear(face_landmarks.landmark, OJO_DERECHO, w, h)
            ear_promedio = (ear_izq + ear_der) / 2.0
            
            for (cx, cy) in coords_izq + coords_der:
                cv2.circle(frame, (cx, cy), 1, (0, 255, 0), -1)

            # 2. Cabeza
            ratio_actual, nariz_coords = calcular_ratio_cabeza(face_landmarks.landmark, w, h)
            desviacion = ratio_actual - ratio_normal

            # Textos
            texto_ear = f"EAR: {ear_promedio:.2f}"
            texto_pitch = f"Ratio: {ratio_actual:.2f} (Desv: {desviacion:.2f})"
            
            color_ear = (0, 255, 0) if ear_promedio > UMBRAL_EAR else (0, 0, 255)
            color_pitch = (0, 255, 0) if desviacion < UMBRAL_RATIO_CABECEO else (0, 0, 255)

            cv2.putText(frame, texto_ear, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ear, 2)
            cv2.putText(frame, texto_pitch, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_pitch, 2)

            # 4. Lógica de Alertas
            condicion_ojos = ear_promedio < UMBRAL_EAR
            condicion_cabeza = desviacion > UMBRAL_RATIO_CABECEO

            if condicion_ojos or condicion_cabeza:
                if tiempo_inicio_anomalia is None:
                    tiempo_inicio_anomalia = time.time()
                tiempo_transcurrido = time.time() - tiempo_inicio_anomalia
                
                causa = "OJOS CERRADOS" if condicion_ojos else "CABEZA ABAJO"
                if condicion_ojos and condicion_cabeza: causa = "OJOS Y CABEZA"

                if tiempo_transcurrido >= 10:
                    estado_actual = "LLAMANDO 911"
                    byte_actual = b'D'
                elif tiempo_transcurrido >= 5:
                    estado_actual = "!ALERTA¡ SIN RESPUESTA"
                    byte_actual = b'C'
                elif tiempo_transcurrido >= 2:
                    estado_actual = "CANSANCIO"
                    byte_actual = b'B'
                else:
                    estado_actual = f"DETECTANDO: {causa}"
                    byte_actual = b'A'

                cv2.putText(frame, f"Tiempo: {tiempo_transcurrido:.1f}s", (30, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(frame, estado_actual, (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                tiempo_inicio_anomalia = None
                estado_actual = "CONDUCTOR SEGURO"
                byte_actual = b'A'
                
                cv2.putText(frame, estado_actual, (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 5. Visualización Cabeceo
            p1 = (int(nariz_coords[0]), int(nariz_coords[1]))
            longitud_visual = int(desviacion * FACTOR_LINEA)
            if longitud_visual < 10: longitud_visual = 10 
            p2 = (int(nariz_coords[0]), int(nariz_coords[1] + longitud_visual))
            col_linea = (255, 0, 0) if not condicion_cabeza else (0, 0, 255)
            cv2.arrowedLine(frame, p1, p2, col_linea, 3)

    # --- LÓGICA DE ENVÍO ROBUSTA (HEARTBEAT) ---
    if ser and byte_actual is not None:
        contador_frames_envio += 1
        
        # Enviamos si:
        # 1. El estado CAMBIÓ (Prioridad inmediata)
        # 2. O pasaron 30 frames (~1 segundo) para recordar el estado (Heartbeat)
        if byte_actual != ultimo_byte_enviado or contador_frames_envio >= 30:
            ser.write(byte_actual)
            ultimo_byte_enviado = byte_actual
            contador_frames_envio = 0 # Reiniciar contador
            # print(f"Enviado: {byte_actual}")

    cv2.imshow('Sistema Final', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c') or key == ord('C'):
        if 'ratio_actual' in locals():
            ratio_normal = ratio_actual
            calibrado = True
            print(f"Calibrado! Ratio Normal: {ratio_normal:.2f}")

cap.release()
cv2.destroyAllWindows()