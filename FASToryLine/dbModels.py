from datetime import datetime
from FASToryLine import db,dump_datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

class WorkstationInfo(db.Model):
    __tablename__ = 'workstationInfo'
    id = db.Column(db.Integer, primary_key=True)
    #WorkCellName = db.Column(db.String(255), unique=True, nullable=False)
    WorkCellID = db.Column(db.Integer, unique=True, default=0,nullable=False)
    RobotMake = db.Column(db.String(20),nullable=False)
    RobotType = db.Column(db.String(20),nullable=False)
    HasZone4 = db.Column(db.Boolean)
    HasEM_Module = db.Column(db.Boolean)
    WorkCellIP = db.Column(db.String(255), unique=True, nullable=False)
    EM_service_url = db.Column(db.String(255), unique=True, nullable=False)
    CNV_service_url = db.Column(db.String(255), unique=True, nullable=False)
    Robot_service_url = db.Column(db.String(255), unique=True, nullable=False)
    Capabilities= db.Column(db.JSON, nullable=True)
    ComponentStatus= db.Column(db.JSON, nullable=True)
    #relations
    ProcessedComponents= db.relationship('CompletedComponents',backref='components',lazy=True)#,uselist=False
    LineEvents= db.relationship('FASToryLineEvents',backref='SimEvents',lazy=True)#,uselist=False
    S1000Subscriptions =db.relationship('S1000Subscriptions',backref='Subscriptions',lazy=True)#,uselist=False
    FetchOrders =db.relationship('Orders',backref='Fetch)unProcessedOrders',lazy=True)
    def __repr__(self):
        return f"Workstation('{self.__dict__}')"
    
    @hybrid_property
    def getCapabilities(self):
        return self.Capabilities

    @hybrid_property
    def getURLS(self):
        return {
            "WorkCellIP":self.WorkCellIP,
            "EM_service_url":self.EM_service_url,
            "CNV_service_url" :self.CNV_service_url,
            "Robot_service_url" :self.Robot_service_url
        }


class S1000Subscriptions(db.Model):
    __tablename__ = 'EventsSubscriptions'
    id = db.Column(db.Integer, primary_key=True)
    Event_url = db.Column(db.String(255), unique=True, nullable=False)
    Destination_url = db.Column(db.String(255), unique=False, nullable=False)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationInfo.id'),nullable=False)

    @hybrid_property
    def getSubsEventURLS(self):
        return (f'{self.Destination_url}/events',self.Event_url)
    @hybrid_property
    def getUnSubsEventURLS(self):
        return self.Event_url.split('/notifs')[0]

class FASToryLineEvents(db.Model):
    __tablename__ = 'FASToryLineEvents'
    id = db.Column(db.Integer, primary_key=True)
    SenderID = db.Column(db.String(15))
    Events= db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationInfo.id'),nullable=False)
    
    def __repr__(self):
        return f"('Events:{self.SenderID}')"

    @hybrid_property
    def getEventAsJSON(self):
       """Return object data in easily serializable format"""
                #        "eventID":self.Events.get('id'), "Sender":self.SenderID,
                # "PalletID":self.Events.get('payload').get('palletId'),
                # "Drawing":self.Events.get('payload').get('Recipe'),
                # self.Events.get('payload').get('PenColor'),
                # dump_datetime(self.timestamp)
       return {
           
           'SenderID': self.id,
           # This is an example how to deal with Many2Many relations
           'event'  : self.Events,
           'timestamp' : dump_datetime(self.timestamp)
       }
    
    @hybrid_property
    def getEventAsCSV(self):
       """Return object data in easily serializable format"""
       return [ self.SenderID,self.Events.get('id'),
                self.Events.get('payload').get('Recipe'),
                self.Events.get('payload').get('PenColor'),
                self.Events.get('payload').get('palletId'),
                dump_datetime(self.timestamp)]


