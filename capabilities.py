from FASToryLine import db
from FASToryLine.dbModels import*
from sqlalchemy import exc

ReferancePolicy = [
    # Workstation 1
    ['LoadpPaper', 'UnLoadPaper'],
    # Workstation 2
    ['Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 3
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 4
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 5
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 6
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 7
    ['LoadPallet', 'UnLoadPallet'],
    # Workstation 8
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 9
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 10
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # Workstation 11
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9'],
    # general Workstation 12
    [ 'Draw1', 'Draw2', 'Draw3', 'Draw4',
     'Draw5', 'Draw6', 'Draw7', 'Draw8', 'Draw9']
]
#policy2-Fixed Color
FixedColorPolicy = [
    # Workstation 1
    ['LoadpPaper', 'UnLoadPaper'],
    # Workstation 2
    ['RED'],
    # Workstation 3
    [ 'GREEN'],
    # Workstation 4
    [ 'BLUE'],
    # Workstation 5
    [ 'GREEN'],
    # Workstation 6
    [ 'BLUE'],
    # Workstation 7
    ['LoadPallet', 'UnLoadPallet'],
    # Workstation 8
    [ 'RED'],
    # Workstation 9
    [ 'BLUE'],
    # Workstation 10
    [ 'RED'],
    # Workstation 11
    [ 'GREEN'],
    # general Workstation 12
    [ 'RED','BLUE','GREEN']
]
#policy3
FixedColorRecipePolicy = [
    #Workstation 1
    ['LoadpPaper','UnLoadPaper'],
    #frames Workstation 2
    ['RED','Draw1','Draw2','Draw3'],
    #screens Workstation 3
    ['GREEN','Draw4','Draw5','Draw6'],
    #keypads Workstation 4
    ['BLUE','Draw7','Draw8','Draw9'],
    ################################
    #frames Workstation 5
    ['GREEN','Draw1','Draw2','Draw3'],
    #screens Workstation 6
    ['BLUE','Draw4','Draw5','Draw6'],
    #Workstation 7
    ['LoadPallet','UnLoadPallet'],
    #keypads Workstation 8
    ['RED','Draw7','Draw8','Draw9'],
    ###############################
    #frames Workstation 9
    ['BLUE','Draw1','Draw2','Draw3'],
    #screens Workstation 10
    ['RED','Draw4','Draw5','Draw6'],
    #keypads Workstation 11
    ['GREEN','Draw7','Draw8','Draw9'],
    #general Workstation 12
    ['RED','GREEN','BLUE','Draw1','Draw2','Draw3','Draw4',
     'Draw5','Draw6','Draw7','Draw8','Draw9']
]
#Error
Error = [
    #Workstation 1
    ['LoadpPaper','UnLoadPaper'],
    #frames Workstation 2
    ['ERROR'],
    #screens Workstation 3
    ['ERROR'],
    #keypads Workstation 4
    ['ERROR'],
    ################################
    #frames Workstation 5
    ['ERROR'],
    #screens Workstation 6
    ['ERROR'],
    #Workstation 7
    ['LoadPallet','UnLoadPallet'],
    #keypads Workstation 8
    ['ERROR'],
    ###############################
    #frames Workstation 9
    ['ERROR'],
    #screens Workstation 10
    ['RED','Draw1','Draw2','Draw3'],
    #keypads Workstation 11
    ['GREEN','Draw4','Draw5','Draw6'],
    #general Workstation 12
    ['BLUE','Draw7','Draw8','Draw9']
]

for i in range(12):
    cap=WorkstationCapabilities(
                                ReferancePolicy=ReferancePolicy[i],
                                FixedColorPolicy=FixedColorPolicy[i],
                                FixedColorRecipePolicy=FixedColorRecipePolicy[i],
                                Error=Error[i]
                                )
    try:
        db.session.add(cap)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        print(f'[XE] {e}')