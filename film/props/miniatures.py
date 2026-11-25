"""Architectural models, workshop objects and keepsakes."""
import math
from .shapes import Model, PAINT


def cable_car():
    m=Model()
    m.base(.92,.45,.06,'steel')
    for x in (-.28,.28):
        for y in (-.16,.16):m.disc(x,y,.125,.14,.075,'ink')
    m.box(0,0,.25,.79,.39,.18)
    for x in (-.34,-.11,.11,.34):
        for y in (-.17,.17):m.box(x,y,.49,.034,.035,.32,'brown')
    for y in (-.16,.16):m.box(0,y,.38,.72,.044,.046,'gold')
    m.box(0,0,.67,.89,.48,.09,'cream')
    m.rod((-.18,0,.71),(.17,0,.87),.032,'steel')
    m.box(.15,0,.87,.27,.035,.037,'charcoal')
    return m


def truss_bridge():
    m=Model()
    for x in (-.44,.44):m.box(x,0,.125,.18,.46,.25,'steel')
    m.box(0,0,.27,1.12,.42,.08,'brown')
    for y in (-.205,.205):
        m.rod((-.49,y,.30),(.49,y,.30),.04,PAINT)
        m.rod((-.26,y,.60),(.26,y,.60),.048,PAINT)
        for x1,z1,x2,z2 in [(-.49,.30,-.26,.60),(-.26,.60,0,.30),(0,.30,.26,.60),(.26,.60,.49,.30)]:
            m.rod((x1,y,z1),(x2,y,z2),.041,PAINT)
    for x in (-.26,.26):m.rod((x,-.205,.60),(x,.205,.60),.034,'gold')
    return m


def water_tower():
    m=Model()
    for x in (-.23,.23):
        for y in (-.17,.17):
            m.rod((x,y,.029),(x*.72,y*.72,.55),.058,'brown')
            m.box(x,y,.025,.11,.10,.05,'steel')
    for x in (-.23,.23):m.rod((x,-.17,.07),(-x*.8,-.135,.43),.027,'gold')
    m.drum(0,0,.66,.52,.43,PAINT)
    for z in (.48,.62,.84):m.drum(0,0,z,.54,.028,'charcoal')
    m.cone(0,0,.95,.61,.20,'rust')
    return m


def signal_gantry():
    m=Model()
    for x in (-.42,.42):
        m.box(x,0,.044,.22,.34,.088,'charcoal')
        m.box(x,0,.45,.066,.10,.79,'steel')
    m.box(0,0,.82,.92,.13,.083,PAINT)
    for x in (-.21,.21):
        m.box(x,-.019,.65,.17,.095,.32,'ink')
        for i,c in enumerate(['mint','gold','red']):
            m.disc(x,-.081,.55+i*.096,.068,.036,c)
    for i in range(5):m.box(.34,-.006,.19+i*.106,.14,.047,.028,'gold')
    m.rod((.27,0,.13),(.27,0,.71),.025,'steel')
    return m


def parcel_cart():
    m=Model()
    for x in (-.32,.32):
        for y in (-.18,.18):
            m.disc(x,y,.11,.22,.075,'ink')
            m.disc(x,y+(.044 if y>0 else -.044),.11,.082,.023,'steel')
    m.box(0,0,.24,.83,.45,.076,PAINT)
    for y in (-.17,.17):m.rod((-.37,y,.27),(-.48,y,.71),.045,'steel')
    m.rod((-.48,-.17,.71),(-.48,.17,.71),.055,'brown')
    for x,z,w,h,c in [(-.11,.39,.36,.22,'brown'),(.21,.38,.21,.20,'cream'),(-.13,.57,.29,.14,'rust')]:
        m.box(x,0,z,w,.29,h,c)
        m.box(x,0,z,.045,.30,h+.009,'gold')
    return m


