bool completed_handshake;
uint8_t sequence_counter;


struct DataPacket {
  uint8_t beetle_id; 
  uint8_t packet_id;
  uint8_t sequence_id;
  uint16_t payload_1;
  uint16_t payload_2;
  uint16_t payload_3;
  uint16_t payload_4;
  uint16_t payload_5;
  uint16_t payload_6;
  uint16_t buffer_1;
  uint16_t buffer_2;
  uint8_t buffer_3;
};

void send_packet(
  uint8_t beetle_id,
  uint8_t packet_id,
  uint8_t sequence_id,
  uint16_t payload_1,
  uint16_t payload_2,
  uint16_t payload_3,
  uint16_t payload_4,
  uint16_t payload_5,
  uint16_t payload_6) {
  DataPacket packet;
  packet.beetle_id = (uint8_t)beetle_id;
  packet.packet_id = (uint8_t)packet_id;
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
  packet.sequence_id = (uint8_t)sequence_id;
  packet.payload_1 = (uint16_t)payload_1;
  packet.payload_2 = (uint16_t)payload_2;
  packet.payload_3 = (uint16_t)payload_3;
  packet.payload_4 = (uint16_t)payload_4;
  packet.payload_5 = (uint16_t)payload_5;
  packet.payload_6 = (uint16_t)payload_6;
  packet.buffer_1 = (uint16_t)0;
  packet.buffer_2 = (uint16_t)0;
  packet.buffer_3 = (uint8_t)0;

  
  Serial.write((uint8_t *)&packet, sizeof(packet));
}


void setup() {
  Serial.begin(115200); 
  // B4 52 A9 09 B6 D2
  completed_handshake = false;
  sequence_counter = 0;
  pinMode(13, OUTPUT);
}



void loop() {
  if(Serial.available()){
    if(sequence_counter == 49) {
      sequence_counter = 50;
    }
    // UNO receives data in ASCII 
    // e.g. "A" has value 65
    // Serial.read clears the buffer
    switch(Serial.read()) {
      case 65: 
        // start handshake
        send_packet(1,2,0,0,0,0,0,0,0);
        break;
      case 66:
        // complete handshake
        completed_handshake = true;
        digitalWrite(13, HIGH);
        break;
      case 67:
      case 68:
        int count = 0;
        for(count = 0; count < 50; count++){
          send_packet(1,5,count,4,5,6,7,8,9); 
        }
        break;
      default:
        break;
    }
 }
}
