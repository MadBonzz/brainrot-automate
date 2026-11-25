"""Low-poly construction pieces. Positions are relative to the support surface; angles are degrees."""
import math

PAINT = 'prop_paint'


class Model:
    def __init__(self):
        self.pieces = []
        self.pivot = None

    def axle(self, x, y, z, axis):
        """All subsequent pieces rotate about this point on a turn cue."""
        self.pivot = dict(point=[x,y,z], axis=axis)

    def piece(self, shape, x,y,z, w,d,h, color, rotation=(0,0,0)):
        self.pieces.append(dict(shape=shape, pos=[x,y,z], size=[w,d,h], color=color,
                                rotation=list(rotation), moving=self.pivot is not None))

    def box(self, x,y,z, w,d,h, c=PAINT, rotation=(0,0,0)):
        self.piece('box',x,y,z,w,d,h,c,rotation)

    def ball(self, x,y,z, w,d,h, c):
        self.piece('sphere',x,y,z,w,d,h,c)

    def drum(self, x,y,z, diameter,height, c, rotation=(0,0,0)):
        self.piece('cylinder',x,y,z,diameter,diameter,height,c,rotation)

    def disc(self, x,y,z, diameter,depth, c):
        self.drum(x,y,z,diameter,depth,c,(90,0,0))

    def cone(self, x,y,z, diameter,height, c, rotation=(0,0,0)):
        self.piece('cone',x,y,z,diameter,diameter,height,c,rotation)

    def ring(self, x,y,z, diameter,thickness, c, rotation=(90,0,0)):
        self.piece('ring',x,y,z,diameter,diameter,thickness,c,rotation)

    def rod(self, a,b, diameter,c):
        self.along('cylinder',a,b,diameter,c)

    def along(self, shape,a,b,diameter,c):
        dx,dy,dz=(q-p for p,q in zip(a,b))
        length=math.sqrt(dx*dx+dy*dy+dz*dz)
        mid=[(p+q)/2 for p,q in zip(a,b)]
        ang=(0,math.degrees(math.acos(dz/length)),math.degrees(math.atan2(dy,dx)))
        self.piece(shape,*mid,diameter,diameter,length,c,ang)

    def base(self, w,d,h=.10,c='brown'):
        self.box(0,0,h/2,w,d,h,c)

    def dial(self, x,y,z, diameter):
        self.disc(x,y,z,diameter,.07,'gold')
        self.disc(x,y-.042,z,diameter*.84,.026,'cream')
        for i in range(8):
            a=i*math.tau/8
            self.box(x+math.sin(a)*diameter*.33,y-.065,z+math.cos(a)*diameter*.33,
                     .018,.014,diameter*.09,'ink',(0,math.degrees(a),0))
