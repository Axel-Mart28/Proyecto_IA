import cv2
import mediapipe as mp
import time
import math

# --- CONFIGURACIÓN ---
# Umbral: Si el EAR es menor a esto, el ojo se considera cerrado.
# (Calibra este valor: 0.20 a 0.25 suele funcionar bien)
UMBRAL_EAR = 0.22 

# Variables de estado
tiempo_inicio_cierre = None
estado_actual = "NORMAL"

# --- INICIALIZACIÓN DE MEDIAPIPE ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True, # Importante para tener puntos precisos del iris/ojo
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Índices de los puntos de los ojos en la malla de MediaPipe
# (Estos son puntos específicos del contorno del ojo)
OJO_IZQUIERDO = [362, 385, 387, 263, 373, 380]
OJO_DERECHO = [33, 160, 158, 133, 153, 144]

# --- FUNCIONES MATEMÁTICAS ---
def distancia_euclidiana(punto1, punto2):
    x1, y1 = punto1
    x2, y2 = punto2
    return math.hypot(x2 - x1, y2 - y1)

def calcular_ear(landmarks, indices, w, h):
    # Obtener coordenadas (x, y) de los 6 puntos del ojo
    coords = []
    for i in indices:
        pt = landmarks[i]
        coords.append((int(pt.x * w), int(pt.y * h)))

    # Calcular las distancias verticales (p2-p6 y p3-p5)
    A = distancia_euclidiana(coords[1], coords[5])
    B = distancia_euclidiana(coords[2], coords[4])

    # Calcular la distancia horizontal (p1-p4)
    C = distancia_euclidiana(coords[0], coords[3])

    # Fórmula del EAR (Eye Aspect Ratio)
    ear = (A + B) / (2.0 * C)
    return ear, coords

# --- BUCLE PRINCIPAL ---
cap = cv2.VideoCapture(0) # 0 suele ser la webcam por defecto

print("Iniciando sistema... Presiona 'q' para salir.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # MediaPipe requiere imagen en RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = face_mesh.process(frame_rgb)
    
    # Obtener dimensiones para dibujar
    h, w, _ = frame.shape

    if resultados.multi_face_landmarks:
        for face_landmarks in resultados.multi_face_landmarks:
            # Calcular EAR para ambos ojos
            ear_izq, coords_izq = calcular_ear(face_landmarks.landmark, OJO_IZQUIERDO, w, h)
            ear_der, coords_der = calcular_ear(face_landmarks.landmark, OJO_DERECHO, w, h)

            # Promedio de ambos ojos (para mayor robustez)
            ear_promedio = (ear_izq + ear_der) / 2.0

            # --- DIBUJAR EN PANTALLA ---
            # Dibujamos el contorno de los ojos para ver qué detecta
            for (x, y) in coords_izq + coords_der:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # Mostrar valor EAR en pantalla (útil para calibrar)
            cv2.putText(frame, f"EAR: {ear_promedio:.2f}", (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # --- LÓGICA DE DETECCIÓN DE SUEÑO ---
            if ear_promedio < UMBRAL_EAR:
                # Ojos cerrados
                if tiempo_inicio_cierre is None:
                    tiempo_inicio_cierre = time.time()
                
                tiempo_transcurrido = time.time() - tiempo_inicio_cierre
                
                # Clasificar según el tiempo (Lógica que pediste)
                if tiempo_transcurrido >= 10:
                    estado_actual = "LLAMANDO 911"
                    color_alerta = (0, 0, 255) # Rojo intenso
                    # TODO: Enviar 'D' al Arduino
                elif tiempo_transcurrido >= 5:
                    estado_actual = "ALERTA (5s)"
                    color_alerta = (0, 165, 255) # Naranja
                    # TODO: Enviar 'C' al Arduino
                elif tiempo_transcurrido >= 2:
                    estado_actual = "CANSANCIO (2s)"
                    color_alerta = (0, 255, 255) # Amarillo
                    # TODO: Enviar 'B' al Arduino
                else:
                    estado_actual = "PARPADEO / CERRANDO"
                    color_alerta = (200, 200, 200)

                # Mostrar tiempo y estado en pantalla
                cv2.putText(frame, f"Tiempo: {tiempo_transcurrido:.1f}s", (30, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2)
                cv2.putText(frame, estado_actual, (30, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color_alerta, 3)

            else:
                # Ojos abiertos
                tiempo_inicio_cierre = None
                estado_actual = "OK - Ojos Abiertos"
                # TODO: Enviar 'A' al Arduino
                
                cv2.putText(frame, "ESTADO: OK", (30, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('Detector de Sueno - Vision Artificial', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()