def diving_helmet():
    m=Model()
    m.piece('cylinder',0,0,.075,.70,.49,.15,'brown')
    m.drum(0,0,.185,.49,.10,'gold')
    m.ball(0,0,.51,.59,.53,.58,PAINT)
    m.disc(0,-.232,.54,.36,.10,'gold')
    m.disc(0,-.294,.54,.26,.036,'ink')
    for x in (-.071,0,.071):
        m.box(x,-.32,.54,.013,.017,.20,'steel')
    m.box(0,-.324,.54,.22,.02,.014,'steel')
    for x in (-.27,.27):
        m.drum(x,0,.53,.22,.09,'gold',(0,90,0))
    m.rod((.13,.08,.74),(.20,.10,.82),.072,'steel')
    return m


def treasure_chest():
    m=Model()
    m.box(0,0,.21,.81,.48,.42,PAINT)
    m.piece('cylinder',0,0,.43,.48,.46,.80,PAINT,(0,90,0))
    for x in (-.27,.27):
        m.box(x,0,.212,.062,.49,.423,'gold')
        m.piece('cylinder',x,0,.43,.49,.47,.067,'gold',(0,90,0))
    m.box(0,-.25,.36,.15,.035,.19,'gold')
    m.disc(0,-.276,.37,.049,.019,'ink')
    for x in (-.36,.36):
        for z in (.09,.30):m.disc(x,-.249,z,.043,.02,'steel')
    return m


def folding_easel():
    m=Model()
    for x in (-.29,.29):m.rod((x,-.15,.022),(x*.43,.065,.91),.048,'brown')
    m.rod((0,.25,.023),(0,.045,.86),.049,'brown')
    m.box(0,-.08,.54,.52,.052,.50,'cream',(-10,0,0))
    m.box(0,-.15,.315,.64,.14,.054,'gold')
    m.box(0,-.03,.83,.14,.09,.062,'charcoal')
    m.disc(-.095,-.12,.65,.097,.023,'gold')
    m.box(.06,-.118,.55,.20,.025,.052,PAINT,(0,-16,0))
    return m


def stone_gateway():
    m=Model()
    m.base(.95,.37,.065,'steel')
    for s in (-1,1):
        for i in range(4):
            m.box(s*.33,0,.147+i*.148,.22+(i%2)*.018,.26,.14,'cream' if i%2 else 'steel')
        m.box(s*.33,0,.63,.28,.30,.072,PAINT)
    # Radial masonry pieces frame a real opening.
    for i in range(9):
        a=i*math.pi/8
        m.box(.33*math.cos(a),0,.66+.33*math.sin(a),.19,.28,.142,
              'gold' if i==4 else 'cream',(0,-math.degrees(a),0))
    return m


def well_and_winch():
    m=Model()
    for i in range(12):
        a=i*math.tau/12
        m.box(.237*math.cos(a),.237*math.sin(a),.18,.108,.14,.36,'steel' if i%3 else 'cream',(0,0,math.degrees(a)))
    for x in (-.27,.27):m.box(x,0,.58,.064,.079,.50,'brown')
    for s in (-1,1):m.box(s*.17,0,.90,.40,.42,.057,PAINT,(0,s*23,0))
    m.drum(0,0,.68,.105,.53,'gold',(0,90,0))
    m.rod((.09,-.045,.68),(.09,-.045,.38),.016,'brown')
    m.drum(.09,-.045,.36,.12,.11,'charcoal')
    return m


def rocking_horse():
    m=Model()
    for y in (-.13,.13):
        for x1,z1,x2,z2 in [(-.44,.11,-.26,.043),(-.26,.043,.26,.043),(.26,.043,.44,.11)]:
            m.rod((x1,y,z1),(x2,y,z2),.071,'brown')
        for x in (-.22,.22):m.rod((x,y,.07),(x*.73,y,.40),.057,'brown')
    m.ball(0,0,.44,.54,.29,.30,PAINT)
    m.box(.23,0,.57,.15,.19,.30,'brown',(0,19,0))
    m.box(.31,0,.72,.25,.18,.14,'brown',(0,10,0))
    m.cone(.26,.03,.82,.079,.13,'brown')
    m.disc(.31,-.095,.74,.041,.019,'ink')
    m.ball(-.22,.01,.46,.17,.14,.16,'cream')
    m.box(-.02,0,.595,.21,.24,.045,'rust')
    return m


