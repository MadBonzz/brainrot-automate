"""Mechanical clues with large readable controls and contrasting trim."""
import math
from .shapes import Model, PAINT


def gramophone():
    m=Model()
    m.base(.78,.52,.22,PAINT)
    m.drum(-.10,-.04,.25,.44,.055,'ink')
    m.drum(-.10,-.04,.28,.13,.02,'rust')
    m.rod((.25,.14,.23),(.28,.13,.55),.055,'gold')
    m.rod((.28,.13,.55),(.12,.06,.64),.09,'gold')
    m.along('horn',(.12,.06,.64),(-.21,-.17,.87),.49,'gold')
    m.rod((.21,-.08,.26),(.01,-.12,.32),.026,'steel')
    return m


def film_projector():
    m=Model()
    m.base(.84,.46,.11)
    m.box(0,0,.42,.68,.34,.47)
    m.rod((.29,0,.46),(.52,0,.46),.22,'ink')
    m.rod((.50,0,.46),(.55,0,.46),.25,'gold')
    for x in (-.23,.20):
        m.disc(x,0,.86,.43,.13,'steel')
        m.disc(x,-.081,.86,.085,.035,'gold')
        for i in range(5):
            a=i*math.tau/5
            m.disc(x+.13*math.sin(a),-.076,.86+.13*math.cos(a),.082,.022,'ink')
    m.rod((-.34,-.06,.73),(-.18,-.06,.56),.027,'brown')
    for i in range(4):
        for y in (-.18,.18):m.box(-.20+i*.075,y,.38,.036,.023,.14,'charcoal')
    return m


def cassette_deck():
    m=Model()
    m.base(.99,.41,.10,'ink')
    m.box(0,0,.36,.95,.36,.50)
    m.box(-.11,-.191,.41,.61,.031,.29,'charcoal')
    m.box(-.11,-.214,.42,.49,.026,.17,'cream')
    for x in (-.25,.03):
        m.disc(x,-.24,.43,.115,.035,'ink')
        m.disc(x,-.261,.43,.045,.016,'gold')
    for i in range(5):m.box(-.35+i*.118,-.209,.19,.084,.047,.054,'red' if i==4 else 'steel')
    for i in range(5):
        m.box(.34,-.192,.27+i*.055,.13,.032,.019,'charcoal')
        m.box(.24,.184,.28+i*.045,.22,.017,.017,'charcoal')
    m.box(-.20,.185,.31,.38,.023,.20,'charcoal')
    return m


def typewriter():
    m=Model()
    m.base(.90,.56,.12,'charcoal')
    m.box(0,-.015,.23,.87,.43,.23)
    m.box(0,.105,.41,.81,.22,.25)
    m.drum(0,.09,.54,.117,.86,'ink',(0,90,0))
    m.box(0,.135,.68,.57,.028,.32,'cream',(-7,0,0))
    for i in range(3):m.box(-.06,.115,.63+i*.052,.33-.04*i,.012,.012,'steel')
    for row in range(3):
        for col in range(7):
            m.drum((col-3)*.093+row*.009,-.196+row*.065,.352+row*.022,.057,.042,'ivory')
    m.box(0,-.249,.33,.38,.043,.033,'ink')
    for x in (-.455,.455):m.drum(x,.09,.54,.14,.06,'gold',(0,90,0))
    return m


def rotary_telephone():
    m=Model()
    m.base(.78,.53,.13,'ink')
    m.box(0,0,.265,.73,.42,.27)
    m.disc(0,-.223,.28,.31,.04,'gold')
    for i in range(9):
        a=i*math.tau/10
        m.disc(.112*math.sin(a),-.25,.28+.112*math.cos(a),.042,.018,'ink')
    for x in (-.25,.25):
        m.box(x,.01,.455,.09,.14,.15,'charcoal')
        m.ball(x,0,.53,.20,.20,.16,'ink')
    m.rod((-.24,0,.55),(.24,0,.55),.089,'ink')
    for i in range(5):m.ring(.31+i*.021,-.018,.44-i*.041,.086,.025,'charcoal')
    return m


