from  flask_mqtt import Mqtt
from sqlalchemy import exc
from FASToryLine.configurations import BASE_TOPIC
from FASToryLine.dbModels import AuthResult,Emotion
from FASToryLine import app,db
import json,datetime
from pprint import pprint as P
mqtt = Mqtt(app)
#####MQTT callbacks################

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc==0:
        mqtt.unsubscribe_all()
        mqtt.subscribe(f'{BASE_TOPIC}authentication')
        print(f'[X-Routes] Subscribed to topic: {BASE_TOPIC}authentication')
        mqtt.subscribe(f'{BASE_TOPIC}emotion')
        print(f'[X-Routes] Subscribed to topic: {BASE_TOPIC}emotion')   
    else:
        print("[X-Routes] Bad connection Returned code=",rc)

@mqtt.on_subscribe()
def handle_subscribe(client, userdata, mid, granted_qos):
    print('[X-Routes] Subscription id {} granted with qos {}.'
          .format(mid, granted_qos))   

@mqtt.on_disconnect()
def handle_disconnect():
    mqtt.unsubscribe_all()
    print("[X-Routes] CLIENT DISCONNECTED")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        message_in=json.loads(message.payload)
        #print(f"[X-Routes] {type(message_in)},'??',{message_in}")
        if  message.retain ==1:
            print(f'[X] Retained message from zRefApp......')
            return     
        
        if message.topic == f'{BASE_TOPIC}authentication':
        
            authResults = message_in
            result = AuthResult(    
                            Authenticated = authResults.get("authenticated"),  
                            Description = authResults.get("description"),
                            DetectedFaces = authResults.get("detectedFaces"), 
                            DistanceScore = authResults.get("distanceScore")
                            )
            db.session.add(result)
            db.session.commit()
            print(f'[X]: Auth result added to DB @ {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        elif message.topic == f'{BASE_TOPIC}emotion':
            #{"detail":"Not a valid file was uploaded"}
            if message_in.get("Response"):
                result = Emotion(    
                                StressLevel = message_in.get("Response").get('stress_level')
                                )
                db.session.add(result)
                db.session.commit()
                print(f'[X]: Emotion result added to DB @ {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                result = Emotion(    
                Description = message_in.get("detail")
                )
                db.session.add(result)
                db.session.commit()
                print(f'[X]: Emotion result added to DB @ {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')
    except ValueError:
        print('[X-Routes] Decoding JSON has failed')

# @app.route('/welcomes', methods = ['GET'])
# def welcomes():
#         return ''
