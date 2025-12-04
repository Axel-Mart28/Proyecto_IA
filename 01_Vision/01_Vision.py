
# IMPORTACIÓN DE LIBRERÍAS
# ==========================================
import cv2                  # OpenCV: Para capturar video y dibujar en la imagen
import mediapipe as mp      # MediaPipe: La IA de Google que detecta la malla facial
import time                 # Time: Para medir los segundos que duras con los ojos cerrados
import math                 # Math: Para operaciones matemáticas (hipotenusa, distancias)
import numpy as np          # NumPy: Para manejo eficiente de arrays numéricos
import serial               # PySerial: Para comunicarnos con el Arduino por USB

# ==========================================
# 1. CONFIGURACIÓN DE COMUNICACIÓN SERIAL
# ==========================================
# Usamos un bloque try-except para que el programa no falle si el Arduino no está conectado.
try:
    print("Conectando a Arduino en COM8...")
    # Intenta abrir el puerto COM8 a 9600 baudios (velocidad estándar)
    # timeout=1 significa que si no responde en 1 seg, deja de esperar.
    ser = serial.Serial('COM8', 9600, timeout=1) 
    time.sleep(2) # Esperamos 2 segundos obligatorios para que el Arduino se reinicie al conectar
    print("Conexión Exitosa.")
except:
    # Si falla (cable desconectado o puerto incorrecto), entra aquí.
    print("ADVERTENCIA: Arduino no conectado. Modo Simulación.")
    ser = None # Definimos ser como None para que el resto del código sepa que no hay Arduino

# ==========================================
# 2. PARÁMETROS DE CALIBRACIÓN (UMBRALES)
# ==========================================
UMBRAL_EAR = 0.21            # Si el EAR (apertura de ojo) baja de 0.21, se considera CERRADO.
UMBRAL_RATIO_CABECEO = 0.3   # Si la relación geométrica de la cara cambia más de 0.3, es CABECEO.
FACTOR_LINEA = 150.0         # Multiplicador visual para que la línea azul de la nariz se vea larga.

# ==========================================
# 3. VARIABLES DE ESTADO Y CONTROL
# ==========================================
tiempo_inicio_anomalia = None  # Guarda la hora exacta (timestamp) cuando empieza a dormirse
estado_actual = "NORMAL"       # Texto para mostrar en pantalla

# Variables para el "Heartbeat" (Latido) del Serial
# Esto evita saturar al Arduino enviando datos innecesarios.
ultimo_byte_enviado = None     
contador_frames_envio = 0      

# Variables de Calibración
ratio_normal = 1.5   # Valor base de tu cara mirando al frente (se ajusta con 'C')
calibrado = False    # Bandera para saber si ya presionaste 'C'

# ==========================================
# 4. INICIALIZACIÓN DE LA IA (MEDIAPIPE)
# ==========================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,                # Solo detectamos 1 cara (el conductor)
    refine_landmarks=True,          # Activa puntos extra en ojos e iris para mayor precisión
    min_detection_confidence=0.5,   # Confianza mínima para detectar cara
    min_tracking_confidence=0.5     # Confianza mínima para seguir la cara
)

# Índices numéricos de los puntos de la malla facial que corresponden a los ojos
OJO_IZQUIERDO = [362, 385, 387, 263, 373, 380]
OJO_DERECHO = [33, 160, 158, 133, 153, 144]

# ==========================================
# 5. FUNCIONES MATEMÁTICAS
# ==========================================

# Función auxiliar para calcular la distancia en línea recta entre dos puntos (x,y)
def distancia_euclidiana(punto1, punto2):
    x1, y1 = punto1
    x2, y2 = punto2
    return math.hypot(x2 - x1, y2 - y1)

# Función principal para detectar OJOS CERRADOS
# EAR = Eye Aspect Ratio (Relación de Aspecto del Ojo)
def calcular_ear(landmarks, indices, w, h):
    coords = []
    # Convertimos las coordenadas normalizadas (0.0 a 1.0) a pixeles reales (ej. 1920x1080)
    for i in indices:
        pt = landmarks[i]
        coords.append((int(pt.x * w), int(pt.y * h)))
    
    # Calculamos las distancias verticales (párpado arriba a párpado abajo)
    A = distancia_euclidiana(coords[1], coords[5])
    B = distancia_euclidiana(coords[2], coords[4])
    # Calculamos la distancia horizontal (comisura a comisura)
    C = distancia_euclidiana(coords[0], coords[3])
    
    # Fórmula del EAR: Promedio de verticales dividido por la horizontal
    return (A + B) / (2.0 * C), coords

