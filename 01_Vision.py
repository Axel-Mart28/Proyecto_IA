import cv2
import mediapipe as mp
import time
import math
import numpy as np
import serial 

# --- CONFIGURACIÓN DEL PUERTO SERIAL (ARDUINO) ---
try:
    # AQUI ESTÁ EL CAMBIO: Puerto COM8
    print("Intentando conectar con Arduino en COM8...")
    ser = serial.Serial('COM8', 9600, timeout=1) 
    time.sleep(2) # Esperamos 2 segundos a que el Arduino se reinicie
    print("¡Conexión Exitosa!")
except:
    print("ERROR: No se pudo conectar al Arduino en COM8. Verifica conexión.")
    ser = None

# --- PARÁMETROS DE CALIBRACIÓN ---
UMBRAL_EAR = 0.21        
UMBRAL_PITCH_ABAJO = 12  
FACTOR_LINEA = 3.0       # Multiplicador visual

# --- VARIABLES DE ESTADO ---
tiempo_inicio_anomalia = None
estado_actual = "NORMAL"

# Variables de Calibración (Offset)
offset_pitch = 0
offset_yaw = 0
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

def obtener_angulo_cabeza(landmarks, w, h):
    face_3d = np.array([
        (0.0, 0.0, 0.0),             # Nariz
        (0.0, -330.0, -65.0),        # Barbilla
        (-225.0, 170.0, -135.0),     # Ojo Izquierdo
        (225.0, 170.0, -135.0),      # Ojo Derecho
        (-150.0, -150.0, -125.0),    # Boca Izquierda
        (150.0, -150.0, -125.0)      # Boca Derecha
    ], dtype=np.float64)

    face_2d = []
    for idx in [1, 152, 263, 33, 291, 61]:
        lm = landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        face_2d.append([x, y])
    
    face_2d = np.array(face_2d, dtype=np.float64)

    focal_length = 1 * w
    cam_matrix = np.array([ [focal_length, 0, w / 2], [0, focal_length, h / 2], [0, 0, 1] ])
    dist_matrix = np.zeros((4, 1), dtype=np.float64)

    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
    rmat, jac = cv2.Rodrigues(rot_vec)
    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

    x = float(angles[0]) * 360 
    y = float(angles[1]) * 360
    
    if x < -180: x += 360
    elif x > 180: x -= 360
    
    return x, y 

# --- BUCLE PRINCIPAL ---
cap = cv2.VideoCapture(0)

print("INSTRUCCIONES: Presiona 'C' para calibrar tu posición neutral.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = face_mesh.process(frame_rgb)
    h, w, _ = frame.shape
    
    # Panel de info superior
    cv2.rectangle(frame, (0,0), (w, 30), (50, 50, 50), -1)
    if calibrado:
        msg_cal = "SISTEMA CALIBRADO"
        col_cal = (0, 255, 0)
    else:
        msg_cal = "NO CALIBRADO (Presiona 'C' mirando al frente)"
        col_cal = (0, 0, 255)
    
    cv2.putText(frame, msg_cal, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_cal, 1)

    if resultados.multi_face_landmarks:
        for face_landmarks in resultados.multi_face_landmarks:
            # 1. EAR y Puntos
            ear_izq, coords_izq = calcular_ear(face_landmarks.landmark, OJO_IZQUIERDO, w, h)
            ear_der, coords_der = calcular_ear(face_landmarks.landmark, OJO_DERECHO, w, h)
            ear_promedio = (ear_izq + ear_der) / 2.0
            
            for (cx, cy) in coords_izq + coords_der:
                cv2.circle(frame, (cx, cy), 1, (0, 255, 0), -1)

            # 2. Cabeza RAW (Crudo)
            raw_pitch, raw_yaw = obtener_angulo_cabeza(face_landmarks.landmark, w, h)

            # 3. Aplicar Calibración (Resta el offset)
            pitch = raw_pitch - offset_pitch
            yaw = raw_yaw - offset_yaw

            # Textos
            texto_ear = f"EAR: {ear_promedio:.2f}"
            texto_pitch = f"Cabeza: {pitch:.1f}"
            
            color_ear = (0, 255, 0) if ear_promedio > UMBRAL_EAR else (0, 0, 255)
            color_pitch = (0, 255, 0) if pitch < UMBRAL_PITCH_ABAJO else (0, 0, 255)

            cv2.putText(frame, texto_ear, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ear, 2)
            cv2.putText(frame, texto_pitch, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_pitch, 2)

            # 4. Lógica de Alertas
            condicion_ojos = ear_promedio < UMBRAL_EAR
            condicion_cabeza = pitch > UMBRAL_PITCH_ABAJO 

            if condicion_ojos or condicion_cabeza:
                if tiempo_inicio_anomalia is None:
                    tiempo_inicio_anomalia = time.time()
                tiempo_transcurrido = time.time() - tiempo_inicio_anomalia
                
                causa = "OJOS CERRADOS" if condicion_ojos else "CABEZA ABAJO"
                if condicion_ojos and condicion_cabeza: causa = "DORMIDO TOTAL"

                if tiempo_transcurrido >= 10:
                    estado_actual = "LLAMANDO 911"
                    if ser: ser.write(b'D')
                elif tiempo_transcurrido >= 5:
                    estado_actual = "ALERTA CRITICA"
                    if ser: ser.write(b'C')
                elif tiempo_transcurrido >= 2:
                    estado_actual = "CANSANCIO"
                    if ser: ser.write(b'B')
                else:
                    estado_actual = f"DETECTANDO: {causa}"
                    if ser: ser.write(b'A')

                cv2.putText(frame, f"Tiempo: {tiempo_transcurrido:.1f}s", (30, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(frame, estado_actual, (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                tiempo_inicio_anomalia = None
                if ser: ser.write(b'A')
                cv2.putText(frame, "CONDUCTOR SEGURO", (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 5. Visualización Nariz (Usamos los ángulos calibrados 'yaw' y 'pitch')
            nose_2d = (int(face_landmarks.landmark[1].x * w), int(face_landmarks.landmark[1].y * h))
            p1 = (int(nose_2d[0]), int(nose_2d[1]))
            # Multiplicamos por FACTOR_LINEA para que se note más
            p2 = (int(nose_2d[0] + yaw * FACTOR_LINEA), int(nose_2d[1] + pitch * FACTOR_LINEA))
            cv2.arrowedLine(frame, p1, p2, (255, 0, 0), 3)

    cv2.imshow('Sistema VW Final', frame)
    
    # --- CONTROL DE TECLAS ---
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c') or key == ord('C'):
        # GUARDAR LA POSICIÓN ACTUAL COMO CERO
        if 'raw_pitch' in locals():
            offset_pitch = raw_pitch
            offset_yaw = raw_yaw
            calibrado = True
            print(f"Calibrado! Nuevo Cero -> Pitch: {offset_pitch:.2f}, Yaw: {offset_yaw:.2f}")

cap.release()
cv2.destroyAllWindows()