def twin_bell_alarm():
    m=Model()
    for s in (-1,1):
        m.rod((s*.22,0,.031),(s*.16,0,.21),.067,'gold')
        m.ball(s*.22,0,.028,.09,.11,.056,'ink')
    m.disc(0,0,.50,.63,.26,PAINT)
    m.dial(0,-.147,.50,.56)
    for s in (-1,1):
        m.rod((s*.14,0,.72),(s*.24,0,.86),.04,'steel')
        m.ball(s*.24,0,.86,.28,.25,.15,'gold')
    m.rod((-.18,0,.83),(.18,0,.83),.025,'ink')
    m.box(-.05,-.232,.53,.126,.02,.025,'rust',(0,22,0))
    m.axle(0,-.24,.50,'y')
    m.box(0,-.24,.60,.027,.022,.20,'ink')
    return m


def bellows_camera():
    m=Model()
    m.base(.78,.60,.08,'brown')
    m.box(0,.13,.12,.60,.16,.09,'brown')
    m.box(0,.14,.41,.63,.14,.55,'brown')
    m.box(0,-.25,.16,.16,.11,.18,'brown')
    for i in range(5):
        size=.50-i*.025
        m.box(0,.055-i*.07,.43,size,.06,size,'ink' if i%2==0 else 'charcoal')
    m.box(0,-.265,.43,.40,.069,.39,PAINT)
    m.disc(0,-.326,.44,.29,.10,'gold')
    m.disc(0,-.387,.44,.21,.034,'ink')
    m.disc(0,-.407,.44,.12,.014,'blue')
    m.box(.22,.14,.74,.135,.13,.11,'ink')
    return m


def tabletop_jukebox():
    m=Model()
    m.base(.74,.38,.10,'charcoal')
    m.box(0,0,.44,.64,.34,.68)
    m.disc(0,0,.74,.65,.34,PAINT)
    m.ring(0,-.185,.73,.50,.045,'gold')
    m.disc(0,-.171,.75,.38,.033,'ink')
    m.disc(0,-.197,.75,.13,.021,'rust')
    for s in (-1,1):m.box(s*.256,-.19,.41,.035,.039,.53,'gold')
    for i in range(5):
        m.box(0,-.19,.22+i*.064,.32,.03,.023,'cream')
        m.box(0,.177,.33+i*.048,.37,.022,.018,'charcoal')
    return m


def sewing_machine():
    m=Model()
    m.base(.94,.46,.115)
    m.box(.30,0,.38,.21,.30,.53)
    m.box(.03,0,.63,.72,.31,.17)
    m.box(-.25,0,.55,.16,.25,.25)
    m.rod((-.25,-.034,.51),(-.25,-.034,.19),.026,'steel')
    m.box(-.25,-.055,.17,.14,.12,.034,'steel')
    m.drum(.06,0,.78,.119,.15,'rust')
    m.disc(.28,-.165,.38,.11,.035,'gold')
    m.axle(.45,0,.60,'x')
    m.ring(.45,0,.60,.35,.055,'gold',(0,90,0))
    for a in (0,60,120):
        m.box(.45,0,.60,.042,.033,.29,'steel',(a,0,0))
    return m


def screw_press():
    m=Model()
    m.base(.81,.49,.11)
    for x in (-.31,.31):m.box(x,0,.49,.09,.15,.77,PAINT)
    m.box(0,0,.84,.73,.18,.12,PAINT)
    m.box(0,0,.21,.53,.36,.09,'brown')
    m.box(0,0,.45,.53,.36,.087,'steel')
    m.drum(0,0,.68,.067,.42,'charcoal')
    for i in range(6):m.drum(0,0,.52+i*.056,.09,.018,'gold')
    m.drum(0,0,.94,.062,.11,'steel')
    m.axle(0,0,.99,'z')
    m.rod((-.28,0,.99),(.28,0,.99),.04,'steel')
    for x in (-.29,.29):m.ball(x,0,.99,.08,.08,.08,'brown')
    return m


def tabletop_fan():
    m=Model()
    m.base(.55,.40,.09,PAINT)
    m.rod((0,.05,.09),(0,.05,.58),.10,'gold')
    m.disc(0,.05,.68,.22,.22,'ink')
    for d in (.75,.61):m.ring(0,-.11,.69,d,.024,'steel')
    for i in range(8):
        a=i*math.tau/8
        m.rod((0,-.13,.69),(.353*math.sin(a),-.105,.69+.353*math.cos(a)),.013,'steel')
    m.axle(0,-.04,.69,'y')
    for i in range(3):
        a=i*math.tau/3
        m.box(.168*math.sin(a),-.046,.69+.168*math.cos(a),.12,.035,.29,'mint',(0,math.degrees(a)+14,0))
    m.disc(0,-.075,.69,.13,.07,'gold')
    return m


