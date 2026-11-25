"""Optics, navigation and scientific instruments."""
import math
from .shapes import Model, PAINT


def balance_scale():
    m=Model()
    m.base(.62,.41,.10)
    m.cone(0,0,.19,.32,.20,'gold')
    m.rod((0,0,.20),(0,0,.92),.085,'gold')
    m.ball(0,0,.91,.14,.14,.14,'rust')
    m.rod((-.38,0,.84),(.38,0,.92),.05,'gold')
    for sign in (-1,1):
        x=sign*.355
        for dx,dy in [(-.115,.05),(.115,.05),(0,-.105)]:
            m.rod((x,0,.88+sign*.04),(x+dx,dy,.45+sign*.04),.017,'steel')
        m.ball(x,0,.43+sign*.04,.30,.28,.085,PAINT)
    return m


def bench_microscope():
    m=Model()
    m.base(.62,.53,.12,'charcoal')
    m.rod((.14,.09,.12),(.30,.10,.52),.15,PAINT)
    m.rod((.30,.10,.52),(.11,.10,.80),.16,PAINT)
    m.box(-.08,-.02,.37,.46,.33,.057,'ink')
    m.box(-.08,-.05,.408,.25,.12,.016,'mint')
    m.rod((-.17,-.01,.51),(.13,.03,.95),.17,'steel')
    m.rod((.08,.025,.88),(.19,.045,1.05),.21,'ink')
    m.disc(.19,-.053,.62,.19,.10,'gold')
    m.ball(-.10,0,.21,.18,.14,.10,'ivory')
    return m


def survey_telescope():
    m=Model()
    for x,y in [(-.38,-.24),(.38,-.24),(0,.29)]:
        m.rod((x,y,.027),(0,0,.63),.065,'brown')
        m.ball(x,y,.032,.093,.09,.064,'ink')
    m.disc(0,-.04,.64,.18,.22,'gold')
    m.rod((-.49,0,.52),(.39,0,.91),.18,PAINT)
    m.rod((.25,0,.85),(.43,0,.93),.25,'gold')
    m.rod((.421,0,.927),(.443,0,.937),.20,'mint')
    m.rod((-.50,0,.516),(-.58,0,.48),.12,'ink')
    m.rod((-.02,-.03,.78),(.18,-.03,.87),.055,'steel')
    return m


def desk_globe():
    m=Model()
    m.drum(0,0,.055,.53,.11,PAINT)
    m.drum(0,0,.17,.12,.18,'gold')
    m.ring(0,0,.69,.86,.065,'gold',(76,20,0))
    m.axle(0,0,.69,'z')
    m.ball(0,0,.69,.66,.66,.66,'blue')
    # Low-relief land follows the spherical surface in longitude/latitude.
    regions = [
        [(-114,51),(-96,68),(-58,54),(-70,40),(-85,25),(-95,17),(-112,28)],
        [(-80,13),(-51,6),(-36,-8),(-53,-26),(-68,-53),(-76,-24)],
        [(-17,31),(6,38),(30,30),(49,6),(35,-18),(19,-35),(9,-14),(-8,4)],
        [(-9,43),(7,59),(36,69),(73,70),(108,60),(146,48),(112,24),(87,11),(68,23),(43,34),(24,38)],
        [(112,-20),(131,-12),(152,-25),(145,-40),(116,-33)],
        [(-57,60),(-48,79),(-23,77),(-31,62)]]
    for region in regions:
        center = tuple(sum(p[i] for p in region)/len(region) for i in (0,1))
        verts,faces=[],[]
        def point(lon,lat):
            lon,lat=math.radians(lon+35),math.radians(lat)
            return [.334*math.cos(lat)*math.sin(lon),-.334*math.cos(lat)*math.cos(lon),.334*math.sin(lat)]
        for j,b in enumerate(region):
            c=region[(j+1)%len(region)]
            grid={}
            steps=8
            for i in range(steps+1):
                for k in range(steps+1-i):
                    uv=[(center[t]*(steps-i-k)+b[t]*i+c[t]*k)/steps for t in (0,1)]
                    grid[i,k]=len(verts)
                    verts.append(point(*uv))
            for i in range(steps):
                for k in range(steps-i):
                    faces.append([grid[i,k],grid[i+1,k],grid[i,k+1]])
                    if i+k<steps-1:faces.append([grid[i+1,k],grid[i+1,k+1],grid[i,k+1]])
        m.piece('surface',0,0,.69,1,1,1,'mint')
        m.pieces[-1].update(vertices=verts,faces=faces)
    return m


