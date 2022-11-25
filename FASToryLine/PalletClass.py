#pallet class

from pprint import pprint


class Pallet:
    def __init__(self,PID,OPID,Frame_specs,Screen_specs,Keypad_specs):
        # pallet ID attributes
        self.PID = PID
        self.Order_Alias =OPID

        # order specifications
        self.Frame_Specs = Frame_specs
        self.Screen_Specs = Screen_specs
        self.Keypad_Specs = Keypad_specs

        # status attributes
        self.is_order_completed = False
        self.frame_done = False
        self.keypad_done = False
        self.screen_done = False
        self.is_Paper_Loaded = False
        self.is_Paper_UnLoaded = False

        #zone attributes
        self.current_zone = 1
        self.next_zone = 4

    #mutators for palletClass
    # accessors
    def get_PID(self):
        return self.PID

    def get_Order_Alias(self):
        return self.Order_Alias

    def get_Frame_specs(self):
        return self.Frame_specs

    def get_Screen_specs(self):
        return self.Screen_specs

    def get_Keypad_specs(self):
        return self.Keypad_specs

    def get_quantity(self):
        return self.quantity

    def get_order_status(self):
        return self.is_order_completed

    def get_frame_status(self):
        return self.frame_done

    def get_screen_status(self):
        return self.screen_done

    def get_keypad_status(self):
        return self.keypad_done

    def get_paperUnloaded(self):
        return self.is_Paper_UnLoaded

    def get_paperloaded(self):
        return self.is_Paper_Loaded

    def get_current_zone(self):
        return self.current_zone

    def get_next_zone(self):
        return self.next_zone

    # setters

    def update_frame_done(self,status):
        self.frame_done = status
        print('PC1: Frame status updated: ',self.frame_done)

    def update_screen_done(self,status):
        self.screen_done = status
        print('PC2: Screen status updated: ',self.screen_done)

    def update_keypad_done(self,status):
        self.keypad_done = status
        print('PC3: keypad status updated: ',self.keypad_done)

    def update_Order_status(self,status):
        self.is_order_completed = status
        print('PC4: Oreder completed: ', self.is_order_completed)

    def set_isPaperLoaded(self,status):
        self.is_Paper_Loaded = status
        print('PC5: Paper loaded: ',self.is_Paper_Loaded)
        pprint(self.info())

    def set_isPaperUnLoaded(self,status):
        self.is_Paper_UnLoaded = status
        print('PC6: Paper Unloaded: ',self.is_Paper_UnLoaded)

    def set_current_zone(self,zone):
        self.current_zone = zone
        #print('HF7: Current Zone: ', self.current_zone)

    def set_next_zone(self,zone):
         self.next_zone = zone
         #print('HF8: Next Zone: ', self.next_zone)


    # retrieve order info
    def info(self):
        pallet_info = [
            self.get_PID(),self.get_Order_Alias(),
            self.get_Frame_specs()['Frame_Specs'][0],self.get_Frame_specs()['Frame_Specs'][1],
            self.get_Screen_specs()['Screen_Specs'][0], self.get_Screen_specs()['Screen_Specs'][1],
            self.get_Keypad_specs()['Keypad_Specs'][0], self.get_Keypad_specs()['Keypad_Specs'][1],self.get_order_status()
        ]
        return  pallet_info


#########END_OF_PALLET_CLASS#########