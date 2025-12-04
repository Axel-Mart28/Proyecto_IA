#include <Wire.h>

#include <LiquidCrystal_I2C.h>



// --- CONFIGURACIÓN DE PINES ---

// Asegúrate de conectar los LEDs con resistencias de 220 o 330 ohms

const int PIN_LED_VERDE = 2;

const int PIN_LED_AMARILLO = 3;

const int PIN_LED_ROJO = 4;

const int PIN_BUZZER = 5; // Buzzer activo o pasivo



// --- CONFIGURACIÓN DEL LCD ---

// Dirección I2C: Usualmente es 0x27 o 0x3F.

LiquidCrystal_I2C lcd(0x27, 16, 2);



// Variables para control de tiempo (sin delay)

char estado_actual = 'A';

unsigned long tiempo_anterior_led = 0;

bool estado_led = false;



void setup() {

  Serial.begin(9600); // Velocidad debe coincidir con Python

 

  pinMode(PIN_LED_VERDE, OUTPUT);

  pinMode(PIN_LED_AMARILLO, OUTPUT);

  pinMode(PIN_LED_ROJO, OUTPUT);

  pinMode(PIN_BUZZER, OUTPUT);



  // Iniciar LCD

  lcd.init();

  lcd.backlight();

 

  // Test de inicio

  lcd.setCursor(0,0);

  lcd.print("SISTEMA");

  lcd.setCursor(0,1);

  lcd.print("INICIANDO...");

  delay(2000);

  lcd.clear();

  actualizarLCD('A'); // Estado inicial

}



void loop() {

  // 1. LEER COMANDO DESDE PYTHON

  if (Serial.available() > 0) {

    char nuevo_estado = Serial.read();

   

    // Solo actuamos si el estado cambia (para no parpadear el LCD)

    if (nuevo_estado != estado_actual) {

      // Apagar todo antes de cambiar de estado

      apagarTodo();

      estado_actual = nuevo_estado;

      actualizarLCD(estado_actual);

    }

  }



  // 2. MÁQUINA DE ESTADOS (COMPORTAMIENTO)

  unsigned long tiempo_actual = millis();



  switch (estado_actual) {

    case 'A': // NORMAL

      digitalWrite(PIN_LED_VERDE, HIGH);

      break;



    case 'B': // CANSANCIO (Parpadeo Lento Amarillo)

      if (tiempo_actual - tiempo_anterior_led >= 500) { // Cada 500ms

        tiempo_anterior_led = tiempo_actual;

        estado_led = !estado_led;

        digitalWrite(PIN_LED_AMARILLO, estado_led);

       

        // Pitido suave sincronizado

        if (estado_led) tone(PIN_BUZZER, 1000, 100);

      }

      break;



    case 'C': // ALERTA CRÍTICA (Parpadeo Rápido Rojo)

      if (tiempo_actual - tiempo_anterior_led >= 150) { // Cada 150ms

        tiempo_anterior_led = tiempo_actual;

        estado_led = !estado_led;

        digitalWrite(PIN_LED_ROJO, estado_led);

       

        // Pitido agudo

        if (estado_led) tone(PIN_BUZZER, 2000, 100);

      }

      break;



    case 'D': // EMERGENCIA 911 (Rojo Fijo + Sirena)

      digitalWrite(PIN_LED_ROJO, HIGH);

      // Efecto sirena simple

      if ((tiempo_actual / 500) % 2 == 0) {

         tone(PIN_BUZZER, 2500);

      } else {

         tone(PIN_BUZZER, 1500);

      }

      break;

  }

}



void apagarTodo() {

  digitalWrite(PIN_LED_VERDE, LOW);

  digitalWrite(PIN_LED_AMARILLO, LOW);

  digitalWrite(PIN_LED_ROJO, LOW);

  noTone(PIN_BUZZER);

}



void actualizarLCD(char estado) {

  lcd.clear();

  switch (estado) {

    case 'A':

      lcd.setCursor(0, 0); lcd.print("ESTADO: SEGURO");

      lcd.setCursor(0, 1); lcd.print("MONITOREANDO...");

      break;

    case 'B':

      lcd.setCursor(0, 0); lcd.print("CANSANCIO");

      lcd.setCursor(0, 1); lcd.print("DETECTADO");

      break;

    case 'C':

      lcd.setCursor(0, 0); lcd.print("!ALERTA!");

      lcd.setCursor(0, 1); lcd.print("NO RESPONDE");

      break;

    case 'D':

      lcd.setCursor(0, 0); lcd.print("EMERGENCIA");

      lcd.setCursor(0, 1); lcd.print("LLAMANDO 911...");

      break;

  }

}