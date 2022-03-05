from logging.handlers import BaseRotatingHandler
from signal import signal
from bluepy import btle
import signal
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
- C: ACK (for receiving data)
"""

mac_address_1 = "80:30:DC:D9:1F:A9"
service = "0000dfb0-0000-1000-8000-00805f9b34fb"
beetle_characteristic = "0000dfb1-0000-1000-8000-00805f9b34fb"
buffer = []


class Beetle_Delegate(btle.DefaultDelegate):
    def init(self):
        btle.DefaultDelegate.init(self)

    def handleNotification(self, cHandle, data):
        # print("recieved, ", data)
        decoded_data = data.decode()
        """
        Expects packets of the len 9
        i.e. 
        id|id|p_1a|p_1b|p_2a|p_2b|p
        """
        print(len(data))
        print("received, ", data)
        print(" ", decoded_data)
        buffer.append(data)




class Beetle_Connection:
    def init(self, address):
        self.address = address
        self._periph = None
        self._periph_delegate = None

    
    def make_connection(self):
        # establishes a connection to the specified beetle
        self._periph = btle.Peripheral(self.address)
        print(self._periph.getState())
        print("connected!")
        self._periph_delegate = Beetle_Delegate()
        self._periph.setDelegate(self._periph_delegate)

        # svc = self._periph.getServiceByUUID("dfb0")
        # ch = svc.getCharacteristics("dfb1")[0]
        # # return ch
    
    
    def reconnect(self):
        try:
            print("reconnecting")
            self.make_connection()
        except Exception as e: 
            print("did not reconnect, error: ", e)
            return

    
    def disconnect(self):
        # disconnects the beetle
        self._periph.disconnect()
        print("disconnected!")

    
    def write(self, val):
        for characteristic in self._periph.getCharacteristics():
            if characteristic.uuid == beetle_characteristic:
                print("sending 'A' packet to %s" % (self._periph.addr))
                characteristic.write(bytes(val, "UTF-8"), withResponse=False)

    
    def do_handshake(self):
        self.write("A")
        self._periph.waitForNotifications(2.0)
        if buffer[0] == b'\x01\x02\x00\x00\x00\x00\x00\x00\x00':
            buffer.clear()
            print(buffer)
            self.write("B")
        print("handshake completed!")


    def main_routine(self):
        self._periph = None
        while self._periph is None:
            try:
                self.make_connection()
                self.do_handshake()
            except Exception as e:
                print("error, ", e)
                time.sleep(2.0)


        while True:
            try:
                for i in range(100):
                    if self._periph.waitForNotifications(0.01):
                        continue
                    print("waiting...")
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
    

    

if __name__ == "__main__":
    beetle_1 = Beetle_Connection(mac_address_1)
    beetle_1.main_routine()
    print(buffer)


    # To check if bluetooth is working
    # test = btle.Peripheral(mac_address_1)
    # print("connected")
    # test.disconnect()
    # print("disconnected")