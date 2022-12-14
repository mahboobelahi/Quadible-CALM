from pprint import pprint as P
import time,threading,socket,requests
from FASToryLine.dbModels import(Orders,WorkstationCapabilities,PalletObjects,FASToryLineEvents,WorkstationInfo,S1000Subscriptions) 
from FASToryLine import db
from FASToryLine import configurations as CONFIG 
from sqlalchemy import exc
from FASToryLine import ProductionPolicy as WkC
#creating data base modles

WS_obj_list = list()

# create tables in DB
def createModels():
    db.create_all()

def insertPalletInfo(pallet_obj):
        mapped_pallet_obj = PalletObjects(
                                    LotNumber=pallet_obj[1],
                                    PalletID=pallet_obj[0],
                                    FrameType=pallet_obj[2],
                                    FrameColor=pallet_obj[3],
                                    ScreenType=pallet_obj[4],
                                    ScreenColor=pallet_obj[5],	
                                    KeypadType=pallet_obj[6],
                                    KeypadColor=pallet_obj[7],
                                    Status=pallet_obj[8])
        try:
            db.session.add(mapped_pallet_obj)
            db.session.commit()
            print(mapped_pallet_obj.serialize)
            
        except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')

def insertLineEvents(event_notif,id):
    LineEvent = FASToryLineEvents(
                                    SenderID=event_notif.get('senderID'),
                                    Events = event_notif,
                                    Fkey=id
                                )
    try:
        db.session.add(LineEvent)
        db.session.commit()
        print(f'[X] app2: {LineEvent}')     
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

#checking machine local IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# formatting data for orders to make processing easy
def formated_orders(raw_orders):#current_order,
    """
    converts the raw orders, from a query result of DB to a formatted and easy to process dictionary orders list
    :param raw_orders: list of order tuples
    :param row: contains list of tuples
    :return: formatted dictionary orders list
    """
    formatted_orders = list()#{}
    for order in raw_orders:

        key = 'Order_'+str(order[0])#'order_specs'  # + str(row[i][0])
        # order specifications
        for i in range(order[7]):
            temp_=list(
                        (#order[0],
                        'Order'+str(order[0]),
                         {"Frame": list(order[1:3])},
                         {"Screen": list(order[3:5])},
                         {"Keypad": list(order[5:7])}#{"Quantity": order[7]}
                         )
            )
            formatted_orders.append(temp_ )
        #print('HF8: Temp Order: ', formatted_orders)
    return formatted_orders

#called by policyBasedToolChange
def changePen(result):
    try:
        if result.WorkCellID in [1,2,3,4,5,6,7,8]:
            print(f"[X] Workstation_{result.WorkCellID} does not has pen change service....:-(")
            return
        capability = result.getCapabilities
        robServiceURL = result.getURLS.get("Robot_service_url")
        res = requests.post(f'{robServiceURL}GetPenColor',json={}) 
        currentPen = res.json().get("CurrentPen").upper()
        # print(f"[x] {'ERROR' not in capability},  {currentPen =='NA'}")
        # {"id":9,"capabilities":["RED"]}
        if "ERROR" not in capability:
            if currentPen == 'NA': #2,9,10,11,12
                res = requests.post(robServiceURL+f'ChangePen{capability[0]}',json={"destUrl": ""})
                if res.status_code not in [200,202.0]:   
                    print(f'[X]')
                    P(res.json())
                else:
                    print(f'[X] Workstation_{result.WorkCellID} has changed Pencolor to {capability[0]}, ({res.status_code},{res.reason})' )
                return
        
            elif (currentPen != capability[0]):
                res = requests.post(robServiceURL+f'ChangePen{capability[0]}',json={"destUrl": ""})
                if res.status_code not in [200,202.0] :   
                    print(f'[X]')
                    P(res.json())
                else:
                    print(f'[X] Workstation_{result.WorkCellID} has changed Pencolor to {capability[0]}, ({res.status_code},{res.reason})' )
                return
        print(f"[X] Workstation_{result.WorkCellID} already up to date....:-)")
    except requests.exceptions.RequestException as err:
        print(f"[X-Err] for Workstation_{result.WorkCellID} OOps: {err}" ) 

def policyBasedToolChanging(id=None,capability=None):
    try:
        if id:
            WS_obj_list[id-1]. WkSINFO()
            changePen( WorkstationInfo.query.get_or_404(id))
            return
        else:
            for res in WorkstationInfo.query.all():
                changePen(res)
            return
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

