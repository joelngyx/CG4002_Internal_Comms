from ctypes import sizeof
from distutils import errors
from logging.handlers import BaseRotatingHandler
from signal import signal
from bluepy import btle
import threading
import time

"""
MAKE SURE THAT BLUETOOTH DRIVER IS CONNECTED
(File->Removable Devices->Bluetooth Driver)

To start/stop bluetooth:
- sudo systemctl start/stop bluetooth

To check status
- systemctl status bluetooth
 
bluetoothctl for various bluetooth functions
- power on
- agent on
- scan on/off
- connect/disconnect MAC ADDRESS

packet ids
- A: SYN (handshake)
- B: ACK (handshake)
- C: REQ (request for data)
- D: ACK (acknowledge data)
"""

mac_address_1 = "80:30:DC:D9:1F:A9"
mac_address_2 = "30:E2:83:AE:68:71"
service = "0000dfb0-0000-1000-8000-00805f9b34fb"
beetle_characteristic = "0000dfb1-0000-1000-8000-00805f9b34fb"
all_beetles_connected = 0
num_of_beetles = 2

# this global variable (list of lists) stores incoming data
# 1 list for each beetle
buffer = [[],[]]


def add_two_binaries(val1, val2):
    """
    
    """
    temp_binary = 0b0000_0000_0000_0000
    temp_binary = temp_binary|val1
    temp_binary = temp_binary << 8
    temp_binary = temp_binary | val2
    return temp_binary



class Packet:
    def __init__(
        self, 
        beetle_id, 
        packet_id,
        payload_1,
        payload_2,
        payload_3,
        payload_4,
        payload_5,
        payload_6):
        self.beetle_id = beetle_id,
        self.packet_id = packet_id,
        self.payload_1 = payload_1
        self.payload_2 = payload_2
        self.payload_3 = payload_3 
        self.payload_4 = payload_4
        self.payload_5 = payload_5
        self.payload_6 = payload_6 



class Beetle_Delegate(btle.DefaultDelegate):
    """
    Enables the script to receive Bluetooth messages asynchronously,
    processes incoming data
    """
    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)
        self.beetle_id = params


    def handleNotification(self, cHandle, data):
        print(self.beetle_id, " received, ", data)

        # each packet comes in the format
        # [beetle_id][packet_id][sequence_id] //0,1,2
        # [payload_1][payload_2][payload_3] //3,4,5,6,7,8
        # [payload_4][payload_5][payload_6] //9,10,11,12,13,14
        # remaining bytes are buffers

        # Arrange packets
        temp_packet = Packet(
            data[0],
            data[1],
            add_two_binaries(data[3], data[4]),
            add_two_binaries(data[5], data[6]),
            add_two_binaries(data[7], data[8]),
            add_two_binaries(data[9], data[10]),
            add_two_binaries(data[11], data[12]),
            add_two_binaries(data[13], data[14])
        )   

        buffer[self.beetle_id].append(temp_packet)
        # print(buffer[self.beetle_id][0].beetle_id)
        # print(buffer[self.beetle_id][0].packet_id)
        # print(buffer[self.beetle_id][0].payload_1)
        # print(buffer[self.beetle_id][0].payload_2)
        # print(buffer[self.beetle_id][0].payload_3)
        # print(buffer[self.beetle_id][0].payload_4)
        # print(buffer[self.beetle_id][0].payload_5)
        # print(buffer[self.beetle_id][0].payload_6)



