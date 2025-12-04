<div align="center">
<h1>🚗 Sistema de Detección Del Sueño</h1>
<p>

<i>Inspirado en el sistema <a href="https://www.youtube.com/shorts/G59pxnDXlto">"Emergency Assist" de Volkswagen</a></i>
</p>




<hr>

📖 Descripción del Proyecto

Este proyecto es un prototipo funcional de un sistema de detección del sueño para autos. Combina visión artificial con un sistema embebido (ARDUINO UNO) de seguridad para prevenir accidentes automovilísticos causados por fatiga o distracción.

El sistema monitorea constantemente el rostro del conductor. Si detecta anomalías (ojos cerrados o cabeceo), inicia un protocolo de seguridad escalonado que va desde una advertencia visual hasta una intervención de emergencia simulada.

Características Técnicas:

Visión Artificial (Python):

Detección de Ojos: Algoritmo EAR (Eye Aspect Ratio) para identificar fatiga visual.

Detección de Cabeza: Algoritmo de Geometría Facial (Ratio Frente/Barbilla) para detectar microsueños (cabeceo) sin descalibrarse.

Calibración Dinámica: Sistema de "Calibración" con tecla C para adaptarse a cualquier conductor y posición de asiento.

Heartbeat Serial: Comunicación robusta con Arduino para evitar desincronización.

Sistema Embebido (Arduino):

Interfaz Humano-Máquina: Pantalla LCD I2C para mensajes de estado.

Feedback Multisensorial: Semáforo LED y Buzzer con frecuencias variables.


Diagrama de Conexiones (Hardware)

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
<td>📺 LCD I2C</td>
<td>A4 (SDA), A5 (SCL)</td>
<td>VCC a 5V, GND a GND</td>
</tr>
</table>
</div>

Lógica de Estados (Alertas)

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

Nota de Seguridad: Si el sistema entra en éste estado, se hace una simulación de un llamado de emergencia a las autoridades.

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