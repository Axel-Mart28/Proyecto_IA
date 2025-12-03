#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

// INTENTO 1: Dirección 0x27 (La más común)
LiquidCrystal_I2C lcd(0x27, 16, 2);  

// Si NO funciona, comenta la linea de arriba y descomenta esta:
// LiquidCrystal_I2C lcd(0x3F, 16, 2); 

void setup() {
  // Inicializar el LCD
  lcd.init();
  
  // Encender la luz de fondo (IMPORTANTE)
  lcd.backlight();
  
  // Escribir mensaje
  lcd.setCursor(0,0); // Columna 0, Fila 0
  lcd.print("TEST PANTALLA");
  
  lcd.setCursor(0,1); // Columna 0, Fila 1
  lcd.print("FUNCIONA OK!");
}

void loop() {
  // Hacemos parpadear el texto para confirmar que no se congeló
  lcd.noBacklight();
  delay(500);
  lcd.backlight();
  delay(500);
}