class WorkstationCapabilities(db.Model):
    __tablename__ = 'WorkstationCapabilities'
    id = db.Column(db.Integer, primary_key=True)
    ReferancePolicy= db.Column(db.JSON, nullable=True)
    FixedColorPolicy= db.Column(db.JSON, nullable=True)
    FixedColorRecipePolicy= db.Column(db.JSON, nullable=True)
    Error= db.Column(db.JSON, nullable=True)
    #relations
    #StationCapability= db.relationship('WorkstationInfo',backref='capability',lazy=True)#,uselist=False
# only for PR
class Orders(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    FrameType = db.Column(db.String(10),nullable=True)
    FrameColor = db.Column(db.String(10),nullable=True)
    ScreenType = db.Column(db.String(10),nullable=True)
    ScreenColor = db.Column(db.String(10),nullable=True)
    KeypadType = db.Column(db.String(10),nullable=True)
    KeypadColor = db.Column(db.String(10),nullable=True)
    Quantity = db.Column(db.Integer,)
    ProdPolicy = db.Column(db.Integer,nullable=True, default=None)
    OrderStatus = db.Column(db.Boolean)
    IsFetched = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    db.relationship('FinishedComponents',backref='components',lazy=True)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationInfo.id'),nullable=False)
    def __repr__(self):
        return f'Order({(self.id,dump_datetime(self.timestamp),self.Quantity),self.OrderStatus,self.IsFetched})'

    @property
    def getOrder(self):
       """Return object data in easily serializable format"""
       return ( {"LotNumber":self.id,'timestamp' : dump_datetime(self.timestamp),'Quantity':self.Quantity,
                    "Prodpolicy":self.ProdPolicy},
                {"Frame_Specs":[self.FrameType,self.FrameColor]},
                {"Screen_Specs":[self.ScreenType,self.ScreenColor]},
                {"Keypad_Specs":[self.KeypadType,self.KeypadColor]})

# only for demo
class CompletedComponents(db.Model):
    __tablename__ = 'CompletedComponents'
    id = db.Column(db.Integer, primary_key=True)
    Component = db.Column(db.String(10),nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Fkey = db.Column(db.Integer, db.ForeignKey('workstationInfo.id'),nullable=False)
    def __repr__(self):
        return f"Workstation('{self.WorkCellID}')"


class PalletObjects(db.Model):
    __tablename__ = 'PalletObjects'
    id = db.Column(db.Integer, primary_key=True)
    LotNumber = db.Column(db.Integer,nullable=True)
    PalletID = db.Column(db.String(255),nullable=True,unique=True)
    FrameType = db.Column(db.String(10),nullable=True)
    FrameColor = db.Column(db.String(10),nullable=True)
    ScreenType = db.Column(db.String(10),nullable=True)
    ScreenColor = db.Column(db.String(10),nullable=True)
    KeypadType = db.Column(db.String(10),nullable=True)
    KeypadColor = db.Column(db.String(10),nullable=True)
    Status = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, nullable=True, default=datetime.now)
    
    
    @hybrid_property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'LotNumber': self.LotNumber,
           'PalletID': f"{self.PalletID}",
           'Frame'  : {"type":self.FrameType, "color":self.FrameColor},
           'Screen'  : {"type":self.ScreenType, "color":self.ScreenColor},
           'Keypad'  : {"type":self.KeypadType, "color":self.KeypadColor},
           'status' :self.Status,
           'timestamp' : dump_datetime(self.timestamp)
       }

class AuthResult(db.Model):
    __tablename__ = 'AuthResult'
    id = db.Column(db.Integer, primary_key=True)
    Authenticated = db.Column(db.Boolean)  
    Description = db.Column(db.String(50),nullable=True)
    DetectedFaces = db.Column(db.Boolean) 
    DistanceScore = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=True, default=datetime.now)

class Emotion(db.Model):
    __tablename__ = 'Emotion'
    id = db.Column(db.Integer, primary_key=True)
    StressLevel = db.Column(db.Integer)
    Description = db.Column(db.String(50),nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True, default=datetime.now)