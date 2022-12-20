import requests,threading,json
from sqlalchemy import exc
from flask import flash, request,render_template,redirect,url_for
from FASToryLine import app, db
from FASToryLine import dbModels as DataBase
from FASToryLine import helperFunctions as HF



@app.route('/about-productionPolicies')
def AboutPolicies():    
    return render_template("orchestrator/productionPolicies.html",title="ProductionPolicies")


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
        pass
    flash("Orchestrator initializing FASTory Line...")
    res = requests.post('http://192.168.100.100:2009/startProduction')
    print(f'[X] {res.status_code}.????{res.reason}')
    return  redirect(url_for('welcome'))


@app.route('/updateCapability',methods=['POST'])
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
