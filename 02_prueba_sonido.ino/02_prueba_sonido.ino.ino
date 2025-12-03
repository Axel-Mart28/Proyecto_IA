const int pinBuzzer = 9;

void setup(){
  pinMode(pinBuzzer, HIGH);
  delay(1000);

  digitalWrite(pinBuzzer, LOW);
  delay(3000);
}
