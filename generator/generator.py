import numpy as np
import math
from math import pi, cos, sin
from shapely.geometry import Point,LineString,Polygon,MultiPolygon,MultiPoint,MultiLineString,GeometryCollection
from shapely.coords import CoordinateSequence
from shapely import affinity
from shapely.ops import unary_union,split
from solid.objects import translate
from solid import *
# from solid import hull
# from solid import union
from solid.objects import linear_extrude, union, hull
import random
# from solid.extrude_along_path import extrude_along_path
from solid import scad_render_to_file, polygon

def add_roof(base_poly,offset,height,thickness,homeheight):
    footprint=base_poly.buffer(offset).simplify(0.01,preserve_topology=False)
    peak=list(list(footprint.centroid.coords)[0])
    peak.append(height)
    basepts=list(footprint.exterior.coords)
    basepts=[(list(pt)+[0]) for pt in basepts]
    basepts.append(basepts[0])
    faces=[]
    points=[peak]
    for i in range(len(basepts)-1):
        points.append(basepts[i])
        faces.append([0,i,i+1])
    roof=translate([0,0,homeheight])(polyhedron(points=points,faces=faces))
    base=translate([0,0,-thickness-.25])(linear_extrude(thickness)(polygon(list(footprint.exterior.coords))))
    return roof,base


def fractalize(chaos,poly,cuts,rays,count,maxcount,rgb=[1,.66,.8]):
    if count<maxcount:
        #shift=chaos*1/(1+count)
        shift=count/maxcount
        phis=np.linspace(0+shift,shift+2*pi,rays,endpoint=False)
        pt=list(poly.centroid.coords)[0]
        r=1000
        geom=poly
        lines=[LineString([[(pt[0]-r*math.cos(phi)),(pt[1]-r*math.sin(phi))],[(pt[0]+r*math.cos(phi)),(pt[1]+r*math.sin(phi))]]) for phi in phis]
        for line in lines:
            try:
                newgeom=split(geom,line)
            except:
                pass
            geom=MultiPolygon([g for g in newgeom if isinstance(g,Polygon) or isinstance(g,MultiPolygon)])
            for g in geom:
                h=1/(1+(g.area)**.5)
                c=np.clip([np.random.normal(rgb[0],chaos/25),np.random.normal(rgb[1],chaos/25),np.random.normal(rgb[2],chaos/25)],0,1)
                c*=h
                c=np.clip(c,0,1)
                cuts.append(color(c)(linear_extrude(h)(polygon(list(g.exterior.coords)))))
        if isinstance(geom,Polygon):
            fractalize(chaos,geom,cuts,rays,count+1,maxcount,rgb)
        else:
            for poly in geom:
                fractalize(chaos,poly,cuts,rays,count+1,maxcount,rgb)

def follow_lpf(line,momentum=0.6,wiggle=.2):
    out = [line[0]+1] 
    for i in range(1,len(line)):
        prev = line[i]
        prevprev=line[i-1]
        target = prev+1  
        path = prev+(prev-prevprev)/2
        delta=target-path
        correction = delta*random.uniform(1-wiggle,1+wiggle)
        corrected = path+correction
        out_lpf = out[-1]*momentum + corrected*(1-momentum)
        out.append(out_lpf)

    out=[o-1 for o in out]
    return out

def lpf(data,momentum=0.1):
    out = [data[0]]
    for i in range(1,len(data)):
        out.append(out[-1]*momentum+data[i]*(1-momentum))
    return out

