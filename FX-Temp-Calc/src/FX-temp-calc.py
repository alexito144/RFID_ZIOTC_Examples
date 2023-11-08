import ziotc
import json
import os
import traceback
from Logger import Logger
from RestAPI import RestAPI


# Global Variables
DEBUG_SERVER = "192.168.13.140"
DEBUG_PORT = 40514
LOG_ONLY_TO_CONSOLE = False
REST_API_RETRY_COUNT = 3

## Constants 
A = 0.3378
B = -133

# ************************************************************************
# Passthrough callback
# ************************************************************************
def passthru_callback(msg_in):
    return b"unrecognized command"

# ************************************************************************
# New Event Received
# ************************************************************************
def new_msg_callback(msg_type, msg_in):
    if msg_type == ziotc.ZIOTC_MSG_TYPE_GPI:
        process_gpi(msg_in)

    if msg_type == ziotc.ZIOTC_MSG_TYPE_TAG_INFO_JSON:
        process_tag(msg_in)

# ************************************************************************
# Process Tag Event
# ************************************************************************
def process_tag(msg_in):
	global Location
	try:
		msg_in_json = json.loads(msg_in)
		user_bank = msg_in_json["data"]["USER"]
		user1 = user_bank[4:8]
		user5 = user_bank[20:24]
		user6 = user_bank[24:28]
		temperature_calibration = int(user5,16) / 100
		value_chip_temperature_sensor_calibration = int(user6,16) / 8
		user1_bin = bin(int(user1,16))[2:].zfill(16)
		power_ok = int(user1_bin[2:3],2)
		data_temperature_sensor = int(user1_bin[3:],2) / 2**(int(user1_bin[0:2],2))
		expected_code = 1/A * (temperature_calibration - B)
		offset = expected_code - value_chip_temperature_sensor_calibration
		value_temperature = A * (data_temperature_sensor + offset) + B
		msg_in_json["TEMPERATURE"]=value_temperature
		ziotcObject.send_next_msg(ziotc.ZIOTC_MSG_TYPE_DATA, bytearray(json.dumps(msg_in_json).encode('utf-8')))

	except Exception as err:
		tb_lines = [line.rstrip('\n') for line in traceback.format_exception(err.__class__, err, err.__traceback__)]
		logger.err(f"Got Exception : {tb_lines}")	

# ************************************************************************
# Process GPI Events
# ************************************************************************
def process_gpi(msg_in):
    pass

# ************************************************************************
# Entry Point
# ************************************************************************
ziotcObject = ziotc.ZIOTC()
logger = Logger(DEBUG_SERVER, DEBUG_PORT, LOG_ONLY_TO_CONSOLE)
restAPI = RestAPI(logger, REST_API_RETRY_COUNT,ziotcObject)


logger.debug("System Started:  " + str(os.getpid()))
logger.debug("Reader Version: " + restAPI.getReaderVersion())
logger.debug("Reader Serial Number: " + restAPI.getReaderSerial())
logger.debug("Script Version: " + str(os.getenv("VERSION")))

# Start Inventory Scan
restAPI.startInventory()

# Loop Forever
ziotcObject.reg_new_msg_callback(new_msg_callback)
ziotcObject.reg_pass_through_callback(passthru_callback)
ziotcObject.enableGPIEvents()
ziotcObject.loop.run_forever()

# Clean up
restAPI.stopIventory()

logger.info("Stopped")
