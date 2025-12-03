#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>

// --- PINES DE SALIDA ---
const int PIN_LED_VERDE = 2;
const int PIN_LED_AMARILLO = 3;
const int PIN_LED_ROJO = 4;
const int PIN_BUZZER = 5;

// --- CONFIGURACIÓN TECLADO 4x4 ---
const byte FILAS = 4; 
const byte COLUMNAS = 4; 
char teclas[FILAS][COLUMNAS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
// Pines del teclado (Ajusta si los conectaste diferente)
byte pinesFilas[FILAS] = {6, 7, 8, 9}; 
byte pinesColumnas[COLUMNAS] = {10, 11, 12, 13}; 

Keypad teclado = Keypad(makeKeymap(teclas), pinesFilas, pinesColumnas, FILAS, COLUMNAS);
LiquidCrystal_I2C lcd(0x27, 16, 2); 

// --- ESTADOS DEL SISTEMA ---
enum Estado {
  NORMAL,             // 'A' - Luz Verde
  CANSANCIO,          // 'B' - Amarillo parpadeando + Bip suave
  ALERTA,             // 'C' - Rojo rápido + Bip agudo
  EMERGENCIA,         // 'D' - Rojo fijo + Sirena
  PREGUNTA_SEGURIDAD, // Menú "¿Está bien?"
  BLOQUEO_FATIGA,     // Menú "3 veces cansado"
  LLAMADA_911         // Estado irreversible
};

Estado estado_actual = NORMAL;
char input_python = 'A'; // Último dato recibido de la cámara

// --- VARIABLES DE LÓGICA ---
int contador_fatiga = 0;
bool flag_cansancio_contado = false; // Para contar solo 1 vez por evento de fatiga

// Variables para efectos sin delay()
unsigned long tiempo_anterior_efecto = 0;
bool estado_led_blink = false;

void setup() {
  Serial.begin(9600);
  
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  lcd.init();
  lcd.backlight();
  
  // Intro rápida
  lcd.setCursor(0,0); lcd.print("SISTEMA ACTIVO");
  lcd.setCursor(0,1); lcd.print("TECLADO OK");
  delay(1500);
  cambiarEstado(NORMAL);
}

void loop() {
  // 1. LEER TECLADO
  char tecla = teclado.getKey();
  
  // 2. LEER PYTHON (Solo si no estamos en estados críticos que requieren atención manual)
  if (Serial.available() > 0) {
    char lectura = Serial.read();
    
    // Si estamos en un menú de pregunta, solo hacemos caso a alertas graves ('C' o 'D')
    // para no ignorar si el usuario se duerme mientras lee la pantalla.
    if (estado_actual == PREGUNTA_SEGURIDAD || estado_actual == BLOQUEO_FATIGA) {
       if (lectura == 'C' || lectura == 'D') input_python = lectura;
    } 
    // Si ya estamos llamando al 911, ignoramos a Python (es irreversible)
    else if (estado_actual != LLAMADA_911) {
       input_python = lectura;
    }
  }

  // 3. MÁQUINA DE ESTADOS (COMPORTAMIENTO)
  unsigned long tiempo_actual = millis();

  switch (estado_actual) {
    
    // --- CASO A: TODO BIEN ---
    case NORMAL:
      digitalWrite(PIN_LED_VERDE, HIGH);
      
      flag_cansancio_contado = false; // Reset para poder volver a contar fatiga después

      // Transiciones automáticas por cámara
      if (input_python == 'B') cambiarEstado(CANSANCIO);
      if (input_python == 'C') cambiarEstado(ALERTA);
      if (input_python == 'D') cambiarEstado(EMERGENCIA);
      break;

    // --- CASO B: CANSANCIO (Amarillo + Bip Lento) ---
    case CANSANCIO:
      // EFECTO VISUAL/AUDITIVO (Cada 500ms)
      if (tiempo_actual - tiempo_anterior_efecto >= 500) {
        tiempo_anterior_efecto = tiempo_actual;
        estado_led_blink = !estado_led_blink;
        digitalWrite(PIN_LED_AMARILLO, estado_led_blink);
        
        // Pitido suave (1000Hz) solo cuando el LED enciende
        if (estado_led_blink) tone(PIN_BUZZER, 1000, 100); 
      }

      // LÓGICA DE CONTEO (REGLA DE 3 VECES)
      if (!flag_cansancio_contado) {
        contador_fatiga++;
        flag_cansancio_contado = true;
        // Mostrar contador discreto en la esquina
        lcd.setCursor(15, 0); lcd.print(contador_fatiga);
      }

      // TRANSICIONES
      if (contador_fatiga >= 3) {
        cambiarEstado(BLOQUEO_FATIGA); // ¡Bloqueo!
      } else if (input_python == 'A') {
        cambiarEstado(NORMAL);
      } else if (input_python == 'C') {
        cambiarEstado(ALERTA);
      }
      break;

    // --- CASO C: ALERTA (Rojo + Bip Rápido) ---
    case ALERTA:
      // EFECTO VISUAL/AUDITIVO (Cada 150ms)
      if (tiempo_actual - tiempo_anterior_efecto >= 150) {
        tiempo_anterior_efecto = tiempo_actual;
        estado_led_blink = !estado_led_blink;
        digitalWrite(PIN_LED_ROJO, estado_led_blink);
        
        // Pitido agudo (2000Hz)
        if (estado_led_blink) tone(PIN_BUZZER, 2000, 100);
      }

      // TRANSICIONES
      // Si abre los ojos ('A'), NO volvemos a Normal. Preguntamos estado.
      if (input_python == 'A') cambiarEstado(PREGUNTA_SEGURIDAD);
      if (input_python == 'D') cambiarEstado(EMERGENCIA);
      break;

    // --- CASO D: EMERGENCIA (Sirena) ---
    case EMERGENCIA:
      digitalWrite(PIN_LED_ROJO, HIGH);
      // EFECTO SIRENA (Cambia tono cada 500ms)
      if ((tiempo_actual / 500) % 2 == 0) {
         tone(PIN_BUZZER, 2500);
      } else {
         tone(PIN_BUZZER, 1500);
      }
      
      // Si se despierta, preguntamos.
      if (input_python == 'A') cambiarEstado(PREGUNTA_SEGURIDAD);
      break;

    // --- INTERACCIÓN 1: PREGUNTA SEGURIDAD ---
    case PREGUNTA_SEGURIDAD:
      digitalWrite(PIN_LED_ROJO, HIGH); // Rojo fijo (Alerta de espera)
      noTone(PIN_BUZZER); // Silencio para leer

      if (tecla == 'A') {
        contador_fatiga = 0; // Reiniciar cuenta si dice que está bien
        cambiarEstado(NORMAL);
      } 
      else if (tecla == '0') {
        cambiarEstado(LLAMADA_911);
      }
      
      // Si se vuelve a dormir esperando respuesta, volvemos a alarmar
      if (input_python == 'C' || input_python == 'D') cambiarEstado(ALERTA);
      break;

    // --- INTERACCIÓN 2: BLOQUEO POR 3 FATIGAS ---
    case BLOQUEO_FATIGA:
      // Parpadeo lento de ROJO y AMARILLO alternados para indicar bloqueo
      if (tiempo_actual - tiempo_anterior_efecto >= 500) {
         tiempo_anterior_efecto = tiempo_actual;
         estado_led_blink = !estado_led_blink;
         digitalWrite(PIN_LED_AMARILLO, estado_led_blink);
         digitalWrite(PIN_LED_ROJO, !estado_led_blink);
      }
      noTone(PIN_BUZZER); // Silencio para leer
      
      if (tecla == 'A') {
         contador_fatiga = 0;
         cambiarEstado(NORMAL);
      }
      else if (tecla == '0') {
         cambiarEstado(LLAMADA_911);
      }
      break;

    // --- ESTADO FINAL: 911 ---
    case LLAMADA_911:
      digitalWrite(PIN_LED_ROJO, HIGH);
      // SIRENA DE POLICÍA PERPETUA
      if ((tiempo_actual / 300) % 2 == 0) tone(PIN_BUZZER, 3000);
      else tone(PIN_BUZZER, 2000);
      
      // Aquí no hay salida (Loop infinito hasta reiniciar Arduino)
      break;
  }
}

// --- FUNCIÓN PARA CAMBIAR ESTADOS Y ACTUALIZAR LCD ---
void cambiarEstado(Estado nuevo) {
  estado_actual = nuevo;
  
  // Apagar todo al cambiar para limpiar residuos de parpadeos
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
  noTone(PIN_BUZZER);

  lcd.clear();
  
  switch (nuevo) {
    case NORMAL:
      lcd.setCursor(0, 0); lcd.print("SISTEMA OK");
      lcd.setCursor(0, 1); lcd.print("Manejando...");
      break;
    case CANSANCIO:
      lcd.setCursor(0, 0); lcd.print("! CANSANCIO !");
      lcd.setCursor(0, 1); lcd.print("ALERTA NIVEL 1");
      break;
    case ALERTA:
      lcd.setCursor(0, 0); lcd.print("!!! ALERTA !!!");
      lcd.setCursor(0, 1); lcd.print("DESPIERTA YA");
      break;
    case EMERGENCIA:
      lcd.setCursor(0, 0); lcd.print("EMERGENCIA");
      lcd.setCursor(0, 1); lcd.print("DETECTADA");
      break;
    case PREGUNTA_SEGURIDAD:
      lcd.setCursor(0, 0); lcd.print("ESTA BIEN? A:Si");
      lcd.setCursor(0, 1); lcd.print("ASISTENCIA? 0:No");
      break;
    case BLOQUEO_FATIGA:
      lcd.setCursor(0, 0); lcd.print("FATIGA CRITICA");
      lcd.setCursor(0, 1); lcd.print("CONTINUAR? A/0");
      break;
    case LLAMADA_911:
      lcd.setCursor(0, 0); lcd.print("LLAMANDO 911...");
      lcd.setCursor(0, 1); lcd.print("AYUDA EN CAMINO");
      break;
  }
}