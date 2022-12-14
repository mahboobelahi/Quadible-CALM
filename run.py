import requests,threading,time,json
from sqlalchemy import exc
from flask import Flask, flash, request,render_template,redirect,url_for
from FASToryLine import app, db
from FASToryLine import dbModels as DataBase
from FASToryLine import configurations as CONFIG
from FASToryLine import helperFunctions as HF

#welcom and about page
@app.route('/')
@app.route('/welcome')
def welcome():
    #WS_obj_list = HF.WS_instance(num_of_objs)  # contains instances of workstations

        flash('Welcome to FASTory Line Orchestrator!')
        return render_template("orchestrator/welcom.html",title="Home")

@app.route('/about-productionPolicies')
def AboutPolicies():
        
    return render_template("orchestrator/productionPolicies.html",title="ProductionPolicies")

@app.route('/about')
def about():
        return render_template("orchestrator/about.html",title="About")

#####################information##################
@app.route('/workstations',methods=['GET'])
def workstations():

        print('[X-Routes]Request Came from: ',request.url)
        workstations = DataBase.WorkstationInfo.query.all()
        return render_template('orchestrator/workCell.html',title='Worksations',content=workstations)

######################subscriptions######################

#Event Subscriptions and UnSubscriptions
@app.route('/eventSubscriptions')
def eventSubscription():
    try:
        
        # [getEventURLs(res) for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
        # URLs= [DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).filter_by(Fkey=t.WorkCellID).all() for t in test]
        #[getEventURLs(res) for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
        #Too much crazy query
        #URLs= [DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).filter_by(Fkey=res.WorkCellID).all()  for res in DataBase.WorkstationInfo.query.all() if (res.WorkCellID not in [1,7] and "ERROR" not in res.getCapabilities)]
        #URLs= DataBase.S1000Subscriptions.query.with_entities(DataBase.S1000Subscriptions.Event_url,DataBase.S1000Subscriptions.Destination_url).all()
        # a better choice
        filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        for url in filteredURLS:
            #print(f"[X-ORC] {url}")
            list(map(HF.subEvents, url))
            
        
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

    #flash('You have successfully subscribed to the events on FASTory simulator')
    return render_template("orchestrator/welcom.html",title="Home")

#Event UnSubscriptions and UnSubscriptions
@app.route('/eventUnSubscriptions')
def eventUnSubscription():
    try:
        filteredURLS= [DataBase.S1000Subscriptions.query.filter_by(Fkey=res.WorkCellID).all() for res in DataBase.WorkstationInfo.query.all() if( res.WorkCellID not in [1,7]and "ERROR" not in res.getCapabilities)]
        for url in filteredURLS:
            #print(f"[X-ORC] {url}")
            list(map(HF.UnSubEvents, url))       
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')

    #flash('You have successfully unsubscribed events on FASTory simulator')
    return render_template("orchestrator/welcom.html",title="Home")

############Production##################

# Order placement
@app.route('/placeorder', methods=['POST', 'GET'])
def order():
    if request.method == 'POST':
        print(f'[XT] Data from order fourm: {request.form}')
        ReceivedOrder = DataBase.Orders(
                                FrameType = request.form['FrameType'],
                                FrameColor = request.form['FrameColor'],
                                ScreenType = request.form['ScreenType'],
                                ScreenColor = request.form['ScreenColor'],
                                KeypadType = request.form['KeypadType'],
                                KeypadColor = request.form['KeypadColor'],
                                Quantity = request.form['quantity'],
                                OrderStatus = False,
                                IsFetched = False,
                                Fkey=7
                                )
        try:
            db.session.add(ReceivedOrder)
            db.session.commit()
            print(f'[X] app2: {ReceivedOrder}')
            print('app3:_request: ',request,'\n')
            flash('Your order has been placed successfully')
            return render_template("orchestrator/order.html",title="Orders")         
        except exc.SQLAlchemyError as e:
            print(f'[XE] {e}')
            flash(f'Ops! {str(e)}')
            return render_template("orchestrator/order.html",title="Orders")
    else:
        return render_template("orchestrator/order.html",title="Orders")

