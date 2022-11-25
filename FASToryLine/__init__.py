from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from FASToryLine import configurations as CONFIG

app = Flask(__name__)


########using flask-mqtt for message bus connection##########
app.config['MQTT_CLIENT_ID'] = CONFIG.MQTT_CLIENT_ID
app.config['MQTT_USERNAME'] = CONFIG.NAME
app.config['MQTT_BROKER_URL'] = CONFIG.zMQTT_BROKER_URL  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = CONFIG.zMSG_TLS_PORT#zMSG_PORT_VPN # default port for non-tls connection
app.config['MQTT_USERNAME'] = CONFIG.MQTT_USERNAME  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = CONFIG.MQTT_PASSWORD  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = CONFIG.Conn_ALIVE  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = CONFIG.MQTT_TLS_ENABLED # set TLS to disabled for testing purposes
#app.config['MQTT_TLS_CA_CERTS'] = CONFIG.MQTT_TLS_CERTFILE
#app.config['MQTT_TLS_INSECURE'] = True-'MQTT_TLS_CERTFILE'
#New MySQL DB
#'mysql://username:passward@localhost/<databasename>'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{CONFIG.DB_USER}:{CONFIG.DB_PASSWORD}@{CONFIG.DB_SERVER}/{CONFIG.DB_NAME}'
#f"sqlite:///{CONFIG.DB_NAME}.db" 
#f'mysql+pymysql://{CONFIG.DB_USER}:{CONFIG.DB_PASSWORD}@{CONFIG.DB_SERVER}/{CONFIG.DB_NAME}'
app.config['SECRET_KEY'] = "stringrandom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def dump_datetime(value):
        """Deserialize datetime object into string form for JSON processing."""
        if value is None:
            return None
        return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
#to avoid circular imports
from FASToryLine import messageBus