def updateDB(result,capability):
    #print(f"[X] {capability}, {result}")
    try:
        result.Capabilities = capability
        db.session.commit()
    except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')

def updateCapability(policyID ):
    try:
        result=Orders.query.filter_by(ProdPolicy=None).all()
        for res in result:
            res.ProdPolicy =policyID 
        db.session.commit() 
        #dynamc input query with "with_entities"
        policyID=4 #test id remove this line during final testing
        WS_capabilities=WorkstationCapabilities.query.with_entities(
                        eval(f'{WorkstationCapabilities.__tablename__}.{CONFIG.ProdIDtoCapability[policyID]}')
                        ).all()        
        
        #static query
        # WS_capabilities=WorkstationCapabilities.query.\
        #                 with_entities(WorkstationCapabilities.Error).all()   
        result = WorkstationInfo.query.all()
        list(map(updateDB,WorkstationInfo.query.all(),[cap for (cap,) in WS_capabilities]))
        time.sleep(1)
        stratPolicyBasedToolChange=threading.Thread(target=policyBasedToolChanging)
        stratPolicyBasedToolChange.daemon=True
        stratPolicyBasedToolChange.start()
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

def getAndSetIsFetchOrders(res):
    try:
        res.IsFetched =True
        db.session.commit() 
        return res.getOrder
        
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

def instencateWorkstations():
    #instentiate Workstation servers according to Production policy
    global  WS_obj_list 
    CONFIG.wrkCellLoc_Port = 2000
    for i in range(1,13):
        #change capabilities for policies
        if i in [1,2,3,4,5,6,7,8]:
            continue
        # if i !=7 and  i!=10:
        #     continue
        # if  i!=10:
        #      continue
        temp_obj=WkC.Workstation(i,CONFIG.wrkCellLoc_Port+i,
                                CONFIG.robot_make[i-1],CONFIG.robot_type[i-1],
                                CONFIG.ComponentStatus[i-1])
        threading.Thread(target=temp_obj.runApp,daemon=True).start()
        time.sleep(0.5)
        print(f'[XHF] Workstation INFO:')
        P(temp_obj.WkSINFO())

        #check record exists in DB otherwise add one
        if not bool(WorkstationInfo.query.filter_by(WorkCellID=i).first()):
            #db.session.query(db.exists().where(WorkstationInfo.id == i)).scalar()
            temp_obj.callWhenDBdestroyed()
        time.sleep(1)
        temp_obj.updateIP()
        WS_obj_list.append(temp_obj)
    print(f"AccessOrchestrtor here: http://{get_local_ip()}:1064")

    #CNV and Robot events subscriptions
    if len(S1000Subscriptions.query.all()) == 0:
        for obj in WS_obj_list:
            if obj.get_ID() == 1:continue
            print('\nSubscription for Workstation_%d\n' % obj.get_ID())
            for zone_name in range(1, 6):
                if zone_name == 5:
                    continue
                obj.CNV_event_subscriptions(zone_name)

            if obj.get_ID() == 1:
                obj.ROB_event_subscriptions('PaperLoaded')
                obj.ROB_event_subscriptions('PaperUnloaded')
            elif obj.get_ID() == 7:
                
                # obj.ROB_event_subscriptions('PalletLoaded')
                obj.ROB_event_subscriptions('PalletUnloaded')
            else:
                #obj.ROB_event_subscriptions('PenChangeStarted')
                #obj.ROB_event_subscriptions('DrawStartExecution')
                obj.ROB_event_subscriptions('PenChangeEnded')
                obj.ROB_event_subscriptions('DrawEndExecution')
    return ""

def sendHTTPReqtoS1000(url, Unsubs=False):
    try: 
        if not Unsubs:
            r=requests.post(url[1],json={"destUrl":f"{url[0]}"})
            print(f"[X] FASTory Line Event Subscription: {r.status_code},{r.reason}")
        else:
             r=requests.delete(url)
             print(f"[X] FASTory Line Event Un-Subscription: {r.status_code},{r.reason}")

    except requests.exceptions.RequestException as err:
        print("[X-Err] OOps: Something Else", err)
def subEvents(url):
    print( f"[X] {url.getSubsEventURLS[1]},{url.getSubsEventURLS[0]}")
    time.sleep(.2)
    sendHTTPReqtoS1000(url.getSubsEventURLS)


def UnSubEvents(url):
    print( f"[X] {url.getUnSubsEventURLS}")
    time.sleep(.2)
    sendHTTPReqtoS1000(url.getUnSubsEventURLS,Unsubs=True)