def cup_anemometer():
    m=Model()
    m.base(.46,.40,.09)
    m.drum(0,0,.45,.09,.75,'steel')
    m.drum(0,0,.30,.15,.09,PAINT)
    m.axle(0,0,.85,'z')
    m.ball(0,0,.85,.16,.16,.15,'gold')
    for i in range(3):
        a=i*math.tau/3
        x,y=.37*math.cos(a),.37*math.sin(a)
        m.rod((0,0,.85),(x,y,.85),.039,'charcoal')
        m.ball(x,y,.85,.20,.18,.14,PAINT)
        m.ball(x-.065*math.sin(a),y+.065*math.cos(a),.858,.10,.11,.09,'ink')
    return m


def brass_orrery():
    m=Model()
    m.drum(0,0,.07,.67,.14,PAINT)
    m.drum(0,0,.21,.22,.17,'gold')
    m.drum(0,0,.44,.055,.42,'gold')
    m.ball(0,0,.69,.28,.28,.28,'gold')
    m.axle(0,0,.43,'z')
    for x,y,z,c,d in [(.41,.10,.43,'blue',.16),(-.26,-.18,.52,'rust',.12),(.04,.26,.59,'mint',.09)]:
        m.rod((0,0,z),(x,y,z),.029,'gold')
        m.rod((x,y,z),(x,y,z+.10),.028,'steel')
        m.ball(x,y,z+.12,d,d,d,c)
    return m


def gimbal_compass():
    m=Model()
    m.base(.61,.38,.09)
    for x in (-.32,.32):
        m.rod((x,0,.09),(x,0,.55),.055,'gold')
    m.ring(0,0,.54,.75,.07,PAINT)
    m.dial(0,-.045,.54,.59)
    m.axle(0,-.13,.54,'y')
    m.cone(0,-.13,.63,.082,.19,'red')
    m.cone(0,-.13,.45,.082,.19,'charcoal',(180,0,0))
    m.ball(0,-.15,.54,.076,.043,.076,'gold')
    return m


def metronome():
    m=Model()
    m.base(.57,.39,.09)
    m.piece('tapered_case',0,0,.545,.54,.34,.91,PAINT)
    m.box(0,-.119,.57,.095,.027,.62,'ink',(-8,0,0))
    for i in range(6):
        z=.37+i*.075
        m.box(.02,-.164+(z-.37)*.14,z,.055,.013,.012,'ivory')
    m.rod((0,-.219,.23),(.22,-.219,.86),.029,'gold')
    m.box(.15,-.22,.67,.12,.065,.10,'steel',(0,19,0))
    return m


def desk_gyroscope():
    m=Model()
    m.drum(0,0,.055,.53,.11,'brown')
    for x in (-.32,.32):
        m.rod((x*.52,0,.11),(x,0,.58),.055,'gold')
    m.ring(0,0,.60,.76,.071,'steel')
    m.axle(0,0,.60,'x')
    m.ring(0,0,.60,.57,.055,PAINT,(55,0,0))
    m.rod((-.25,0,.60),(.25,0,.60),.04,'gold')
    m.drum(0,0,.60,.32,.105,'gold',(0,90,0))
    return m


def sand_timer():
    m=Model()
    for z in (.055,.95): m.drum(0,0,z,.56,.11,PAINT)
    for x,y in [(-.205,-.105),(.205,-.105),(0,.22)]:
        m.rod((x,y,.10),(x,y,.90),.037,'gold')
    # Open glass outlines preserve the interior sand in the opaque workbench renderer.
    for z,r in [(.14,.15),(.23,.17),(.77,.17),(.87,.15)]:
        m.ring(0,0,z,r*2,.019,'mint',(0,0,0))
    for angle in (25,145,265):
        x,y=math.cos(math.radians(angle)),math.sin(math.radians(angle))
        for za,ra,zb,rb in [(.14,.15,.23,.17),(.23,.17,.50,.022),(.52,.022,.77,.17),(.77,.17,.87,.15)]:
            m.rod((x*ra,y*ra,za),(x*rb,y*rb,zb),.014,'mint')
    m.cone(0,0,.195,.28,.18,'gold')
    m.cone(0,0,.70,.20,.24,'gold',(180,0,0))
    m.rod((0,0,.20),(0,0,.61),.014,'gold')
    m.drum(0,0,.51,.082,.075,'steel')
    return m