# Función geométrica para detectar CABEZA AGACHADA
# Usa la proporción entre la frente, la nariz y la barbilla.
def calcular_ratio_cabeza(landmarks, w, h):
    # Obtenemos alturas Y de puntos clave
    y_gla = landmarks[168].y * h    # Entrecejo
    y_nariz = landmarks[1].y * h    # Punta nariz
    y_barbilla = landmarks[152].y * h # Barbilla
    
    # Distancia Superior (Frente a Nariz) -> Esta casi no cambia al agachar
    dist_sup = y_nariz - y_gla
    
    # Distancia Inferior (Nariz a Barbilla) -> Esta se hace PEQUEÑA visualmente al agachar la cabeza
    dist_inf = y_barbilla - y_nariz
    
    # Evitamos división por cero por seguridad
    if dist_inf < 0.1: dist_inf = 0.1
    
    # Calculamos ratio. Si agachas la cabeza, dist_inf baja, por lo tanto el RATIO SUBE.
    ratio = dist_sup / dist_inf
    return ratio, (landmarks[1].x * w, y_nariz) 

# ==========================================
# 6. BUCLE PRINCIPAL DEL PROGRAMA
# ==========================================
cap = cv2.VideoCapture(0) # Abrir cámara web (ID 0)

print("INSTRUCCIONES: Presiona 'C' para calibrar mirando al frente.")

