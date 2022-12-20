from sqlalchemy import exc
from flask import  flash, request,render_template
from FASToryLine import app, db
from FASToryLine import dbModels as DataBase

@app.route('/productionLot',methods=['GET','POST'])
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
@app.route('/palletObj',methods=['GET','POST'])
def fetchPalletObj():
    
    try:
        if request.method == 'POST':
            
            print(f'[XT] Data from order fourm: {request.form}')
            DataBase.PalletObjects.query.filter_by(PalletID=request.form['palletRFIDtag']).delete()
            db.session.commit()
    
        result= DataBase.PalletObjects.query.all()
        if result:
            Pallet_obj = [res.serialize for res in result]
            #print(result[0].serialize)
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