def seismograph():
    m=Model()
    m.base(1.04,.49,.11)
    m.drum(-.22,0,.37,.35,.52,'cream',(0,90,0))
    for x in (-.48,.04):
        m.drum(x,0,.37,.40,.045,'gold',(0,90,0))
        m.box(x,0,.21,.06,.13,.22,'steel')
    m.box(.36,.13,.40,.09,.08,.61,PAINT)
    m.rod((.36,.13,.68),(-.12,.06,.68),.055,'steel')
    m.rod((-.12,.06,.68),(-.14,-.11,.50),.024,'ink')
    for i,z in enumerate([.38,.42,.34,.45,.35,.38]):
        if i: m.rod((-.44+(i-1)*.075,-.169,prev),(-.44+i*.075,-.169,z),.013,'rust')
        prev=z
    return m


def laboratory_still():
    m=Model()
    m.base(.91,.42,.09)
    m.ball(-.23,0,.33,.35,.35,.41,'blue')
    m.drum(-.23,0,.60,.08,.22,'steel')
    m.rod((-.23,0,.71),(.27,0,.57),.06,'gold')
    m.rod((-.03,0,.65),(.20,0,.59),.12,'mint')
    m.rod((.27,0,.57),(.30,0,.37),.045,'gold')
    m.cone(.29,0,.22,.25,.25,PAINT)
    m.drum(.29,0,.38,.064,.12,'steel')
    for x in (-.39,-.08): m.rod((x,0,.09),(x,0,.20),.04,'charcoal')
    return m


def telegraph_key():
    m=Model()
    m.base(.88,.47,.11)
    for x in (-.30,.32):
        m.drum(x,.11,.18,.11,.14,'gold')
        m.drum(x,.11,.26,.08,.037,'ink')
    m.box(.04,-.04,.23,.15,.20,.22,'gold')
    m.rod((-.34,-.06,.24),(.30,-.06,.39),.060,'steel')
    m.drum(.30,-.06,.43,.20,.08,PAINT)
    m.drum(-.27,-.055,.17,.09,.10,'gold')
    return m


def recording_barometer():
    m=Model()
    m.base(.75,.44,.12)
    m.box(.22,.06,.43,.14,.13,.62,PAINT)
    for i in range(5):
        m.drum(-.16,-.01,.20+i*.079,.33-i*.012,.051,'gold')
    m.dial(.08,-.055,.76,.44)
    m.axle(.08,-.14,.76,'y')
    m.box(.08,-.14,.84,.025,.022,.16,'rust')
    m.ball(.08,-.15,.76,.055,.03,.055,'ink')
    return m


def tuning_fork():
    m=Model()
    m.base(.70,.45,.16,PAINT)
    m.disc(0,-.232,.088,.092,.027,'ink')
    m.drum(0,0,.30,.076,.28,'steel')
    m.box(0,0,.46,.34,.096,.09,'steel')
    for x in (-.14,.14):
        m.box(x,0,.75,.066,.095,.56,'steel')
    m.rod((.28,-.13,.19),(.28,.14,.48),.035,'brown')
    m.ball(.28,.14,.48,.105,.105,.105,'ink')
    return m


def binocular_viewer():
    m=Model()
    m.drum(0,0,.06,.52,.12,'charcoal')
    m.drum(0,0,.33,.12,.44,'steel')
    m.box(0,0,.63,.54,.26,.15,PAINT)
    for x in (-.17,.17):
        m.disc(x,0,.72,.29,.52,PAINT)
        m.disc(x,-.27,.72,.32,.065,'ink')
        m.disc(x,-.307,.72,.245,.022,'blue')
        m.disc(x,.285,.72,.19,.085,'charcoal')
    return m


def tabletop_radiometer():
    m=Model()
    m.drum(0,0,.065,.54,.13,'brown')
    m.drum(0,0,.25,.11,.26,'gold')
    m.ring(0,0,.68,.75,.043,'steel')
    m.ring(0,0,.68,.75,.043,'steel',(90,0,90))
    m.drum(0,0,.68,.033,.62,'gold')
    m.ball(0,0,1.07,.12,.12,.12,PAINT)
    m.axle(0,0,.65,'z')
    for i in range(4):
        a=i*math.pi/2
        x,y=.23*math.cos(a),.23*math.sin(a)
        m.rod((0,0,.65),(x,y,.65),.020,'steel')
        m.box(x,y,.65,.10,.026,.16,'ink' if i%2 else 'ivory',(0,0,i*90))
    return m


MODELS = [balance_scale, bench_microscope, survey_telescope, desk_globe, cup_anemometer,
          brass_orrery, gimbal_compass, metronome, desk_gyroscope, sand_timer, seismograph,
          laboratory_still, telegraph_key, recording_barometer, tuning_fork, binocular_viewer,
          tabletop_radiometer]
