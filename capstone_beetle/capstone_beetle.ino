bool completed_handshake;

void setup() {
  Serial.begin(115200); 
  // B4 52 A9 09 B6 D2
  completed_handshake = false;
  pinMode(13, OUTPUT);
}

struct DataPacket {
  uint8_t beetle_id;
  uint8_t packet_id;
  int payload_1;
  int payload_2;
  int payload_3;
  uint8_t crc;
};

void send_packet(
  uint8_t beetle_id,
  uint8_t packet_id,
  int payload_1,
  int payload_2,
  int payload_3,
  uint8_t crc) {
  // Dummy data
  DataPacket packet;
  packet.beetle_id = beetle_id;
  packet.packet_id = packet_id;
  /*
   * packet id and their purposes
   * 1: SYN
   * 2: SYN-ACK
   * 3: ACK
   * 4: NAK
   * 5: accelerometer data
   * 6: ir sensor data
   * 7: laser tag gun data
   * 8: reload
   * 8: START
   * 10: FIN
   */
  packet.payload_1 = payload_1;
  packet.payload_2 = payload_2;
  packet.payload_3 = payload_3;
  packet.crc = crc;

  Serial.write((uint8_t *)&packet, sizeof(packet));
}


void loop() {
  if(Serial.available()){
    // UNO receives data in ASCII 
    // e.g. "A" has value 65
    // Serial.read clears the buffer
    switch(Serial.read()) {
      case 65: 
        // start handshake
        send_packet(1,2,0,0,0,0);
      case 66:
        // complete handshake
        completed_handshake = true;
        digitalWrite(13, HIGH);
      default:
        break;
    }
 }
}