while cap.isOpened():
    # 1. Leer imagen de la cámara
    ret, frame = cap.read()
    if not ret: break # Si no hay imagen, salir

    # 2. Procesar imagen con MediaPipe
    # MediaPipe necesita color RGB, OpenCV usa BGR. Convertimos.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = face_mesh.process(frame_rgb)
    h, w, _ = frame.shape # Obtener tamaño de la ventana
    
    # 3. Dibujar Interfaz (Panel superior gris)
    cv2.rectangle(frame, (0,0), (w, 30), (50, 50, 50), -1)
    
    # Mostrar estado de calibración
    if calibrado:
        msg_cal = f"CALIBRADO (Ref: {ratio_normal:.2f})"
        col_cal = (0, 255, 0) # Verde
    else:
        msg_cal = "NO CALIBRADO (Presiona 'C')"
        col_cal = (0, 0, 255) # Rojo
    
    cv2.putText(frame, msg_cal, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_cal, 1)

    byte_actual = None # Variable para guardar qué letra enviaremos al Arduino en este ciclo

    # Si MediaPipe detectó una cara...
    if resultados.multi_face_landmarks:
        for face_landmarks in resultados.multi_face_landmarks:
            
            # --- ANÁLISIS DE OJOS ---
            ear_izq, coords_izq = calcular_ear(face_landmarks.landmark, OJO_IZQUIERDO, w, h)
            ear_der, coords_der = calcular_ear(face_landmarks.landmark, OJO_DERECHO, w, h)
            # Promediamos ambos ojos para ser más robustos
            ear_promedio = (ear_izq + ear_der) / 2.0
            
            # Dibujar puntitos verdes en los ojos
            for (cx, cy) in coords_izq + coords_der:
                cv2.circle(frame, (cx, cy), 1, (0, 255, 0), -1)

            # --- ANÁLISIS DE CABEZA ---
            ratio_actual, nariz_coords = calcular_ratio_cabeza(face_landmarks.landmark, w, h)
            # Calculamos cuánto te has movido respecto a tu posición "Cero" (Calibrada)
            desviacion = ratio_actual - ratio_normal

            # --- MOSTRAR DATOS EN PANTALLA ---
            texto_ear = f"EAR: {ear_promedio:.2f}"
            texto_pitch = f"Ratio: {ratio_actual:.2f} (Desv: {desviacion:.2f})"
            
            # Definir colores de texto (Verde si OK, Rojo si Mal)
            color_ear = (0, 255, 0) if ear_promedio > UMBRAL_EAR else (0, 0, 255)
            color_pitch = (0, 255, 0) if desviacion < UMBRAL_RATIO_CABECEO else (0, 0, 255)

            cv2.putText(frame, texto_ear, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ear, 2)
            cv2.putText(frame, texto_pitch, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_pitch, 2)

            # --- LÓGICA DE DETECCIÓN DE SUEÑO ---
            # ¿Están los ojos cerrados?
            condicion_ojos = ear_promedio < UMBRAL_EAR
            # ¿Está la cabeza agachada más de lo permitido?
            condicion_cabeza = desviacion > UMBRAL_RATIO_CABECEO

            # Si CUALQUIERA de las dos condiciones es cierta...
            if condicion_ojos or condicion_cabeza:
                # Si acabamos de detectar el sueño, guardamos la hora actual
                if tiempo_inicio_anomalia is None:
                    tiempo_inicio_anomalia = time.time()
                
                # Calculamos cuánto tiempo ha pasado desde que empezaste a dormirte
                tiempo_transcurrido = time.time() - tiempo_inicio_anomalia
                
                # Determinamos la causa para mostrar en pantalla
                causa = "OJOS CERRADOS" if condicion_ojos else "CABEZA ABAJO"
                if condicion_ojos and condicion_cabeza: causa = "OJOS Y CABEZA"

                # --- MÁQUINA DE ESTADOS POR TIEMPO ---
                if tiempo_transcurrido >= 10:
                    estado_actual = "LLAMANDO 911"
                    byte_actual = b'D' # Enviar 'D' al Arduino
                elif tiempo_transcurrido >= 5:
                    estado_actual = "!ALERTA! SIN RESPUESTA"
                    byte_actual = b'C' # Enviar 'C' al Arduino
                elif tiempo_transcurrido >= 2:
                    estado_actual = "CANSANCIO"
                    byte_actual = b'B' # Enviar 'B' al Arduino
                else:
                    estado_actual = f"DETECTANDO: {causa}"
                    byte_actual = b'A' # Aun es seguro, mantenemos 'A'

                # Mostrar tiempo y estado en pantalla
                cv2.putText(frame, f"Tiempo: {tiempo_transcurrido:.1f}s", (30, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(frame, estado_actual, (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                # Si todo está bien, reseteamos el temporizador
                tiempo_inicio_anomalia = None
                estado_actual = "CONDUCTOR SEGURO"
                byte_actual = b'A' # Enviar 'A' (Verde)
                
                cv2.putText(frame, estado_actual, (30, 160), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # --- DIBUJAR LÍNEA DE LA NARIZ (VISUALIZACIÓN) ---
            p1 = (int(nariz_coords[0]), int(nariz_coords[1]))
            # La línea crece según qué tan agachada esté la cabeza (desviación)
            longitud_visual = int(desviacion * FACTOR_LINEA)
            if longitud_visual < 10: longitud_visual = 10 
            p2 = (int(nariz_coords[0]), int(nariz_coords[1] + longitud_visual))
            
            # Color de la línea cambia a rojo si detecta cabeceo
            col_linea = (255, 0, 0) if not condicion_cabeza else (0, 0, 255)
            cv2.arrowedLine(frame, p1, p2, col_linea, 3)

    # --- COMUNICACIÓN SERIAL ROBUSTA (HEARTBEAT) ---
    # Solo enviamos datos si tenemos conexión y hay un dato válido
    if ser and byte_actual is not None:
        contador_frames_envio += 1
        
        # ENVIAMOS SI:
        # 1. El estado CAMBIÓ (byte_actual es diferente al último enviado) -> Prioridad Alta
        # 2. O pasaron 30 frames (~1 segundo) -> Heartbeat para recordar al Arduino que estamos vivos
        if byte_actual != ultimo_byte_enviado or contador_frames_envio >= 30:
            ser.write(byte_actual)
            ultimo_byte_enviado = byte_actual
            contador_frames_envio = 0 # Reiniciar contador
            # print(f"Enviado: {byte_actual}")

    # Mostrar ventana final
    cv2.imshow('Sistema Final', frame)
    
    # --- CONTROL DE TECLADO ---
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): # Salir con Q
        break
    elif key == ord('c') or key == ord('C'): # Calibrar con C
        if 'ratio_actual' in locals():
            ratio_normal = ratio_actual # Guardar posición actual como referencia
            calibrado = True
            print(f"Calibrado! Ratio Normal: {ratio_normal:.2f}")

# Liberar cámara y cerrar ventanas al terminar
cap.release()
cv2.destroyAllWindows()