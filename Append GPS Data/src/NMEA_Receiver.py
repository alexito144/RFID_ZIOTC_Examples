import threading
import socket
import traceback

class NMEA_Receiver:
    _instance = None
    _latitude = 0.0
    _longitude = 0.0
    _speed = 0.0
    _course = 0.0
    _valid = False
    _quit = False
    _udp_port = 9000

    def __new__(self,logger,port):
        if self._instance is None:
            self._udp_port = port
            self._logger = logger
            self._instance = super(NMEA_Receiver,self).__new__(self)
            self._thread = threading.Thread(target=self._instance._ReceiverThread)
            self._thread.start()
        return self._instance

    def close(self):
        self._quit = True
        self._thread.join()       

    def getValidFix(self):
        return self._valid

    def getLatitude(self):
        return self._latitude
    
    def getLongitude(self):
        return self._longitude
    
    def getSpeed(self):
        return self._speed

    def getCourse(self):
        return self._course

# ************************************************************************
# Process GPRMC Messages (  Recommended Minimum Specific GNSS Data )
# ************************************************************************
    def _ProcessRMC(self,nema):
        fields = nema.split(",")
        self._valid = True if fields[2] == "A" else False
        self._latitude = self._CalcLatLongToDecimal(fields[3],fields[4])
        self._longitude = self._CalcLatLongToDecimal(fields[5],fields[6])
        self._speed = float(fields[7])
        self._course = float(fields[8])

# ************************************************************************
# Convert Lat/Long to Decimal Degrees
# ************************************************************************
    def _CalcLatLongToDecimal(self,degrees,orientation):
        DD = int(float(degrees) / 100)
        SS = float(degrees) - DD * 100
        R = (DD * 100000) + ((SS/60) * 100000)
        M = 1
        if orientation == "S" or orientation == "W":
            M =-1
        return int(R * M)/100000

# ************************************************************************
# Background thread to receive NMEA data and decode it.
# ************************************************************************
    def _ReceiverThread(self):
        self._logger.debug("Starting NMEA Receive Thread")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0",self._udp_port))
        sock.settimeout(5.0)

        # Processing loop
        while not self._quit:
            try:
                data, addr = sock.recvfrom(1024)
                msgs = data.decode('utf-8').split("\n")
                for msg in msgs:
                    if msg.startswith("$GPRMC"):
                        self._ProcessRMC(msg.strip())

            except Exception as err:
                tb_lines = [line.rstrip('\n') for line in traceback.format_exception(err.__class__, err, err.__traceback__)]
                self._logger.err(f"Got Exception : {tb_lines}")
                self._valid = False

        sock.close()
        self._logger.debug("Stopped NMEA Receive Thread")