def add_doors(chaos,base_poly,rooms,offset=-.5,doorsize=(3,7)):
    mapping=np.zeros((len(rooms)+1,len(rooms)))
    doors=[]
    extdoors=[]
    for i in range(len(rooms)):
        if rooms[i].intersects(base_poly.exterior):
            overlap=rooms[i].intersection(base_poly.exterior)
            if isinstance(overlap,MultiLineString):
                overlap=list(list(overlap)[0].coords)
            if isinstance(overlap,LineString):
                overlap=list(overlap.coords)
            if isinstance(overlap,list):
                if len(overlap)>1:
                    l=((overlap[0][0]-overlap[1][0])**2+(overlap[0][1]-overlap[1][1])**2)**.5
                    if l==0:
                        l=.00001
                    phi=math.atan((overlap[0][1]-overlap[1][1])/(.00001+overlap[0][0]-overlap[1][0]))
                    phi+=pi/2
                    floor,ceiling=.2+(doorsize[0]/2)/l,.8-(doorsize[0]/2)/l
                    point=np.clip(np.random.normal(0.5,chaos),a_min=floor,a_max=ceiling)
                    doorscalar=np.clip(doorsize[0]/(2*l),.01,.99)
                    point=np.clip(point,.01,.99)
                    l,r=list(np.average(overlap[:2],axis=0,weights=[point+doorscalar,1-(point+doorscalar)])),list(np.average(overlap[:2],axis=0,weights=[point-doorscalar,1-(point-doorscalar)]))
                    r.append(0)
                    l.append(0)
                    doorbase=[[r[0]-math.cos(phi),r[1]-math.sin(phi)],[l[0]-math.cos(phi),l[1]-math.sin(phi)],[l[0]+math.cos(phi),l[1]+math.sin(phi)],[r[0]+math.cos(phi),r[1]+math.sin(phi)]]
                    extdoors.append(doorbase)
                    mapping[-1,i]+=1

        for j in range(len(rooms)):
            if i!=j:
                if rooms[i].intersects(rooms[j]) and mapping[i,j]<np.clip(np.random.normal(1,2*chaos),a_min=1,a_max=1+chaos*6):
                    overlap=rooms[i].intersection(rooms[j])
                    if isinstance(overlap,Polygon):
                        overlap=list(overlap.exterior.coords)
                    if isinstance(overlap,LineString):
                        overlap=list(overlap.coords)
                    if isinstance(overlap,list):
                        if isinstance(rooms[i].intersection(rooms[j]),Polygon):
                            overlap=list(rooms[i].intersection(rooms[j]).exterior.coords)
                        else:
                            overlap=list(rooms[i].intersection(rooms[j]).coords)
                        if len(overlap)>1:
                            l=((overlap[0][0]-overlap[1][0])**2+(overlap[0][1]-overlap[1][1])**2)**.5
                            if l==0:
                                l=.001
                            phi=math.atan((overlap[0][1]-overlap[1][1])/(.00001+overlap[0][0]-overlap[1][0]))
                            phi+=pi/2
                            floor,ceiling=.2+(doorsize[0]/2)/l,.8-(doorsize[0]/2)/l
                            point=np.clip(np.random.normal(0.5,chaos),a_min=floor,a_max=ceiling)
                            point=np.clip(point,.01,.99)
                            doorscalar=np.clip(doorsize[0]/(2*l),.01,.99)
                            l,r=list(np.average(overlap[:2],axis=0,weights=[point+doorscalar,1-(point+doorscalar)])),list(np.average(overlap[:2],axis=0,weights=[point-doorscalar,1-(point-doorscalar)]))
                            r.append(0)
                            l.append(0)
                            doorbase=[[r[0]-math.cos(phi),r[1]-math.sin(phi)],[l[0]-math.cos(phi),l[1]-math.sin(phi)],[l[0]+math.cos(phi),l[1]+math.sin(phi)],[r[0]+math.cos(phi),r[1]+math.sin(phi)]]
                            doors.append(doorbase)
                            mapping[i,j]+=1

    doorsout=[]
    extdoorsout=[]
    for door in doors:
        doorsout.append(linear_extrude(doorsize[1])(polygon(door)))
    for door in extdoors:
        extdoorsout.append(linear_extrude(doorsize[1])(polygon(door)))
    return(sum(extdoorsout),sum(doorsout))


def make_geom(base_poly,rooms,evector=[0,0,10],generative=False,slices=100,linepts=100):
    roomsout=[scale([.999,.999,.999])(extrude_geom(room,evector,offset=-0.25)) for room in rooms]
    baseout=extrude_geom(base_poly,evector)
    return baseout,roomsout               

    
