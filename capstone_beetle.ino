void setup() {
  Serial.begin(115200); 
  // B4 52 A9 09 B6 D2
}

void loop() {
  if(Serial.available()){
    Serial.print("Connected! Buffer contains:");
    Serial.print(Serial.read());
    Serial.print("\n");
//    Serial.flush();
    Serial.print("Buffer contains:");
    Serial.print(Serial.read());
//    Serial.write("1");
//    Serial.print(String(Serial.read()));
  }
}