class Beetle_Connection:
    def __init__(self, address, beetle_id):
        self.address = address
        self.beetle_id = beetle_id
        self._periph = None
        self._periph_delegate = None

    
    def make_connection(self):
        """
        Establishes a connection to the specified beetle
        (id as provided by the instance of Beetle_Connection)
        """
        self._periph = btle.Peripheral(self.address)
        print(self._periph.getState())
        print("connected!")
        self._periph_delegate = Beetle_Delegate(self.beetle_id)
        self._periph.setDelegate(self._periph_delegate)

    
    def reconnect(self):
        """
        Upon abrupt disconnection, the script will attempt to 
        reconnect to the Beetle
        """
        try:
            print("reconnecting")
            self.make_connection()
        except Exception as e: 
            print("did not reconnect, error: ", e)
            return

    
    def disconnect(self):
        """
        Disconnects the beetle
        """
        self._periph.disconnect()
        print("disconnected!")

    
    def write(self, val):
        """
        Writes the provided value val to the Beetle
            - encoded by UTF-8
            - the value will be received as its ASCII value
            - e.g. A is 65
        """
        for characteristic in self._periph.getCharacteristics():
            if characteristic.uuid == beetle_characteristic:
                print("sending", val, "packet to ", self._periph.addr)
                characteristic.write(bytes(val, "UTF-8"), withResponse=False)

    
    def do_handshake(self):
        """
        Conducts a 3-way handshake, i.e.
            - Laptop -SYN-> Beetle
            - Beetle -SY-ACK-> Laptop
            - Laptop -ACK-> Laptop
        Uses the values in buffer as a flag
        Adds 1 to the global variable all_beetles_connected
        """
        self.write("A")
        self._periph.waitForNotifications(2.0)
        try:
            if buffer[self.beetle_id][0].packet_id == (2,):
                print(buffer)
                self.write("B")
                print("handshake completed!") 

                global all_beetles_connected
                all_beetles_connected = all_beetles_connected + 1
            else: 
                print("handshake incomplete!")
                # Connection may have been established, but the received
                # SYN=ACK packet might have not been accepted
                try:
                    self._periph.disconnect()
                except Exception as e: 
                    print(e)
            
                self._periph = None
        except Exception as e:
            print("handshake error", e)

        
        buffer[self.beetle_id].clear()

    
    def stop_and_wait(self):
        """
        This function conducts a stop-and-wait protocol
            - uses the buffer list to check if packets received are in
              order
            - self._periph.waitForNotifications enables the
              asynchronous reception of packets
            - when a packet is received, Beetle_Delegate's method(s)
              are called. 
              > if the packet is received successfully, the packet is
                written onto the buffer list. The script acknowledges 
                the received packet by sending a "D" packet to the 
                Beetle
              > if the packet is not received successfully, the packet
                is not written onto the buffer list. The script will then
                request for the packet to be re-sent
        """
        packet_count = 0
        try:
            for i in range(160):
                # Tests Stop-n-Wait, for approx. 1 second
                print("iteration, ", i)
                if self._periph.waitForNotifications(0.001):
                    if buffer[self.beetle_id][packet_count] is None:
                        print("no input")
                        self.write("C")
                    else:
                        self.write("D")
                        packet_count += 1
                        print("packet count, ", packet_count)
                        print(buffer)
                        print("success!")
                    # self.write("C")
                    continue
            print("packets received = ", packet_count)
            print(buffer)
            self.disconnect()
            return
        except KeyboardInterrupt:
            try:
                self.disconnect()
            except:
                print("end of run")
                return
        except btle.BTLEException as e:
            print("error, ", e)
            self._periph = None
            while self._periph is None:
                self.reconnect()
        except Exception as f:
            if(self._periph is not None):
                self.disconnect()
            print("error, ", f)
            self._periph = None
            while self._periph is None:
                self.reconnect()


    def sliding_window(self):
        """
        This function conducts a sliding window protocol
            - upon sending a "C" packet, the Beetle will send over 50 
              packets at once
            - (TO BE IMPLEMENTED) if there are any issues with the packets
              e.g. lost packets, an "E" packet will be sent, followed by
              a packet containing the problematic packet's sequence number
              [However, a consideration: is the overhead and resulting 
              decrease in throughput worth it?]
            - achieves a rate of around 25 Hz; this value could be less
              if 
                a. Beetles are further away from the laptop
                b. 3 Beetles are connected at once, 
                c. Beetles take time to pick up data from the hardware 
                   sensors
        """
        try:
            for i in range(120):
                # print("iteration, ", i)
                if self._periph.waitForNotifications(0.01):
                    continue
        except KeyboardInterrupt:
            try:
                self.disconnect()
            except:
                print("end of run")
                return
        except btle.BTLEException as e:
            print("error, ", e)
            self._periph = None
            while self._periph is None:
                self.reconnect()
        except Exception as f:
            if(self._periph is not None):
                self.disconnect()
            print("error, ", f)
            self._periph = None
            while self._periph is None:
                self.reconnect()

        print(len(buffer[self.beetle_id]))
        print(buffer)

    
    def main_routine(self):
        while self._periph is None:
            try:
                self.make_connection()
                self.do_handshake()
            except Exception as e:
                print("error, ", e)
                time.sleep(2.0)

        while all_beetles_connected != num_of_beetles:
            pass

        # To kick off the sending of data
        self.write("C")

        # Tests packets received in a second
        start = time.time()
        self.sliding_window()
        end = time.time()
        print("time elapsed in seconds", (end - start))

        self.disconnect()

        # while True:
        #     self.sliding_window()
        #     if no errors
        #         self.write("C")

    

if __name__ == "__main__":
    beetle_1 = Beetle_Connection(mac_address_1, 0)
    thread_1 = threading.Thread(target=beetle_1.main_routine, args=())
    beetle_2 = Beetle_Connection(mac_address_2, 1)
    thread_2 = threading.Thread(target=beetle_2.main_routine, args=())
    
    thread_1.start()
    thread_2.start()
