// ==========================================
// IMPORTACIÓN DE LIBRERÍAS
// ==========================================
#include <Wire.h>              // Librería estándar para comunicarse con dispositivos I2C (como el LCD)
#include <LiquidCrystal_I2C.h> // Librería para controlar pantallas LCD que tienen el módulo I2C soldado

// ==========================================
// CONFIGURACIÓN DE PINES (HARDWARE)
// ==========================================
// Definimos constantes para los pines donde conectamos los componentes.
// Usamos 'const int' para ahorrar memoria y evitar cambios accidentales.

// LEDs del semáforo de estado
const int PIN_LED_VERDE = 2;    // LED Verde conectado al pin digital 2
const int PIN_LED_AMARILLO = 3; // LED Amarillo conectado al pin digital 3
const int PIN_LED_ROJO = 4;     // LED Rojo conectado al pin digital 4

// Buzzer para las alarmas auditivas
const int PIN_BUZZER = 5;       // Buzzer (Pasivo o Activo) en el pin 5

// ==========================================
// CONFIGURACIÓN DEL OBJETO LCD
// ==========================================
// Creamos una instancia llamada 'lcd'.
// 0x27: Es la dirección hexadecimal estándar del chip I2C.
// 16: Indica que la pantalla tiene 16 columnas (caracteres por línea).
// 2: Indica que la pantalla tiene 2 filas.
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ==========================================
// VARIABLES GLOBALES (MEMORIA DEL SISTEMA)
// ==========================================
// Variable que guarda el estado actual del sistema.
// 'A' = Normal, 'B' = Cansancio, 'C' = Alerta, 'D' = Emergencia
char estado_actual = 'A';

// Variables para manejar el parpadeo de LEDs sin usar delay() (Multitasking)
unsigned long tiempo_anterior_led = 0; // Guarda la última vez (en milisegundos) que el LED cambió
bool estado_led = false;               // Guarda si el LED está encendido (true) o apagado (false) en ese instante

// ==========================================
// FUNCIÓN SETUP (SE EJECUTA UNA VEZ AL INICIO)
// ==========================================
void setup() {
  // Iniciamos la comunicación serial a 9600 baudios para hablar con Python.
  Serial.begin(9600);

  // Configuramos los pines de los LEDs y el Buzzer como SALIDAS de voltaje.
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Inicializamos la comunicación con la pantalla LCD
  lcd.init();
  lcd.backlight(); // Encendemos la luz de fondo de la pantalla

  // Secuencia de bienvenida (Intro)
  lcd.setCursor(0,0);       // Posicionamos el cursor: Columna 0, Fila 0
  lcd.print("SISTEMA");     // Escribimos texto
  lcd.setCursor(0,1);       // Bajamos a la Fila 1
  lcd.print("INICIANDO...");
  delay(2000);              // Esperamos 2 segundos para que el usuario lea
  lcd.clear();              // Limpiamos la pantalla

  // Establecemos el estado inicial visual (Verde y mensaje seguro)
  actualizarLCD('A');
}