def model_sailboat():
    m=Model()
    m.base(.51,.32,.067,'brown')
    for x in (-.15,.15):m.box(x,0,.13,.06,.18,.14,'gold')
    m.ball(0,0,.25,.96,.34,.23,PAINT)
    m.box(0,0,.315,.71,.24,.057,'cream')
    m.rod((0,0,.34),(0,0,1.09),.034,'brown')
    m.rod((-.36,0,.43),(.01,0,.43),.037,'brown')
    # Triangular cut sails have a broad unbroken plane at oblique angles.
    m.piece('sail',-.19,0,.73,.35,.026,.56,'ivory')
    m.piece('sail',.145,.021,.65,.26,.024,.44,'gold',(0,0,180))
    m.rod((.39,0,.32),(.012,0,1.03),.013,'steel')
    return m


def desk_harp():
    m=Model()
    m.base(.63,.36,.10,'brown')
    m.rod((-.24,0,.14),(.22,0,.84),.088,PAINT)
    m.rod((-.25,0,.14),(-.25,0,.94),.059,'gold')
    m.rod((-.25,0,.94),(-.04,0,.85),.065,'brown')
    m.rod((-.04,0,.85),(.22,0,.86),.064,'brown')
    for i in range(7):
        x=-.202+i*.058
        low=.14+(x+.24)*1.52
        high=.85+max(0,-.04-x)*.43
        m.rod((x,-.013,low),(x,-.013,high),.018,'cream')
    return m


def camping_stove():
    m=Model()
    m.drum(0,0,.068,.45,.135,'ink')
    m.ball(0,0,.25,.48,.46,.41,PAINT)
    m.drum(0,0,.455,.13,.13,'gold')
    m.drum(0,0,.54,.32,.065,'charcoal')
    for i in range(4):
        a=i*math.pi/2
        dx,dy=math.cos(a),math.sin(a)
        m.rod((.09*dx,.09*dy,.47),(.24*dx,.24*dy,.64),.033,'steel')
        m.rod((.24*dx,.24*dy,.64),(.14*dx,.14*dy,.64),.039,'steel')
    m.disc(0,-.22,.32,.11,.07,'rust')
    return m


def bonsai_planter():
    m=Model()
    for x in (-.23,.23):m.box(x,0,.037,.10,.23,.074,'brown')
    m.box(0,0,.15,.68,.41,.16)
    m.box(0,0,.235,.72,.45,.057,PAINT)
    m.box(0,0,.268,.61,.35,.019,'brown')
    m.rod((.05,0,.27),(-.065,0,.52),.087,'brown')
    m.rod((-.065,0,.52),(.12,0,.72),.065,'brown')
    m.rod((-.055,0,.51),(-.28,.02,.62),.041,'brown')
    m.rod((.06,0,.66),(.27,.045,.70),.035,'brown')
    for x,y,z,w in [(-.25,0,.66,.30),(.23,.035,.74,.26),(.07,.01,.83,.36),(-.07,-.05,.76,.24)]:
        m.ball(x,y,z,w,w*.64,w*.48,'teal' if z<.76 else 'mint')
    return m


def ceramic_teapot():
    m=Model()
    m.drum(0,0,.058,.32,.115,'brown')
    m.ball(0,0,.31,.53,.44,.48,PAINT)
    m.drum(0,0,.53,.32,.060,'cream')
    m.ball(0,0,.59,.11,.11,.095,'gold')
    m.ring(-.28,0,.34,.30,.066,'gold')
    m.rod((.20,0,.27),(.34,0,.36),.119,PAINT)
    m.rod((.34,0,.36),(.41,0,.51),.087,PAINT)
    m.drum(.42,0,.525,.095,.032,'cream',(0,25,0))
    return m


MODELS = [cable_car, truss_bridge, water_tower, signal_gantry, parcel_cart, diving_helmet,
          treasure_chest, folding_easel, stone_gateway, well_and_winch, rocking_horse,
          model_sailboat, desk_harp, camping_stove, bonsai_planter, ceramic_teapot]
