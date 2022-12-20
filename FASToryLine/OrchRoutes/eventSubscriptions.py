
from sqlalchemy import exc
from flask import flash,redirect,url_for
from FASToryLine import app
from FASToryLine import dbModels as DataBase
from FASToryLine import helperFunctions as HF
from FASToryLine.configurations import WS_obj_list

#[getEventURLs(res) for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
# URLs= [DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).filter_by(Fkey=t.WorkCellID).all() for t in test]
#[getEventURLs(res) for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
#Too much crazy query
#URLs= [DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).filter_by(Fkey=res.WorkCellID).all()  for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
#URLs= DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).all()
# a better choice
#filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID !=1)]


#Event Subscriptions and UnSubscriptions
@app.route('/eventSubscriptions')
def eventSubscription():
    
    try:
        cellIDs= [res.WorkCellID-1 for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        obj_list = [WS_obj_list[i] for i in cellIDs]
        HF.subscribeToFASToryEvents(obj_list,Unsub=False)
        
        #filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        #for url in filteredURLS:
            #print(f"[X-ORC] {url}")
            #list(map(HF.subEvents, url))
    
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')
    
    flash('You have successfully subscribed to FASTory Line events.')
    return redirect(url_for('welcome'))#render_template("orchestrator/welcom.html",title="Home")

@app.route('/eventUnSubscriptions')
def eventUnSubscription():
    try:
        cellIDs= [res.WorkCellID-1 for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        obj_list = [WS_obj_list[i] for i in cellIDs]
        HF.subscribeToFASToryEvents(obj_list)

        #filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID !=1)]
        # filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        # for url in filteredURLS:
        #     #print(f"[X-ORC] {url}")
        #     list(map(HF.UnSubEvents, url)) 
              
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

    flash('You have successfully unsubscribed FASTory Line events.')
    return redirect(url_for('welcome'))#render_template("orchestrator/welcom.html",title="Home")
