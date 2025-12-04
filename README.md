<div align="center">
<h1>🚗 Sistema de Asistencia al Conductor (DMS)</h1>
<p>
<strong>Detección de Somnolencia y Distracción en Tiempo Real</strong>




<i>Inspirado en el sistema "Emergency Assist" de Volkswagen</i>
</p>

<!-- BADGES / ESCUDOS -->

<!-- Estos son los escudos de colores que se ven profesionales -->

<img src="https://www.google.com/search?q=https://img.shields.io/badge/Python-3.11-3776AB%3Fstyle%3Dfor-the-badge%26logo%3Dpython%26logoColor%3Dwhite" alt="Python" />
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Arduino-UNO-00979D%3Fstyle%3Dfor-the-badge%26logo%3Darduino%26logoColor%3Dwhite" alt="Arduino" />
<img src="https://www.google.com/search?q=https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8%3Fstyle%3Dfor-the-badge%26logo%3Dopencv%26logoColor%3Dwhite" alt="OpenCV" />
<img src="https://www.google.com/search?q=https://img.shields.io/badge/MediaPipe-Face_Mesh-00E5FF%3Fstyle%3Dfor-the-badge" alt="MediaPipe" />
</div>

<hr>

📖 Descripción del Proyecto

Este proyecto es un prototipo funcional de un Driver Monitoring System (DMS). Combina visión artificial avanzada con un sistema embebido de seguridad para prevenir accidentes automovilísticos causados por fatiga o distracción.

El sistema monitorea constantemente el rostro del conductor. Si detecta anomalías (ojos cerrados o cabeceo), inicia un protocolo de seguridad escalonado que va desde una advertencia visual hasta una intervención de emergencia simulada con bloqueo del sistema.

⚙️ Características Técnicas

👁️ Visión Artificial (Python)

Detección de Ojos: Algoritmo EAR (Eye Aspect Ratio) para identificar fatiga visual.

Detección de Cabeza: Algoritmo de Geometría Facial (Ratio Frente/Barbilla) para detectar microsueños (cabeceo) sin descalibrarse.

Calibración Dinámica: Sistema de "Tarado" con tecla C para adaptarse a cualquier conductor y posición de asiento.

Heartbeat Serial: Comunicación robusta con Arduino para evitar desincronización.

🤖 Sistema Embebido (Arduino)

Interfaz Humano-Máquina: Pantalla LCD I2C para mensajes de estado.

Feedback Multisensorial: Semáforo LED y Buzzer con frecuencias variables.

Protocolo de Seguridad: Máquina de estados con bloqueo. Si el conductor ignora las alertas o acumula fatiga 3 veces, el sistema se bloquea hasta recibir confirmación física (Botón).

🔌 Diagrama de Conexiones (Hardware)

<div align="center">
<table>
<tr>
<th>Componente</th>
<th>Pin Arduino</th>
<th>Nota</th>
</tr>
<tr>
<td>🟢 LED Verde</td>
<td>Pin 2</td>
<td>Estado Seguro</td>
</tr>
<tr>
<td>🟡 LED Amarillo</td>
<td>Pin 3</td>
<td>Precaución / Cansancio</td>
</tr>
<tr>
<td>🔴 LED Rojo</td>
<td>Pin 4</td>
<td>Alerta / Emergencia</td>
</tr>
<tr>
<td>🔊 Buzzer</td>
<td>Pin 5</td>
<td>Pasivo (Tonos)</td>
</tr>
<tr>
<td>🔘 Push Button</td>
<td>Pin 6</td>
<td>Para desbloqueo (GND + Pin 6)</td>
</tr>
<tr>
<td>📺 LCD I2C</td>
<td>A4 (SDA), A5 (SCL)</td>
<td>VCC a 5V, GND a GND</td>
</tr>
</table>
</div>

🚦 Lógica de Estados (Alertas)

El sistema evalúa el tiempo de distracción y reacciona progresivamente:

Nivel

Tiempo

Estímulo

Acción Requerida

1

2 seg

🟡 Parpadeo Lento + Bip Suave

Abrir ojos / Levantar cabeza

2

5 seg

🔴 Parpadeo Rápido + Bip Agudo

Abrir ojos inmediatamente

3

10 seg

🚨 EMERGENCIA: Sirena Policial + Rojo Fijo

BLOQUEO DEL SISTEMA

Nota de Seguridad: Si el sistema entra en Emergencia o detecta Cansancio 3 veces consecutivas, se bloqueará. El conductor deberá presionar el Botón Físico para confirmar que está consciente y reiniciar el sistema.

🚀 Instalación y Uso

1. Requisitos de Software

pip install opencv-python mediapipe numpy pyserial


2. Cargar Firmware

Abrir firmware_arduino.ino en Arduino IDE.

Instalar librería LiquidCrystal I2C.

Subir a la placa Arduino UNO.

3. Ejecutar

python Detector_Cabeza_Reparado.py


4. Instrucciones de Operación

Siéntese frente a la cámara en posición de manejo.

Presione la tecla 'C' para calibrar su posición neutral.

El sistema iniciará el monitoreo.

En caso de bloqueo, presione el botón físico en el circuito.

Para salir, presione 'Q'.

<div align="center">
<p>Desarrollado para la materia de <strong>Inteligencia Artificial</strong></p>
<p>CETI - Ingeniería en Mecatrónica</p>
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Hecho_con-❤️-red" alt="Love" />
</div>