def extrude_geom(geom,evector,offset=-.5):
    sub=geom.buffer(offset)
    if isinstance(sub,MultiPolygon):
        sub=sub.geoms[0]
    sub=polygon(list(sub.exterior.coords))
    geom=polygon(list(geom.exterior.coords))
    if offset<0:
        geom=linear_extrude(evector[2])(geom)
        sub=translate([0,0,-evector[2]/2])(linear_extrude(evector[2]*2)(sub))
        out=geom-sub
    else:
        sub=linear_extrude(evector[2])(sub)
        geom=translate([0,0,-evector[2]/2])(linear_extrude(evector[2]*2)(geom))
        out=sub-geom

    return out

def subdivide_base(chaos,basegeom,rooms=[.4,.3,.5,.2,.4,.4,.5]):
    roomgeoms=[]
    start=basegeom.area
    geom=basegeom
    for i in range(len(rooms)):
        area=geom.area
        scalar=rooms[i]
        target=start*scalar
        shift=start/area
        target/=shift
        scalar=target/area
        rect=geom.minimum_rotated_rectangle
        pt=rect.centroid
        rectpts=list(rect.exterior.coords)
        pt=np.average((rectpts[0],rectpts[1]),weights=[scalar,1-scalar],axis=0)
        result=[]
        while len(result)<2:
            normal=math.atan((rectpts[0][1]-rectpts[1][1])/(.0001+rectpts[0][0]-rectpts[1][0]))+np.random.normal(pi/2,chaos/10)
            sliceline=LineString([(pt[0]+cos(normal)*10000,pt[1]+sin(normal)*10000),(pt[0]-cos(normal)*10000,pt[1]-sin(normal)*10000)])
            result=split(geom,sliceline)
        try:
            slice_a,slice_b=result
        except:
            try:
                if len(result)>2:
                    result=result[:2]
                    slice_a,slice_b=result
            except:
                polys=[]
                for g in result.geoms:
                    if isinstance(g,Polygon):
                        polys.append(g)
                        if len(polys)==2:
                            break
                result=polys
            
        slice_a,slice_b=result
        if slice_a.area>slice_b.area==scalar>0.5:
            take,keep=slice_a,slice_b
        else:
            take,keep=slice_b,slice_a
        if isinstance(take,MultiPolygon):
            take=list(take.geoms)[0]
        if isinstance(keep,MultiPolygon):
            keep=list(keep.geoms)[0]

        roomgeoms.append(take)
        geom=keep
    return roomgeoms

def base_polygon(chaos,n_vertices,r):
    if n_vertices==2 or n_vertices>8:
        n_vertices=100
        rs=np.random.normal(r,.01*chaos,n_vertices)
    else:
        rs=np.random.normal(r,chaos,n_vertices)
    phis=np.linspace(pi/4,9/4*pi,endpoint=False,num=n_vertices)
    points=[(cos(phis[i])*rs[i],sin(phis[i])*rs[i]) for i in range(n_vertices)]
    return Polygon(points)

def base_polygons(chaos,n_polygons=[1,2,6],n_vertices=[2,4,10],bounding_box=[50,20]):
    #number of base polygons
    floor,mu,ceiling=n_polygons
    mu+=chaos*3
    n_polygons=int(np.clip(np.random.normal(mu,chaos),floor,ceiling))
    #number of vertices per base polygon
    floor,mu,ceiling=n_vertices
    mu+=chaos*4
    n_vertices=np.random.normal(mu,chaos,n_polygons)
    n_vertices=np.clip(n_vertices,floor,ceiling).astype(int)
    #radius per base polygon
    bbeuclid=0.5*(bounding_box[0]**2+bounding_box[1]**2)**.5
    floor,mu,ceiling=bbeuclid/8,bbeuclid,bbeuclid
    rs=np.clip(np.random.normal(mu,chaos,n_polygons),floor,ceiling)
    xs=np.clip(np.random.normal(0,bbeuclid/1+4*chaos,n_polygons),a_min=0,a_max=bbeuclid)
    ys=np.clip(np.random.normal(0,bbeuclid/1+4*chaos,n_polygons),a_min=0,a_max=bbeuclid)
    displacements=[(xs[i],ys[i]) for i in range(n_polygons)]
    polygons=[]
    for n in range(n_polygons):
        polygons.append(affinity.translate(base_polygon(chaos,n_vertices[n],rs[n]),displacements[n][0],displacements[n][1],0))
    return polygons
    

