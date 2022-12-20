from sqlalchemy import exc
from flask import jsonify
from FASToryLine import app, db
from FASToryLine import dbModels as DataBase
from FASToryLine import configurations as CONFIG
from FASToryLine import helperFunctions as HF
from pprint import pprint as P



# @app.route('/api-updateCapability',methods=['POST'])
# def ApiUpdateCapability():
#     print(f'[XT] Data from order fourm: {request.form}')
#     try:
#         data = json.loads(request.form["data"])
#         result = DataBase.WorkstationInfo.query.filter_by(WorkCellID= data.get("id")).first()
#         result.Capabilities = data.get("capabilities")
#         print(result)
#         flash(f'Capability updated for workstation_{result.WorkCellID}')
#         db.session.commit()
#         stratPolicyBasedToolChange=threading.Thread(target=HF.policyBasedToolChanging,args=(result.WorkCellID,))
#         stratPolicyBasedToolChange.daemon=True
#         stratPolicyBasedToolChange.start()
#         return render_template("orchestrator/capError.html",title="Capability",err=False)
#     except ValueError as e:
#         flash(f'Invalid JSON:{str(e)}')
#         return render_template("orchestrator/capError.html",title="Capability",err=True)
#     except exc.SQLAlchemyError as e:
#         flash(f'Ops! {str(e)}')
#         return render_template("orchestrator/capError.html",title="Capability",err=True)

@app.route('/api-deleteOrder/<id>', methods=['DELETE'])
def apiDeleteOrder(id):  
    try:
        result= DataBase.Orders.query.get_or_404(id)
        if result and not result.OrderStatus:
            db.session.delete(result)
            db.session.commit() 
            HF.getAndSetIsFetchOrders()   
            print('[X-API] ORDERS_: \n')
            P(CONFIG.ORDERS) 
            return jsonify(Response=200)
    except exc.SQLAlchemyError as e:
        print(f'[X-API] {e}')
        return jsonify(Response=e)
    return ''