// ==========================================
// FUNCIÓN LOOP (SE EJECUTA INFINITAMENTE)
// ==========================================
void loop() {
  
  // ----------------------------------------
  // 1. LEER COMUNICACIÓN DESDE PYTHON
  // ----------------------------------------
  // Serial.available() > 0 significa que han llegado datos por el cable USB.
  if (Serial.available() > 0) {
    char nuevo_estado = Serial.read(); // Leemos el carácter enviado ('A', 'B', 'C' o 'D')

    // Verificamos si el estado recibido es DIFERENTE al actual.
    // Esto es importante para no borrar y reescribir la LCD innecesariamente (evita parpadeo).
    if (nuevo_estado != estado_actual) {
      
      apagarTodo(); // Función auxiliar para apagar luces/sonidos viejos antes de cambiar
      
      estado_actual = nuevo_estado; // Actualizamos la variable de memoria
      
      actualizarLCD(estado_actual); // Cambiamos el texto en la pantalla
    }
  }

  // ----------------------------------------
  // 2. MÁQUINA DE ESTADOS (LÓGICA DE COMPORTAMIENTO)
  // ----------------------------------------
  // Obtenemos el tiempo actual en milisegundos desde que prendió el Arduino.
  unsigned long tiempo_actual = millis();

  // Switch-Case: Decide qué hacer según la letra en 'estado_actual'
  switch (estado_actual) {

    // CASO A: TODO NORMAL (VERDE)
    case 'A': 
      digitalWrite(PIN_LED_VERDE, HIGH); // Encender LED Verde fijo
      break; // Salir del switch

    // CASO B: CANSANCIO (AMARILLO PARPADEANDO)
    case 'B': 
      // Lógica de parpadeo sin delay (Non-blocking):
      // Si han pasado 500ms desde el último cambio...
      if (tiempo_actual - tiempo_anterior_led >= 500) { 
        tiempo_anterior_led = tiempo_actual; // Actualizamos la marca de tiempo
        
        estado_led = !estado_led; // Invertimos el estado (Si estaba ON pasa a OFF, y viceversa)
        digitalWrite(PIN_LED_AMARILLO, estado_led); // Aplicamos el estado al LED
        
        // Sincronizamos un pitido suave con el encendido del LED
        if (estado_led) {
            tone(PIN_BUZZER, 1000, 100); // Tono de 1000Hz por 100ms
        }
      }
      break;

    // CASO C: ALERTA CRÍTICA (ROJO RÁPIDO)
    case 'C': 
      // Similar al caso B, pero más rápido (cada 150ms)
      if (tiempo_actual - tiempo_anterior_led >= 150) { 
        tiempo_anterior_led = tiempo_actual;
        estado_led = !estado_led;
        digitalWrite(PIN_LED_ROJO, estado_led);
        
        // Pitido más agudo (2000Hz) para generar urgencia
        if (estado_led) {
            tone(PIN_BUZZER, 2000, 100); 
        }
      }
      break;

    // CASO D: EMERGENCIA TOTAL (ROJO FIJO + SIRENA)
    case 'D': 
      digitalWrite(PIN_LED_ROJO, HIGH); // LED Rojo siempre encendido (Pánico)

      // Efecto de Sirena de Policía:
      // Usamos matemáticas (módulo %) para alternar tonos cada 500ms
      if ((tiempo_actual / 500) % 2 == 0) {
         tone(PIN_BUZZER, 2500); // Tono muy agudo
      } else {
         tone(PIN_BUZZER, 1500); // Tono medio
      }
      break;
  }
}

// ==========================================
// FUNCIONES AUXILIARES (HERRAMIENTAS)
// ==========================================

// Función para reiniciar todos los pines a 0 (Apagado)
// Se llama cada vez que cambiamos de estado para limpiar residuos.
void apagarTodo() {
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
  noTone(PIN_BUZZER); // Detiene cualquier sonido activo
}

// Función para manejar qué texto se muestra en la pantalla
void actualizarLCD(char estado) {
  lcd.clear(); // Borra todo el texto anterior
  
  switch (estado) {
    case 'A': // Mensaje Normal
      lcd.setCursor(0, 0); lcd.print("ESTADO: SEGURO");
      lcd.setCursor(0, 1); lcd.print("MONITOREANDO...");
      break;

    case 'B': // Mensaje de Advertencia
      lcd.setCursor(0, 0); lcd.print("CANSANCIO");
      lcd.setCursor(0, 1); lcd.print("DETECTADO");
      break;

    case 'C': // Mensaje de Alerta
      lcd.setCursor(0, 0); lcd.print("!ALERTA!");
      lcd.setCursor(0, 1); lcd.print("NO RESPONDE");
      break;

    case 'D': // Mensaje de Emergencia
      lcd.setCursor(0, 0); lcd.print("EMERGENCIA");
      lcd.setCursor(0, 1); lcd.print("LLAMANDO 911...");
      break;
  }
}