def base(chaos,base_geoms):
    #standard case
    base_geom=unary_union(base_geoms)
    if isinstance(base_geom,MultiPolygon):
        return list(base_geom.geoms)[0]
    return base_geom


def gen_form(chaos, ceiling_height, no_of_rooms, length, width, fractalize=True,make_roof=True):
    base_polys=base_polygons(chaos, bounding_box=[length, width])
    base_poly=base(chaos, base_polys)
    

    nodes=list(base_poly.exterior.coords)
    edges=[[nodes[i],nodes[i+1]] for i in range(len(nodes)-1)]
    fractal_pieces=[]
    cweights=np.clip(np.random.normal(.5,chaos,size=3),.2,.8)
    if fractalize:
        rays,maxcount=int(np.clip(np.random.normal(2,chaos*2,size=1),1,5)),int(np.clip(np.random.normal(3,chaos*3,size=1),2,4))
        if rays%2==0:
            rays-=1

        for edge in edges:
            poly=[edge[1],edge[0]]
            phi=pi/2+math.atan((edge[0][1]-edge[1][1])/(.0001+edge[0][0]-edge[1][0]))
            if not Polygon(base_poly).contains(Point([edge[0][0]+.001*math.cos(phi),edge[0][1]+.001*math.sin(phi)])):
                poly.append([edge[0][0]+10*math.cos(phi),edge[0][1]+10*math.sin(phi)])
                poly.append([edge[1][0]+10*math.cos(phi),edge[1][1]+10*math.sin(phi)])
                pos=-1
            else:
                poly.append([edge[0][0]-10*math.cos(phi),edge[0][1]-10*math.sin(phi)])
                poly.append([edge[1][0]-10*math.cos(phi),edge[1][1]-10*math.sin(phi)])
                pos=1

            cuts=[]
            
            centerpt=np.average(edge,axis=0)
            translation=[-centerpt[0],-centerpt[1],0]
            translationback=[centerpt[0],centerpt[1],0]
            rotation=[math.cos(phi-pi/2),math.sin(phi-pi/2),0]
            fractalize(chaos,Polygon(poly),cuts,rays,0,maxcount,cweights)
            cuts=translate(translation)(cuts)
            cuts=rotate(90*pos,rotation)(cuts)
            cuts=translate([0,0,10])(translate(translationback)(cuts))
            fractal_pieces.append(cuts)

    homeheight=np.clip(np.random.normal(ceiling_height,chaos*3),a_min=0.8*ceiling_height,a_max=1.2*ceiling_height)
    room_frac = np.clip(np.random.normal(0.4, 0.1, no_of_rooms - 1), a_min=0.1, a_max=0.99)
    rooms=subdivide_base(chaos,base_poly, rooms=room_frac)
    solidbase,solidrooms=make_geom(base_poly,rooms,evector=[0,0,homeheight])

    
    roofheight=np.random.normal(10,chaos*3)
    roof,slab=add_roof(base_poly,1,roofheight,.25,homeheight)
    if not make_roof:
        roof=[]
    extdoors,doors=add_doors(chaos,base_poly,rooms)
    extdoorspos=intersection()(solidbase,extdoors)
    doorspos=[intersection()(room,doors) for room in solidrooms]
    subs=translate([0,0,.25])(doors+extdoors)
    solidbase=solidbase-subs
    fractal_pieces=[pc-subs for pc in fractal_pieces]

    csrooms=[]
    for room in solidrooms:
        c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
        room=room-subs
        room=color(c)(room)
        csrooms.append(room)

    c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
    doorspos=scale([.99,.99,.99])(doorspos)
    doorspos=color(c)(doorspos)
    doorspos=translate([0,0,.25])(doorspos)

    c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
    extdoorspos=scale([.99,.99,.99])(extdoorspos)
    extdoorspos=color(c)(extdoorspos)
    extdoorspos=translate([0,0,.25])(extdoorspos)

    c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
    solidbase=color(c)(solidbase)

    c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
    roof=color(c)(roof)

    c=np.clip(np.random.normal(.75,chaos/2,size=3),0,1)
    slab=color(c)(slab)
    

    return union()(solidbase,csrooms,doorspos,extdoorspos,fractal_pieces,roof,slab)
