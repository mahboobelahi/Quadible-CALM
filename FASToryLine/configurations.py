#DB#####
DB_USER="FASToryProduction"
DB_PASSWORD = "FASToryProduction2020!"
DB_SERVER = "localhost"
DB_NAME = "Production"

##############################MQTT-Settings###########################################
BASE_TOPIC ='OpenCall2/CALM/result/'
Conn_ALIVE = 60
NAME = 'CALM'
MQTT_CLIENT_ID = 'FASToryEMOrchestrator'
zMSG_TLS_PORT = 8883#30206
zMQTT_BROKER_URL = 'msgbus-zdmp.platform.zdmp.eu'  # public ZDMP messageBus
#MQTT_BROKER_PORT = zMSG_PORT  # default port for non-tls connection
MQTT_USERNAME = 'tau'  # set the username here if you need authentication for the broker
MQTT_PASSWORD = 'ZDMP-tau2020!' # set the password here if the broker demands authentication
MQTT_KEEPALIVE = Conn_ALIVE  # set the time interval for sending a ping to the broker to 5 seconds
MQTT_TLS_ENABLED = True  # set TLS to disabled for testing purposes
MQTT_TLS_CERTFILE = './files/ca_certificate.pem' 
MQTT_REFRESH_TIME = 1.0  # refresh time in seconds

##########Orchestrator###############
orchestrator_IP = '0.0.0.0'#'192.168.100.100' ''
orchestrator_Port = 1064
WorkStations = [1,2,3,4,5,6,7,8,9,10,11,12] #FASTory Line's workcells
wrkCellLoc_IP = '192.168.100.100'
wrkCellLoc_Port = 2000
hav_no_EM = [1,7,8] #  workcells that have no/out of order EM modules
energy_meters=[2,3,4,5,6,9,10,11,12]
robot_make = ["Yaskawa","Sony","Kuka","ABB","Omron-Adept","Sony","N/A","Omron-Adept","Sony","Sony",   "Sony","Sony"]
robot_type = ["Dual-Arm","SCARA","6-axis","6-axis","6-axis","SCARA","N/A","SCARA-eCobra","SCARA",     "SCARA","SCARA","SCARA"]

ComponentStatus =[
    #[MainConveyor,BypassConveyor,Robot]
    [False,None,True],[True,True,True],[True,True,False],
    [True,True,False],[True,True,False],[True,False,False],
    [True,None,False],[True,True,False],[True,True,True],
    [True,True,True],[True,True,True],[True,True,True]
]
ProdIDtoCapability={
    1:"ReferancePolicy",
    2:"FixedColorPolicy",
    3:"FixedColorRecipePolicy",
    4:"Error"
}