import time,socket,requests,threading
from datetime import datetime
from pprint import pprint
from flask import Flask, request, redirect, flash, render_template,jsonify
from FASToryLine import configurations as CONFIG
from FASToryLine import dbModels as DataBase
from FASToryLine import db
from sqlalchemy import exc
from flask_sqlalchemy import SQLAlchemy
from FASToryLine import helperFunctions as HF
from FASToryLine import PalletClass as PC

 #Holds user orders

Drawing_update = True
count =0
#workstation class
class Workstation:
    def __init__(self,ID,port,r_make,r_type,ComponentStatus):
        
        # workstation attributes
        self.ID = ID
        self.job = 0
        self.capabilities = None
        self.ComponentStatus = ComponentStatus
        self.make = r_make
        self.type = r_type
        self.EM = True
        self.port=port
        # workstaion servies
        self.url_self = f'http://{CONFIG.wrkCellLoc_IP}:{self.port}' #use when working in FASTory network
        #self.url_self = f'http://{self.get_local_ip()}:{port}' 
        self.measurement_ADD = f'{self.url_self}/measurements'
        self.EM_service_url = f'http://192.168.{ID}.4/rest/services/send_all_REST'
        self.CNV_service_url = f'http://192.168.{ID}.2/rest/services/'
        self.Robot_url = f'http://192.168.{ID}.1/rest/services/'
        
        #control flags
        self.busy = False
        self.currentPallet = '' # used when robot starts drawing
        self.waitingPallet=''

        # checking for Z4 and installed EM modules
        if self.ID in CONFIG.hav_no_EM:
            self.EM = False
        if ID == 1 or ID == 7:
            self.hasZone4 = False
        else:
            self.hasZone4 = True

    # *****************************************
    #  WorkstationClass mutators section
    # *****************************************
    # accessors
    def callWhenDBdestroyed(self):
        # inserting info to db
        # one time call, only uncomment when db destroyed otherwise
        # do the update
        info = DataBase.WorkstationInfo(
            WorkCellID=self.ID,
            RobotMake = self.make,
            RobotType = self.type,
            HasZone4=self.hasZone4,
            HasEM_Module=self.EM,
            WorkCellIP=self.url_self,
            EM_service_url=self.EM_service_url,
            CNV_service_url=self.CNV_service_url,
            Robot_service_url=self.Robot_url,
            Capabilities = self.capabilities,
            ComponentStatus = self.ComponentStatus

        )
        try:
            db.session.add(info)
            db.session.commit()
        except exc.SQLAlchemyError as err:
            print("[X-W] OOps: Something Else", err)

    def updateIP(self):
        WrkIP = DataBase.WorkstationInfo.query.get(self.ID)
        WrkIP.WorkCellIP = self.url_self
        # WrkIP=WorkstationInfo.query.filter(WorkstationInfo.WorkCellID==self.ID)
        # WrkIP.update({WorkstationInfo.WorkCellIP:self.url_self})
        try:
            db.session.commit()
        except exc.SQLAlchemyError as err:
            print("[X-W] OOps: Something Else", err)
    
    
    # accessors and setters

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def get_ID(self):
        return self.ID

    def get_capabilities(self):
        try:
            return DataBase.WorkstationInfo.query.get_or_404(self.ID).Capabilities 
        except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')

    def get_currentPallet(self):
        return self.currentPallet


    def get_waitingPallet(self):
        return self.waitingPallet

    def WkSINFO(self):

        return self.__dict__

    def is_Workstation_Busy(self):
        return self.busy

    # setters
    def update_capabilities(self,capability):
        try:
            self.capabilities =capability
            result= DataBase.WorkstationInfo.query.get_or_404(self.ID)
            result.Capabilities = capability
            db.session.commit()
        except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')
            
    def set_Busy(self, status):
        self.busy = status

    def update_currentPallet(self, pallet_obj):
        self.currentPallet = pallet_obj
        print(self.currentPallet.get_PID(),"*Updated pallet Obj: ", self.ID)


    def update_job(self, inc):
        self.job += inc



    # *****************************************
    # Subscription section
    # *****************************************

    # Conveyor event subscriptions

    def CNV_event_subscriptions(self, zone_name):
        """
        this method subscribe a workstation to the event for all zones of conveyor
        on that workstation

        :param zone_name:int:zones on convyor
        :return: nothing
        """

        # Prepare URL and body for the environment

        if (self.ID == 1 or self.ID == 7) and zone_name == 4:
            print('WkC_1:_Worksation_%d' % self.ID, 'has no Service for Zone4')
            pass

        else:
            CNV_RTU_Url_s = f'http://192.168.{str(self.ID)}.2/rest/events/Z{str(zone_name)}_Changed/notifs'

            # application URl
            body = {"destUrl": self.url_self+ '/events'}
            
            try:
                r = requests.post(CNV_RTU_Url_s, json=body)
                # print(f'[X] CNV Zone{zone_name} event subscriptions for WK_{self.ID}, {r.reason}')
                
                event_url= DataBase.S1000Subscriptions(
                                Event_url = CNV_RTU_Url_s,
                                Destination_url = self.url_self,
                                Fkey = self.ID)

                db.session.add(event_url)
                db.session.commit()

            except requests.exceptions.RequestException as err:
                print("[X] OOps: Something Else", err)                   
            except exc.IntegrityError as err:
                print("[X] OOps: already exists", err)

    # Robot event subscriptions
    def ROB_event_subscriptions(self, event_name):
        """
        this method subscribe a workstation to the event for all zones of conveyor
        on that workstation

        :param event_name:string:robot services
        :return: nothing
        """

        # Prepare URL and body for the environment
        if self.ID == 1:
            pass
        elif self.ID == 7:
            pass
        else:
            ROB_RTU_Url_s = f'http://192.168.{str(self.ID)}.1/rest/events/{event_name}/notifs'
            # application URl
            body = {"destUrl": self.url_self+ '/events'}
            try:
                r = requests.post(ROB_RTU_Url_s, json=body)
                #print(f'[X] Robot {event_name} event subscriptions for WK_{self.ID}, {r.reason}')
                event_url= DataBase.S1000Subscriptions(
                                Event_url = ROB_RTU_Url_s,
                                Destination_url = self.url_self,
                                Fkey = self.ID)

                db.session.add(event_url)
                db.session.commit()

            except requests.exceptions.RequestException as err:
                print("[X] OOps: Something Else", err)
            except exc.IntegrityError as err:
                print("[X] OOps: already exists", err)

    # *********************************************
    #  WorkstationClass service invocation section
    # *********************************************

    # service invocation on CNVs
    # getting zone status

    def get_zone_status(self, zone_name):
        """
        checks weather a zone is occupied or empty
        :param zone_name:zone at conveyor
        :return:pallet ID at zone
        """
        if (self.ID == 1 or self.ID == 7) and zone_name == 'Z4':
            print('WkC_6_:_Has no Zone 4')
            return ''
        else:
            
            ZONE_staus_Url = self.CNV_service_url+f'Z{str(zone_name)}'
            body = {}
            r = requests.post(ZONE_staus_Url, json=body)
            try:
                # print('Pallet status at '+str(self.ID)+' '+ zone_name + ' :', r.json()['PalletID'])#, r.json()['PalletID']
                return r.json()['PalletID']

            except ValueError:
                print('Decoding JSON has failed......\nPlease rebot CNV RTU! at ', self.FCell)

    # transferring the pallet service
    def TransZone(self,transfer, current_pallet):
        """
        execute the pallet transfer on conveyor
        :param transfer:string:zone name according to FASTory API
        :return:
        """
        # Prepare URL for the environment

        CNV_ser_Url = f'{self.CNV_service_url}TransZone{transfer}'
        # Submit POST request to app for getting event body
        r = requests.post(CNV_ser_Url, json={"destUrl": ""})
        #
        # # Shows response in console
        print(f'Service TransZone{transfer} on WS_{self.ID}, {r.status_code}, {r.reason}')

        if r.status_code==403:
            print('[X] COMMUNICATION IS LOST ???????')
            pprint(current_pallet.info())

    # invoking services on robot

    # pallet loading and unloading
    def pallet_load_unload(self, command):
        """
        :param command:load and unload pallet at workstation 7
        :return:
        """
        # Prepare URL for the environment
        ROB_ser_URL = self.Robot_url+ command
        # Submit POST request
        headers = {"Content-Type": "application/json"}
        r = requests.post(ROB_ser_URL, json={"destUrl": f"{self.url_self}"}, headers=headers)

        # Shows response in console
        # print('\nService ', command, r.status_code, r.reason)

    # papper loading and unloading service

    def paper_loading_unloading(self, command, current_pallet):
        """
        :param command:load and unload paper at workstation 1
        :return:
        """
        # Prepare URL for the environment
        self.update_currentPallet(current_pallet)
        ROB_ser_URL = self.Robot_url+ command
        # Submit POST request
        headers = {"Content-Type": "application/json"}
        r = requests.post(ROB_ser_URL, json={"destUrl": self.url_self+'/events'}, headers=headers)

        self.currentPallet.set_isPaperLoaded(True)
        pprint(self.currentPallet.info())
        # Shows response in console
        # print('\nService ', command, r.status_code, r.reason)

    # Drawingnservices
    def DrawingRecipes(self, current_pallet):
        """
        :param drawing:drawing recipe
        :return:
        """
        pos_update = True
        drawing = ''
        self.update_currentPallet(current_pallet)
        # #specs matching
        #
        # # frame matching
        #
        if current_pallet.get_Frame_specs()['Frame_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Frame_specs()['Frame_Specs'][0] in self.get_capabilities() and \
                current_pallet.get_frame_status() == False:

            drawing = current_pallet.get_Frame_specs()['Frame_Specs'][0]
            current_pallet.update_frame_done(True)

        # screen matching
        elif current_pallet.get_Screen_specs()['Screen_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Screen_specs()['Screen_Specs'][0] in self.get_capabilities() and \
                current_pallet.get_screen_status() == False:

            drawing = current_pallet.get_Screen_specs()['Screen_Specs'][0]
            current_pallet.update_screen_done(True)

        # keypad matching

        elif current_pallet.get_Keypad_specs()['Keypad_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Keypad_specs()['Keypad_Specs'][0] in self.get_capabilities() and \
                current_pallet.get_keypad_status() == False:

            drawing = current_pallet.get_Keypad_specs()['Keypad_Specs'][0]
            current_pallet.update_keypad_done(True)

        # Prepare URL for the environment

        if drawing != '':
            ROB_ser_URL = self.Robot_url+ drawing
            # Submit POST request
            headers = {"Content-Type": "application/json"}
            r = requests.post(ROB_ser_URL, json={"destUrl": ""}, headers=headers)#f"{self.url_self}"
        # Shows response in console
        # print('\nService ',drawing, r.status_code, r.reason)

        # check all parts are printed

        if current_pallet.get_frame_status() == True and \
                current_pallet.get_screen_status() == True and \
                current_pallet.get_keypad_status() == True:
            current_pallet.update_Order_status(True)
            #Update Lot and palletObj status in db
            result=db.session.query(DataBase.PalletObjects).get_or_404(current_pallet.get_PID())
            result.Status = True
            db.session.commit()
        if len(CONFIG.ORDERS) == 0:
            result=db.session.query(DataBase.Orders).filter_by(IsFetched=True).first()
            result.OrderStatus = True
            db.session.commit()
        return pos_update

    # change pencolor
    def changePenColor(self, desire_color):

        """
        :param desire_color:
        :return:
        """
        # Prepare URL for the environment
        ROB_ser_URL = self.Robot_url+f'ChangePen{desire_color}'
        # Submit POST request
        r = requests.post(ROB_ser_URL, json={"destUrl": ""}) #f"{self.url_self}"
        # Shows response in console
        print(f'Workstation {self.ID} has changed Pencolor to {desire_color}..{r.status_code}, {r.reason}' )


    def getPenColor(self):
        """
        :param desire_color:
        :return:
        """
        # Prepare URL for the environment
        ROB_ser_URL = self.Robot_url+'/GetPenColor'
        # Submit POST request
        r = requests.post(ROB_ser_URL, json={"destUrl": f"{self.url_self}"})
        # Shows response in console
        # print('\nService ',r.json(), r.status_code, r.reason)
        return r.json()["CurrentPen"]

    def info(self):
        """
        This method gives information of object on which it is called
        :return: object information dictionary
        """
        return self.__dict__

        ########################MOVE helper#####################

    # rlease workstation
    def release(self,event_notif):
        #only to tackle workstation RFID issue
        if (event_notif['payload'].get('PalletID') == '-1' and \
                 event_notif['senderID'] == 'CNV11'):
            print("[X] AT workstation 11")
            self.TransZone(145,'')
            return ''
        if event_notif['id'] == 'Z3_Changed':
            self.set_Busy(False)
            print(f'[X] From realse with eventID: {id}')
            return ''


    #bypass

    def bypass(self,current_pallet):
        """
        bypass pallet from 1-4-5 as well as from 1-2 if
        workstation is capable to perform a job on pallet
        :param current_pallet:
        :return:
        """
        permission=False

        # capability analyze condition block
        frame_condition=(current_pallet.get_Frame_specs()['Frame_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Frame_specs()['Frame_Specs'][0] in self.get_capabilities() and\
            (not current_pallet.get_frame_status()) )

        screen_condition=(current_pallet.get_Screen_specs()['Screen_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Screen_specs()['Screen_Specs'][0] in self.get_capabilities() and\
            (not current_pallet.get_screen_status()) )

        keypad_condition=(current_pallet.get_Keypad_specs()['Keypad_Specs'][1] in self.get_capabilities() and \
                current_pallet.get_Keypad_specs()['Keypad_Specs'][0] in self.get_capabilities() and\
            (not current_pallet.get_keypad_status()) )

        check = (current_pallet.get_paperloaded() and
                 not current_pallet.get_order_status() and
                 not self.is_Workstation_Busy())
        print(f'[X] FSK {self.get_capabilities() },{frame_condition},{screen_condition},{keypad_condition}')
        permission = (frame_condition or\
                     screen_condition or\
                     keypad_condition)
        print(f'[X] permission>>>> {permission}')
        print(f'[X] check>>>> {check}')
        print(f'[X] permissionANDcheck ({permission and check})')

        if (self.get_ID() == 7 or self.get_ID() == 1 or (permission and check)):

            current_pallet.set_current_zone(1)
            current_pallet.set_next_zone(2)
            self.set_Busy(True)

            print(f'[X] {current_pallet.get_PID()},#####################From_B1###########################')
            print(f"[X] PalletInfo {current_pallet.info()}")
            print(f'[X] bypass_{self.get_ID()}, {current_pallet.get_PID()}, {current_pallet.get_current_zone()}, {current_pallet.get_next_zone()}')
            print(f"[X] Transfering pallet at Workstation_{self.ID}from Z{current_pallet.get_current_zone()} to Z{current_pallet.get_next_zone()}")
            threading.Timer(0.1,self.TransZone,args=(str(current_pallet.get_current_zone()) +
                           str(current_pallet.get_next_zone()),current_pallet)).start()

        # Original Bypass
        else:
            if current_pallet.get_current_zone() == 1:
                current_pallet.set_next_zone(4)
                print(f'[X] {current_pallet.get_PID()}, #####################Original Bypass+1###########################')
            elif current_pallet.get_current_zone() == 4:
                current_pallet.set_next_zone(5)
                print(f'[X] {current_pallet.get_PID()},#####################Original Bypass+2###########################')
            elif current_pallet.get_current_zone() == 3:
                current_pallet.set_next_zone(5)
                print(f'[X] {current_pallet.get_PID()},#####################Original Bypass+3###########################')
            else:
                print(f'[X] {current_pallet.get_PID()},#####################Original Bypass###########################')
                current_pallet.set_current_zone(1)
                current_pallet.set_next_zone(4)

            print(f'[X] {current_pallet.get_PID()},#####################From_B3###########################')
            print(f'[X] bypass_{self.get_ID()}, {current_pallet.get_PID()}, {current_pallet.get_current_zone()}, {current_pallet.get_next_zone()}')
            print(f"[X] Transfering pallet at Workstation_{self.ID} from Z{current_pallet.get_current_zone()} to Z{current_pallet.get_next_zone()}")
            
            threading.Timer(0.2, self.TransZone, args=(str(current_pallet.get_current_zone()) +
                           str(current_pallet.get_next_zone()),current_pallet)).start()
        return ''
    # main with drawing

    def main_transfer_wd_drawing(self,current_pallet):
        global Drawing_update
        Drawing_update = True
        pos_status = True
        print('[X]----------main_transfer_wd_drawing----------')

        permission = False

        # capability analyze condition block
        frame_condition = (current_pallet.get_Frame_specs()['Frame_Specs'][1] in self.get_capabilities() and \
                           current_pallet.get_Frame_specs()['Frame_Specs'][0] in self.get_capabilities() and \
                           (not current_pallet.get_frame_status()))

        screen_condition = (current_pallet.get_Screen_specs()['Screen_Specs'][1] in self.get_capabilities() and \
                            current_pallet.get_Screen_specs()['Screen_Specs'][0] in self.get_capabilities() and \
                            (not current_pallet.get_screen_status()))

        keypad_condition = (current_pallet.get_Keypad_specs()['Keypad_Specs'][1] in self.get_capabilities() and \
                            current_pallet.get_Keypad_specs()['Keypad_Specs'][0] in self.get_capabilities() and \
                            (not current_pallet.get_keypad_status()))

        check = (current_pallet.get_paperloaded() and
                 not current_pallet.get_order_status() and
                 not self.is_Workstation_Busy())

        permission = (frame_condition or\
                     screen_condition or\
                     keypad_condition)
        #paper Load
        if self.get_ID() == 1 and \
            current_pallet.get_current_zone() == 3 and \
                current_pallet.get_paperloaded( ) == False:

            self.paper_loading_unloading('LoadPaper',current_pallet)
            pos_status = False
            return pos_status

        elif self.get_ID() == 7 and \
            current_pallet.get_current_zone() == 3 and \
            current_pallet.get_paperloaded( ) == True and\
            current_pallet.get_order_status() == True:

            global  count
            count = count+1
            self.pallet_load_unload('UnloadPallet')
            pos_status = False;
            print('[X] ???????????????',count)
            print(current_pallet.info())
            CONFIG.pallet_objects.pop(current_pallet.get_PID())
            return pos_status
        
        # drawing command
        elif (self.get_ID() !=7 and self.get_ID()!=1) and \
                current_pallet.get_current_zone() == 3 and\
                 not current_pallet.get_order_status()  and\
                current_pallet.get_paperloaded( ) == True and\
                permission:
            Drawing_update = False
            pos_status =threading.Timer(1,self.DrawingRecipes,args=(current_pallet,)).start()

            return pos_status

        else:
            print(f'[X] {current_pallet.get_PID()},#####################From_M1###########################')
            print(f"[X] Transfering pallet at Workstation_{self.ID}from Z{current_pallet.get_current_zone()} to Z{current_pallet.get_next_zone()}")
            threading.Timer(0.1, self.TransZone, args=(str(current_pallet.get_current_zone()) +
                       str(current_pallet.get_next_zone()), current_pallet)).start()
        return pos_status

    #start process

    def startprocess(self,event_notif):

        global Drawing_update
        Drawing_update = True
        pos_status = True

        if event_notif['id'] == 'PenChangeEnded' or\
            event_notif['id'] == 'PenChangeStarted' or\
                event_notif['id'] == 'DrawStartExecution':
                    print(f"[X] {event_notif['id']} event successfull for {event_notif.get('senderID')}")
                    return ''
        #accessing palletID by avoiding keyerror
        palletID = event_notif['payload'].get('PalletID',0)
        print(f"[X] PalletID and ID type: {palletID}---{type(palletID)}")
        
        if event_notif['payload'].get('PalletID') == '-1' and \
            event_notif['id'] != 'PaperLoaded':

            self.release(event_notif)
            return ''
        else:
            if event_notif['id'] == 'DrawEndExecution' or \
                    event_notif['id'] == 'PenChangeEnded':

                current_pallet =  CONFIG.pallet_objects[self.get_currentPallet().get_PID()]

            elif palletID !=0 :
                    if event_notif['payload'].get('PalletID') in CONFIG.pallet_objects.keys():
                        print(f"[X] if PalletID !=0")
                        current_pallet = CONFIG.pallet_objects[palletID]
            else:
                current_pallet = self.get_currentPallet()
                print(f"[X] if PalletID == 0>>>{current_pallet}")
            # movement between Zones
            print(current_pallet.info())
            if  current_pallet.get_current_zone() == 1 or \
                current_pallet.get_current_zone() == 4 or \
                current_pallet.get_current_zone() == 5:
                print(f'[X] {current_pallet.get_PID()}, #####################_F1_###########################')
                self.bypass(current_pallet)
            else:
                if current_pallet.get_current_zone() == 2:
                    current_pallet.set_next_zone(3)
                    print(f'[X] {current_pallet.get_PID()},#####################_F2_###########################')
                elif current_pallet.get_current_zone() == 3:
                    current_pallet.set_next_zone(5)
                    print(f'[X] {current_pallet.get_PID()},#####################_F3_###########################')
                print(f'Drawing condition: {pos_status and Drawing_update}, at {self.ID}, with palletID {current_pallet.get_PID()}, #####################main_transfer_wd_drawing###########################')
                pos_status = self.main_transfer_wd_drawing(current_pallet)

        if pos_status and Drawing_update:

            current_pallet.set_current_zone(current_pallet.get_next_zone())
            print(f'[X] POS>>>>,{self.get_ID()}, {current_pallet.get_PID()}, {current_pallet.get_current_zone()}, {current_pallet.get_next_zone()}')
            
    #*******************************************
    #   Flask Application
    #*******************************************

    def runApp(self):
        """
        Set the flask application
        :return:none
        """
        app = Flask(__name__,template_folder='templates') #,template_folder='/Quadible-CALM/FASToryLine/'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{CONFIG.DB_USER}:{CONFIG.DB_PASSWORD}@{CONFIG.DB_SERVER}/{CONFIG.DB_NAME}'
        app.config['SECRET_KEY'] = "stringrandom"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db = SQLAlchemy(app)
        
        @app.route('/')
        def welcome():
            
            result=DataBase.WorkstationInfo.query.get(self.ID)
            print(result.LineEvents)
            context = {"ID": self.ID, "url": self.url_self,"lineEvents":[res.getEventAsCSV for res in result.LineEvents]}
            print(context)
            return render_template(f'workstations/Welcome.html',
                                    title=f'Station_{self.ID}',
                                    content=context)

        @app.route('/info')  # ,methods=['GET']
        def info():
            info=DataBase.WorkstationInfo.query.get(self.ID)

            print(info.ComponentStatus,info.Capabilities)
            return render_template("workstations/info.html",
                                    title='Information',
                                    info=DataBase.WorkstationInfo.query.get(self.ID))
        # fetch ordrs from Database
        @app.route('/startProduction', methods=['POST'])
        def startProduction():
            try:
                HF.getAndSetIsFetchOrders()  
            except exc.SQLAlchemyError as e:
                print(f'[XE] {e}')
            print('[X] ORDERS_List from ProdLot: \n')
            pprint(CONFIG.ORDERS) 
            flash('Production lot ready for process')
            return redirect("http://127.0.0.1:1064/placeorder")
        
        @app.route('/events', methods=['POST'])
        def events():
            global count

            try:
                event_notif = request.json
                HF.insertLineEvents(event_notif,self.ID)
                print(f'[X] New event received: {event_notif}')
                if len(CONFIG.ORDERS) != 0:
                    
                    if (
                        event_notif.get('id') == 'Z1_Changed' and\
                        event_notif.get('senderID') == 'CNV09' and\
                        event_notif['payload'].get('PalletID','-1')!= '-1' and\
                        event_notif['payload'].get('PalletID') not in CONFIG.pallet_objects
                    ):
                        temp = CONFIG.ORDERS.pop(0)
                        
                        """
                            type:tuple-4
                            0:{'LotNumber': 1, 'timestamp': ['2022-09-17', '22:03:25'], 'Quantity': 1, 'Prodpolicy': 4}
                            1:{'Frame_Specs': ['Draw2', 'RED']}
                            2:{'Screen_Specs': ['Draw8', 'GREEN']}
                            3:{'Keypad_Specs': ['Draw5', 'BLUE']}
                        """
                        PID = event_notif.get('payload').get('PalletID')

                        CONFIG.pallet_objects[PID] = PC.Pallet(PID, temp[0].get("LotNumber"), temp[1], temp[2], temp[3])
                        print(f'[X] PalletInfo {CONFIG.pallet_objects[PID].info()}')
                        pallet_obj = CONFIG.pallet_objects[PID].info()
                        HF.insertPalletInfo(pallet_obj)
                        count =count+1
                        print(f"[X] Count>>>> {count}")
                else:
                    try:
                        #handle none type attri
                        HF.getAndSetIsFetchOrders()
                        print(f'[X] Fetching Next Order {CONFIG.ORDERS}')
                    except exc.SQLAlchemyError as e:
                        print(f'[XE] {e}')

            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                    print('[X] Decoding JSON has failed')
            except exc.SQLAlchemyError as e:
                    print(f'[XE] {e}')

            print(f'[X]: Remaining orders: {len(CONFIG.ORDERS)}')
            # master function
            self.startprocess(event_notif)

            return 'OK'
        ################# API ##############
        @app.route('/api-fetchNextOrder', methods=['POST'])
        def apiFetchNextOrder():
            
            try:
                result = DataBase.WorkstationInfo.query.filter_by(WorkCellID=7).first()
                # result= DataBase.Orders.query.filter_by(IsFetched=False).all()
                [CONFIG.ORDERS.append(HF.getAndSetIsFetchOrders(res)) for res in result.FetchOrders if not(res.IsFetched)]   
                print('[X-API] ORDERS_: \n')
                pprint(CONFIG.ORDERS) 
                return jsonify(Response=200)
            except exc.SQLAlchemyError as e:
                print(f'[X-API] {e}')
                return jsonify(Response=e)
    
        app.run('0.0.0.0',port=self.port,debug=False)
