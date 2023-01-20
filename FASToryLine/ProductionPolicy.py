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

    # Conveyor event subscriptions handlers

    def CNV_event_subscriptions(self, zone_name,Unsub=True):
        """
        this method subscribe a workstation to the event for all zones of conveyor
        on that workstation

        :param zone_name:int:zones on convyor
        :return: nothing
        """

        # Prepare URL and body for the environment
        CNV_RTU_Url_s = f'http://192.168.{str(self.ID)}.2/rest/events/Z{str(zone_name)}_Changed/notifs'
        if Unsub:
            if (self.ID == 1 or self.ID == 7) and zone_name == 4:
                print(f'[X] Worksation_{self.ID}, has no bypass CNV')
                pass

            else:
                try:
                    r = requests.delete(CNV_RTU_Url_s)
                    if r.status_code == 404:
                        print(f"No subscriptions found for Workstation_{self.ID}:{CNV_RTU_Url_s.split('/')[-2]} CNV event")
                except requests.exceptions.RequestException as err:
                    print("[X] OOps: Something Else", err)
        else:
            if (self.ID == 1 or self.ID == 7) and zone_name == 4:
                print(f'[X] Worksation_{self.ID}, has no bypass CNV')
                pass

            else:

                # application URl
                body = {"destUrl": f"{self.url_self}/events"}
                id=''
                status_code=0
                try:

                    isSubscribed,eventId = HF.checkSubscription(CNV_RTU_Url_s,body)

                    if isSubscribed == False and eventId == None:
                        print(f"[X] Workstation_{self.ID}' is subscribing for CNV_Zone {CNV_RTU_Url_s.split('/')[-2]} event :-(")
                        r = requests.post(CNV_RTU_Url_s, json=body)
                        # print(f'[X] CNV Zone{zone_name} event subscriptions for WK_{self.ID}, {r.reason}')
                        status_code = r.status_code
                        if r.status_code == 404:
                            id = f"{self.ID}:{CNV_RTU_Url_s.split('/')[-2]}:{r.reason}:{r.status_code}"
                            
                        else:
                            id = r.json().get("id")
                        # print('[X] ',db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=CNV_RTU_Url_s).scalar())
                        # print('[X] ',db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=CNV_RTU_Url_s).scalar() is not None)
                        # print('[X] ',db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=CNV_RTU_Url_s).scalar() is None)
                        if (db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=CNV_RTU_Url_s).scalar() is None):
                            event_url= DataBase.S1000Subscriptions(
                                Event_url = CNV_RTU_Url_s,
                                Destination_url = self.url_self,
                                eventID = id,
                                Fkey = self.ID)

                            db.session.add(event_url)
                            db.session.commit()
                            return 

                        else:
                            print(f"[X] Prevous subscription for CNV {CNV_RTU_Url_s.split('/')[-2]} event for Workstation_{self.ID} wae deleted :-)")
                            print(f"[X] Updating subscriptions......")
                            #r = requests.post(CNV_RTU_Url_s, json=body)
                            if (DataBase.S1000Subscriptions.query.filter_by(Event_url=CNV_RTU_Url_s).first().eventID !=\
                                r.json().get("id")) and status_code!=404:
                                result=db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=CNV_RTU_Url_s).first()
                                result.eventID = id
                                db.session.commit()
                                return
                            else:
                                print(f"[X] Subscriptions is already Uptodate ......")
                    if isSubscribed == True and eventId != None:
                        print(f"[X] Workstation_{self.ID} already has subscription for CNV_Zone {CNV_RTU_Url_s.split('/')[-2]} event:-)")
                        return 
                except TypeError:
                    print("[X] OOps: Type Error")
                except requests.exceptions.RequestException as err:
                    print("[X] OOps: Something Else", err)                   
                except exc.IntegrityError as err:
                    print("[X] OOps:", err)

    # Robot event subscriptions handlers

    def ROB_event_subscriptions(self, event_name,Unsub=True):
        """
        this method subscribe a workstation to the event for all zones of conveyor
        on that workstation

        :param event_name:string:robot services
        :return: nothing
        """
        ROB_RTU_Url_s = f'http://192.168.{str(self.ID)}.1/rest/events/{event_name}/notifs'
        # Prepare URL and body for the environment
        if Unsub:
            try:
                r = requests.delete(ROB_RTU_Url_s)
                if r.status_code == 404:
                    print(f"No subscriptions found for Workstation_{self.ID}:{ROB_RTU_Url_s.split('/')[-2]} robot event")
            except requests.exceptions.RequestException as err:
                print("[X] OOps: Something Else", err)
        else:
            if self.ID == 1 or self.ID==7:
                pass

            else:
                # application URl
                body = {"destUrl": self.url_self+ '/events'}
                id=''
                status_code = 0
                try:
                    isSubscribed,eventId = HF.checkSubscription(ROB_RTU_Url_s,body)

                    if isSubscribed == False and eventId == None:
                        print(f"[X] Workstation_{self.ID}' is subscribing for ROB {ROB_RTU_Url_s.split('/')[-2]} event :-(")
                        r = requests.post(ROB_RTU_Url_s, json=body )
                        # print(f'[X] ROB Zone{zone_name} event subscriptions for WK_{self.ID}, {r.reason}')
                        
                        status_code = r.status_code
                        if r.status_code == 404:
                            id = f"{self.ID}:{ROB_RTU_Url_s.split('/')[-2]}:{r.reason}:{r.status_code}"
                        else:
                            id = r.json().get("id")
                        if db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=ROB_RTU_Url_s).scalar() is None:
                            event_url= DataBase.S1000Subscriptions(
                                            Event_url = ROB_RTU_Url_s,
                                            Destination_url = self.url_self,
                                            eventID = id,
                                            Fkey = self.ID)

                            db.session.add(event_url)
                            db.session.commit()
                            return 
                        else:
                            print(f"[X] Prevous subscription for ROB {ROB_RTU_Url_s.split('/')[-2]} event for Workstation_{self.ID} was deleted :-)")
                            print(f"[X] Updating subscriptions......")
                            #r = requests.post(ROB_RTU_Url_s, json=body)
                            if (DataBase.S1000Subscriptions.query.filter_by(Event_url=ROB_RTU_Url_s).first().eventID !=\
                                r.json().get("id"))  and status_code!=404:
                                result=db.session.query(DataBase.S1000Subscriptions).filter_by(Event_url=ROB_RTU_Url_s).first()
                                result.eventID = id
                                db.session.commit()
                                return
                            else:
                                print(f"[X] Subscriptions is already Uptodate ......")
                                return
                    elif isSubscribed == True and eventId != None:
                        print(f"[X] Workstation_{self.ID} already has subscription for ROB {ROB_RTU_Url_s.split('/')[-2]} event:-)")
                        return 
                    else:
                        print(f"[X] In else block")
                except TypeError:
                    print("[X] OOps: Type Error")
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
        if self.ID==11:
            print(transfer)
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
        # specs matching
        
        # frame matching
        
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
        try:
            if current_pallet.get_frame_status() == True and \
                    current_pallet.get_screen_status() == True and \
                    current_pallet.get_keypad_status() == True:
                current_pallet.update_Order_status(True)
                #Update Lot and palletObj status in db
                print(f"[X] Updating order status.....")
                current_pallet.get_PID()
                
                result=db.session.query(DataBase.PalletObjects).filter_by(PalletID=current_pallet.get_PID()).first_or_404()
                if result!=404:
                    result.Status = True
                    db.session.commit()
                    print(f"[X] Order status updated")

                # checking for processed orders from a lot 
                orderQuantity = DataBase.Orders.query.get_or_404(current_pallet.get_Order_Alias()).Quantity
                processedPallets = DataBase.PalletObjects.query.filter(
                                    DataBase.PalletObjects.LotNumber==current_pallet.get_Order_Alias(),
                                    DataBase.PalletObjects.Status==True ).count() 
                print(f"[X] Updating order status.....")
                if orderQuantity == processedPallets:
                    result=db.session.query(DataBase.Orders).get_or_404(current_pallet.get_Order_Alias())#filter_by(IsFetched=True).first()
                    if result !=404:
                        result.OrderStatus = True
                        db.session.commit()
                        print(f"[X] Lot status updated")
                        # print(f"[X] {list(CONFIG.pallet_objects.keys())}")
                        # print(f"[X] {list(CONFIG.pallet_objects.pop(current_pallet.get_PID()))}")
                        
        except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')
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
                        print(f'[X] Found pallet objects with ID: {palletID}::{CONFIG.pallet_objects.get(palletID)}')
                        return
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
        
        @app.route('/<name>')
        @app.route('/',defaults={'name': None})
        def welcome(name):
            # result=DataBase.WorkstationInfo.query.get(self.ID)
            # print(result.LineEvents)
            # context = {"ID": self.ID, "url": self.url_self,"lineEvents":[res.getEventAsCSV for res in result.LineEvents]}
            # print(context)
            #For displaying workcell events on UI with pagination
            queryParam = ''
            if name:
                queryParam = f"{name+str(self.ID)}"

             
            page = request.args.get('page',1,type=int)#Fkey=self.ID
            lineEvents= DataBase.FASToryLineEvents.query.filter_by(SenderID=queryParam).order_by(
               DataBase.FASToryLineEvents.id.desc()).paginate(per_page=10, page=page )
            print(f"""[X] {lineEvents.items}, {lineEvents.total}""")
            return render_template(f'workstations/Welcome.html',
                                    title=f'Station_{self.ID}',
                                    ID=self.ID,url= self.url_self,
                                    lineEvents=lineEvents,
                                    name=name)

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

        #events from line receives here
        #vital for FASTory service orchestration
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
