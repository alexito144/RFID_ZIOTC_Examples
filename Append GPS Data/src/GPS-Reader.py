import ziotc
import json
import os
import traceback
from Logger import Logger
from RestAPI import RestAPI
from NMEA_Receiver import NMEA_Receiver

# Global Variables
UDP_PORT = 9000
DEBUG_SERVER = "192.168.13.140"
DEBUG_PORT = 40514
LOG_ONLY_TO_CONSOLE = False
REST_API_RETRY_COUNT = 3

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
		msg_in_json["latitude"] = Location.getLatitude()
		msg_in_json["longitude"] = Location.getLongitude()
		msg_in_json["valid_fix"] = Location.getValidFix()   
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
Location = NMEA_Receiver(logger,UDP_PORT)

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
Location.close()
logger.info("Stopped")