def beacon_tower():
    m=Model()
    m.drum(0,0,.075,.55,.15,'charcoal')
    m.cone(0,0,.43,.45,.70,'cream')
    m.drum(0,0,.40,.34,.13,'rust')
    m.drum(0,0,.68,.46,.079,'charcoal')
    for x in (-.13,.13):
        for y in (-.10,.10):m.box(x,y,.81,.032,.032,.20,'gold')
    m.cone(0,0,.98,.45,.16,PAINT)
    m.axle(0,0,.81,'z')
    m.disc(0,0,.81,.14,.18,'gold')
    m.disc(0,-.10,.81,.114,.027,'mint')
    return m


def coffee_grinder():
    m=Model()
    m.base(.58,.50,.10,'charcoal')
    m.box(0,0,.29,.53,.45,.38,'brown')
    m.box(0,-.238,.26,.40,.029,.20,PAINT)
    m.ball(0,-.27,.25,.075,.065,.075,'gold')
    m.cone(0,0,.59,.44,.25,'gold',(180,0,0))
    m.drum(0,0,.724,.45,.036,'brown')
    m.axle(0,0,.74,'z')
    m.drum(0,0,.77,.052,.095,'steel')
    m.rod((0,0,.81),(.25,0,.86),.035,'steel')
    m.ball(.25,0,.89,.095,.095,.12,'brown')
    return m


def combination_safe():
    m=Model()
    m.base(.76,.55,.08,'ink')
    m.box(0,0,.415,.72,.50,.67)
    m.box(0,-.265,.425,.58,.055,.53,'charcoal')
    for z in (.26,.59):m.box(-.295,-.288,z,.065,.06,.095,'steel')
    m.dial(.045,-.30,.47,.28)
    m.rod((-.02,-.32,.25),(.15,-.32,.25),.037,'gold')
    m.axle(.045,-.38,.47,'y')
    m.disc(.045,-.38,.47,.12,.055,'ink')
    m.box(.045,-.415,.50,.019,.015,.055,'ivory')
    return m


def pinwheel_box():
    m=Model()
    m.base(.51,.40,.17,'brown')
    m.rod((0,.035,.17),(0,.035,.74),.047,'gold')
    m.axle(0,-.03,.74,'y')
    for i,c in enumerate([PAINT,'gold','mint','rust']):
        a=i*math.pi/2
        x,z=.151*math.sin(a),.74+.151*math.cos(a)
        m.box(x,-.015,z,.164,.039,.295,'cream',(0,i*90+22,0))
        m.box(x,-.035,z,.145,.042,.28,c,(0,i*90+22,0))
    m.disc(0,-.075,.74,.093,.055,'gold')
    return m


def railway_semaphore():
    m=Model()
    m.base(.45,.37,.10,'charcoal')
    m.box(0,.03,.59,.095,.105,.98,'cream')
    m.box(0,0,.123,.24,.21,.056,PAINT)
    for i in range(4):m.box(0,-.033,.30+i*.16,.098,.022,.04,'rust')
    m.disc(0,-.055,.89,.20,.09,'ink')
    m.axle(0,-.12,.89,'y')
    m.box(.17,-.12,.89,.44,.05,.093,'red')
    m.box(.30,-.154,.89,.05,.018,.095,'cream')
    m.disc(-.061,-.15,.89,.10,.034,'mint')
    return m


def ferris_wheel():
    m=Model()
    m.base(.82,.48,.08)
    for y in (-.10,.10):
        for x in (-.28,.28):m.rod((x,y,.08),(0,y,.58),.044,'gold')
    m.axle(0,0,.58,'y')
    m.ring(0,0,.58,.77,.045,'steel')
    for i in range(8):
        a=i*math.tau/8
        x,z=.35*math.sin(a),.58+.35*math.cos(a)
        m.rod((0,0,.58),(x,0,z),.022,PAINT)
        # Rounded capsules keep their silhouette through the rotation.
        m.ball(x,0,z,.13,.16,.105,['red','mint','gold','blue'][i%4])
    m.disc(0,-.025,.58,.11,.09,'gold')
    return m


MODELS = [gramophone, film_projector, cassette_deck, typewriter, rotary_telephone, twin_bell_alarm,
          bellows_camera, tabletop_jukebox, sewing_machine, screw_press, tabletop_fan, beacon_tower,
          coffee_grinder, combination_safe, pinwheel_box, railway_semaphore, ferris_wheel]
