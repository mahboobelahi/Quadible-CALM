import threading
from flask import flash, request,render_template
from FASToryLine import app
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

@app.route('/about')
def about():
        return render_template("orchestrator/about.html",title="About")

@app.route('/workstations',methods=['GET'])
def workstations():

        print('[X-Routes]Request Came from: ',request.url)
        workstations = DataBase.WorkstationInfo.query.all()
        return render_template('orchestrator/workCell.html',title='Worksations',content=workstations)

if __name__ == '__main__':
        
    strat_workstations=threading.Timer(2,HF.instencateWorkstations)
    strat_workstations.daemon=True
    strat_workstations.start()

    HF.createModels()

    app.run(host=CONFIG.orchestrator_IP, port=CONFIG.orchestrator_Port,debug=False) #,debug=True