#policy based workstation instentiation
@app.route('/production-policy', methods=['POST'])
def ProductionPolicy():
    policyID = int(request.form.get("productionPolicy"))
    if policyID:
        updateEorkstationCapability=threading.Thread(target=HF.updateCapability,args=(policyID,))
        updateEorkstationCapability.daemon=True
        updateEorkstationCapability.start()
    flash("Orchestrator initializing FASTory Line...")
    res = requests.post('http://192.168.100.100:2009/startProduction')
    print(f'[X] {res.status_code}.????{res.reason}')
    return  redirect(url_for('welcome'))

###########Product tracking####################
#Production Lot Status
@app.route('/productionLot',methods=['GET','POST','DELETE'])
def fetchProductionLot():
    try:
        if request.method == 'POST':
            print(f'[XT] Data from order fourm: {request.form["id"]}')
            DataBase.Orders.query.filter_by(id=request.form['id']).delete()
            db.session.commit()

        result= DataBase.Orders.query.all()
        return render_template("orchestrator/productionLotStatus.html", title="Lot-Status",ProductionLot=result)
    except ValueError as e:
        flash(f'Invalid JSON:{str(e)}')
        return render_template("orchestrator/productionLotStatus.html", title="Lot-Status",ProductionLot=result)
    except exc.SQLAlchemyError as e:
        flash(f'Ops! {str(e)}')
        return render_template("orchestrator/productionLotStatus.html", title="Lot-Status",ProductionLot=result)

#Individual Order Status
@app.route('/palletObj',methods=['GET','POST','DELETE'])
def fetchPalletObj():
    
    try:
        if request.method == 'POST':
            
            print(f'[XT] Data from order fourm: {request.form}')
            DataBase.PalletObjects.query.filter_by(PalletID=request.form['palletRFIDtag']).delete()
            db.session.commit()
    
        result= DataBase.PalletObjects.query.all()
        if result:
            Pallet_obj = [res.serialize for res in result]
            print(result[0].serialize)
            return render_template("orchestrator/palletObject.html", Pallet_obj=Pallet_obj,title="Order-Status")
        else:
            return render_template("orchestrator/palletObject.html", Pallet_obj=None,title="Order-Status")
    except ValueError as e:
        flash(f'Invalid JSON:{str(e)}')
        return render_template("orchestrator/palletObject.html", Pallet_obj=Pallet_obj,title="Order-Status")
    except exc.SQLAlchemyError as e:
        flash(f'Ops! {str(e)}')
        return render_template("orchestrator/palletObject.html", Pallet_obj=Pallet_obj,title="Order-Status")
#Individual Order Status
@app.route('/updateCapability',methods=['GET'])
def updatecapability():
    print(f'[XT] Data from order fourm: {request.form}')
    return render_template("orchestrator/updateCapabilities.html",title="Capability",err=False)


@app.route('/api-updateCapability',methods=['POST'])
def ApiUpdateCapability():
    print(f'[XT] Data from order fourm: {request.form}')
    try:
        data = json.loads(request.form["data"])
        result = DataBase.WorkstationInfo.query.filter_by(WorkCellID= data.get("id")).first()
        result.Capabilities = data.get("capabilities")
        print(result)
        flash(f'Capability updated for workstation_{result.WorkCellID}')
        db.session.commit()
        stratPolicyBasedToolChange=threading.Thread(target=HF.policyBasedToolChanging,args=(result.WorkCellID,))
        stratPolicyBasedToolChange.daemon=True
        stratPolicyBasedToolChange.start()
        return render_template("orchestrator/capError.html",title="Capability",err=False)
    except ValueError as e:
        flash(f'Invalid JSON:{str(e)}')
        return render_template("orchestrator/capError.html",title="Capability",err=True)
    except exc.SQLAlchemyError as e:
        flash(f'Ops! {str(e)}')
        return render_template("orchestrator/capError.html",title="Capability",err=True)


# testing route

if __name__ == '__main__':
        
    strat_workstations=threading.Timer(2,HF.instencateWorkstations)
    strat_workstations.daemon=True
    strat_workstations.start()
    
    
    HF.createModels()
    app.run(host=CONFIG.orchestrator_IP, port=CONFIG.orchestrator_Port,debug=False) #,debug=True