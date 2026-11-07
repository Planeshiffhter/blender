"""Original editable C01 head, facial blend shapes, and sculpted wavy hair.

Coordinates are metres, Z up, character faces -Y. No external assets required.
"""
import math
from math import sin, cos, pi, sqrt, exp
import bpy
import bmesh
from mathutils import Vector


def build_head(collection):
    objects=[]
    def material(name, color, rough=.45, sss=0):
        mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.diffuse_color=(*color,1)
        mat.use_nodes=True
        node=mat.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value=(*color,1)
        node.inputs['Roughness'].default_value=rough
        if sss:
            node.inputs['Subsurface Weight'].default_value=sss
            node.inputs['Subsurface Radius'].default_value=(1,.45,.25)
        return mat
    skin=material('C01_skin_warm_peach',(.64,.33,.19),.47,.075)
    blush=material('C01_soft_rose',(.66,.25,.20),.5,.04)
    lips=material('C01_lips_rosewood',(.43,.095,.075),.34,.03)
    mouthmat=material('C01_mouth_interior',(.045,.008,.012),.63)
    ivory=material('C01_eye_ivory',(.92,.94,.91),.23)
    teethmat=material('C01_teeth_enamel',(.88,.84,.70),.3)
    iris=material('C01_iris_honey_brown',(.21,.072,.014),.26)
    irislite=material('C01_iris_amber_ring',(.43,.20,.035),.29)
    pupil=material('C01_pupil',(.006,.003,.002),.21)
    hair=material('C01_chestnut_hair',(.057,.018,.009),.43)
    hairlight=material('C01_chestnut_highlight',(.09,.032,.013),.43)
    hairdark=material('C01_hair_root',(.025,.008,.004),.42)
    lashes=material('C01_brows_lashes',(.035,.013,.009),.5)
    pearl=material('C01_pearl_earrings',(.8,.76,.62),.22)
    # Procedural microvariation is fully packed as nodes; no image dependency.
    for mat in (skin,hair,hairlight):
        nt=mat.node_tree
        noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95 if mat==skin else 27
        noise.inputs['Detail'].default_value=2
        bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.035 if mat==skin else .12
        bump.inputs['Distance'].default_value=.002 if mat==skin else .004
        nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
    def mesh(name,verts,faces,mat,bind='head',sub=0):
        data=bpy.data.meshes.new(name+'_mesh'); data.from_pydata(verts,[],faces); data.update()
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        ob=bpy.data.objects.new(name,data);collection.objects.link(ob);objects.append(ob)
        if mat: data.materials.append(mat)
        for p in data.polygons:p.use_smooth=True
        ob['c01_bind']=bind
        if sub:
            mod=ob.modifiers.new('Sculpt surface subdivision','SUBSURF');mod.levels=sub;mod.render_levels=sub
        return ob
    def shapes(ob, function):
        ob.shape_key_add(name='Basis')
        for key in ('Blink','Smile','MouthOpen','Surprise','Sad','Angry','Viseme_AA','Viseme_EE','Viseme_OO'):
            sk=ob.shape_key_add(name=key)
            for v in sk.data:v.co=function(key,v.co.copy())
        ob['c01_role']='facial_shapes'
    def ellipsoid(name,center,scale,mat,bind='head',nu=36,nv=22,sub=0):
        verts=[];faces=[]
        for j in range(nv+1):
            lat=pi*j/nv
            for i in range(nu):
                t=2*pi*i/nu
                verts.append((center[0]+scale[0]*sin(lat)*cos(t),center[1]+scale[1]*sin(lat)*sin(t),center[2]+scale[2]*cos(lat)))
        for j in range(nv):
            for i in range(nu):
                a=j*nu+i;b=j*nu+(i+1)%nu;faces.append((a,b,b+nu,a+nu))
        return mesh(name,verts,faces,mat,bind,sub)
    def gauss(x,z,cx,cz,sx,sz):return exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
    # Head profile deliberately varies jaw, cheek, temple, forehead and nose.
    profiles=[(1.285,.005,.057,.006),(1.315,.061,.093,.002),(1.35,.111,.116,0),(1.40,.143,.13,0),(1.46,.165,.142,0),(1.53,.171,.143,0),(1.60,.166,.145,.004),(1.67,.139,.124,.006),(1.72,.063,.058,.008),(1.735,.002,.002,.008)]
    def profile(z):
        for index,(a,b) in enumerate(zip(profiles,profiles[1:])):
            if a[0]<=z<=b[0]:
                t=(z-a[0])/(b[0]-a[0])
                previous=profiles[max(0,index-1)];following=profiles[min(len(profiles)-1,index+2)]
                values=[]
                for k in (1,2,3):
                    m0=(b[k]-previous[k])/(b[0]-previous[0])*(b[0]-a[0])
                    m1=(following[k]-a[k])/(following[0]-a[0])*(b[0]-a[0])
                    values.append((2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*m0+(-2*t**3+3*t*t)*b[k]+(t**3-t*t)*m1)
                return values
        return profiles[0][1:] if z<profiles[0][0] else profiles[-1][1:]
    def front_y(x,z):
        rx,ry,cy=profile(z);f=sqrt(max(0,1-(x/max(rx,.001))**2))
        nose=.027*gauss(x,z,0,1.512,.025,.067)+.061*gauss(x,z,0,1.463,.027,.023)
        nose+=.018*(gauss(x,z,.022,1.454,.014,.014)+gauss(x,z,-.022,1.454,.014,.014))
        cheek=.011*(gauss(x,z,.098,1.459,.052,.038)+gauss(x,z,-.098,1.459,.052,.038))
        sockets=.018*(gauss(x,z,.073,1.54,.052,.04)+gauss(x,z,-.073,1.54,.052,.04))
        muzzle=.009*gauss(x,z,0,1.395,.065,.029)
        return cy-ry*f+f**5*(-nose-cheek+sockets-muzzle)
    verts=[];faces=[];rows=64;cols=96
    for j in range(rows+1):
        z=1.285+(1.735-1.285)*j/rows
        rx,ry,cy=profile(z)
        for i in range(cols):
            t=2*pi*i/cols;x=rx*sin(t);y=cy-ry*cos(t)
            front=max(cos(t),0)**5
            # Nose and bridge are continuous with the cheek surface.
            nose=.027*gauss(x,z,0,1.512,.025,.067)+.061*gauss(x,z,0,1.463,.027,.023)
            nose+=.018*(gauss(x,z,.022,1.454,.014,.014)+gauss(x,z,-.022,1.454,.014,.014))
            cheek=.011*(gauss(x,z,.098,1.459,.052,.038)+gauss(x,z,-.098,1.459,.052,.038))
            sockets=.018*(gauss(x,z,.073,1.54,.052,.04)+gauss(x,z,-.073,1.54,.052,.04))
            muzzle=.009*gauss(x,z,0,1.395,.065,.029)
            y+=front*(-nose-cheek+sockets-muzzle)
            verts.append((x,y,z))
    for j in range(rows):
        for i in range(cols):
            a=j*cols+i;b=j*cols+(i+1)%cols;faces.append((a,b,b+cols,a+cols))
    faces.append(tuple(reversed(range(cols))));faces.append(tuple(rows*cols+i for i in range(cols)))
    face=mesh('C01_Face_Sculpted_Quad_Surface',verts,faces,skin,sub=1)
    def face_shape(key,co):
        x,y,z=co;front=max(0,min(1,(-y-.045)/.07))
        if key=='Viseme_AA':key='MouthOpen'
        if key=='Viseme_EE':key='Smile'
        if key=='Viseme_OO':co.x*=1-.08*gauss(x,z,0,1.39,.08,.04)*front
        if key=='Smile':
            co.z+=.012*gauss(x,z,0,1.393,.09,.037)*abs(x)/.055*front
            co.y-=.004*gauss(x,z,0,1.44,.11,.04)*front
        elif key in ('MouthOpen','Surprise'):
            influence=gauss(x,z,0,1.34,.10,.07)*front
            co.z-= (.016 if key=='MouthOpen' else .022)*influence
            co.y+=.004*influence
        elif key=='Sad':co.z-=.008*gauss(x,z,0,1.39,.085,.035)*abs(x)/.06*front
        elif key=='Angry':co.y-=.003*gauss(x,z,0,1.59,.12,.025)*front
        return co
    shapes(face,face_shape)
    # Ears with inset concha; pearl studs follow the head.
    for sign,side in ((1,'L'),(-1,'R')):
        ellipsoid('C01_Ear_'+side,(sign*.163,-.001,1.455),(.024,.025,.048),skin)
        ellipsoid('C01_Ear_Concha_'+side,(sign*.178,-.015,1.456),(.010,.016,.027),blush)
        ellipsoid('C01_Pearl_'+side,(sign*.172,-.025,1.418),(.010,.010,.010),pearl,nu=20,nv=12)
    # Tiny nostril recesses on the sculpted integrated nose.
    for sign in (-1,1):
        ellipsoid('C01_Nostril_'+str(sign),(sign*.0175,-.188,1.451),(.006,.0025,.0036),mouthmat,nu=20,nv=12)
    # Lip ribbons, recessed mouth and a curved upper tooth strip.
    def mouth_surface(name,kind,mat):
        vs=[];fs=[];N=48;M=8
        for j in range(M+1):
            v=j/M
            for i in range(N+1):
                t=-1+2*i/N;x=.059*t
                line=1.389+.015*t*t
                aperture=.008*(1-t*t)
                if kind=='interior':z=line+(-1+2*v)*aperture;y=-.138-.006*(1-t*t)
                elif kind=='upper':
                    top=.0055*(1-t*t)*(1-.35*exp(-(t/.18)**2))
                    z=line+aperture+top*v;y=-.147-.008*sin(pi*v)*(1-t*t)
                elif kind=='lower':
                    z=line-aperture-.008*(1-t*t)*v;y=-.149-.010*sin(pi*v)*(1-t*t)
                else:z=line+.002+v*.004*(1-t*t);y=-.1475
                vs.append((x,y,z))
        for j in range(M):
            for i in range(N):a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
        ob=mesh(name,vs,fs,mat,sub=1)
        def deform(key,co):
            t=co.x/.059;fade=max(0,1-t*t);base=1.389+.015*t*t
            if key=='Viseme_AA':key='MouthOpen'
            if key=='Viseme_EE':
                co.x*=1.18;co.z=base+(co.z-base)*.7
                key='Smile'
            if key=='Viseme_OO':
                co.x*=.48
                co.z=1.389+(co.z-base)*1.9+.006*t*t
                if kind=='lower':co.z-=.012*fade
                if kind=='interior':co.z-=.009*fade
                co.y-=.009*fade
            if key=='Smile':co.z+=.012*t*t;co.x*=1.06
            if key=='Sad':co.z-=.018*t*t
            if key in ('MouthOpen','Surprise'):
                amount=.018 if key=='MouthOpen' else .027
                if kind=='lower':co.z-=amount*fade
                elif kind=='interior':co.z-=amount*fade*(1-(co.z-base)/.008)/2
                elif kind=='upper':co.z+=.003*fade
            if key=='Angry':co.z-=.003*fade
            return co
        shapes(ob,deform);return ob
    mouth_surface('C01_Mouth_Cavity','interior',mouthmat)
    mouth_surface('C01_Upper_Lip','upper',lips)
    mouth_surface('C01_Lower_Lip','lower',lips)
    mouth_surface('C01_Upper_Teeth','teeth',teethmat)
    # Almond sclera surface and skin eyelid bands: each is deformable for a true blink.
    for sign,side in ((1,'L'),(-1,'R')):
        cx=sign*.073;cz=1.541;cy=-.142
        def eye_shape(key,co):
            if key=='Blink':
                co.z=cz+.001+(co.z-cz)*.015;co.y+=.035
            elif key=='Smile':co.z=cz+(co.z-cz)*.87+.002
            elif key=='Surprise':co.z=cz+(co.z-cz)*1.11
            elif key=='Sad':co.z-=.002
            return co
        vs=[(cx,cy-.027,cz)];fs=[];N=64;R=9
        for j in range(1,R+1):
            r=j/R
            for i in range(N):
                t=2*pi*i/N;u=cos(t);v=sin(t)
                x=cx+.044*r*u;z=cz+r*((.027 if v>0 else .020)*v)+sign*(x-cx)*.065
                y=cy-.027*sqrt(max(.02,1-.82*r*r))
                vs.append((x,y,z))
        for i in range(N):fs.append((0,1+i,1+(i+1)%N))
        for j in range(R-1):
            start=1+j*N
            for i in range(N):a=start+i;b=start+(i+1)%N;fs.append((a,b,b+N,a+N))
        eye=mesh('C01_EyeWhite_'+side,vs,fs,ivory,'eye.'+side,sub=1);shapes(eye,eye_shape)
        # Iris and pupil are convex layered meshes, not texture planes.
        for suffix,scale,mat,y in [('Iris_Rim',(.023,.003,.025),lashes,-.170),('Iris',(.0207,.0035,.023),iris,-.173),('Iris_Amber',(.0155,.003,.0185),irislite,-.176),('Pupil',(.0115,.003,.014),pupil,-.179)]:
            ob=ellipsoid('C01_'+suffix+'_'+side,(cx,y,cz-.001),scale,mat,'eye.'+side,nu=36,nv=20)
            shapes(ob,eye_shape)
        for dx,dz,rad in [(-.006,.010,.004),(.006,-.005,.0018)]:
            ob=ellipsoid('C01_Eye_Catchlight_'+side+'_'+str(dx),(cx+dx,-.183,cz+dz),(rad,.0015,rad),ivory,'eye.'+side,nu=16,nv=10);shapes(ob,eye_shape)
        for upper in (True,False):
            N=40;M=4;vs=[];fs=[]
            for j in range(M+1):
                w=j/M
                for i in range(N+1):
                    t=pi*i/N;u=cos(t);v=sin(t)*(1 if upper else -1)
                    x=cx+(.044+.014*w)*u
                    z=cz+((.027 if upper else .020)+(.016 if upper else .012)*w)*v+sign*(x-cx)*.065
                    y=-.154*(1-w)+(front_y(x,z)-.001)*w-.001*sin(pi*w)
                    vs.append((x,y,z))
            for j in range(M):
                for i in range(N):a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
            lid=mesh('C01_'+('Upper' if upper else 'Lower')+'_Eyelid_'+side,vs,fs,skin,sub=1)
            def lid_shape(key,co,upper=upper):
                if key=='Blink':
                    co.z=cz+.001+(co.z-cz)*.04;co.y-=.018
                if key=='Smile':co.z=cz+(co.z-cz)*.86+.002
                if key=='Surprise':co.z=cz+(co.z-cz)*1.16
                if key=='Sad':co.z-=.003
                if key=='Angry':co.z-=.007*(1 if upper else 0)
                return co
            shapes(lid,lid_shape)
        # Sweep a fine tapered lash ribbon along upper rim.
        vs=[];fs=[]
        for j in (0,1):
            for i in range(49):
                t=pi*i/48;x=cx+.044*cos(t);z=cz+.027*sin(t)+sign*(x-cx)*.065
                vs.append((x,-.157-j*.0004,z+j*(.0025+.0015*sin(t))))
        for i in range(48):fs.append((i,i+1,i+50,i+49))
        lash=mesh('C01_Upper_Lash_'+side,vs,fs,lashes,sub=1);shapes(lash,lid_shape)
        # Arched eyebrow as a flattened tapered mesh.
        vs=[];fs=[]
        for j in range(5):
            for i in range(33):
                t=i/32;x=sign*(.027+.101*t)
                z=1.602+.014*sin(pi*t)-.010*t
                width=.0045*(sin(pi*t)**.4+.15)
                vs.append((x,-.139+.015*t,z+(-1+j/2)*width))
        for j in range(4):
            for i in range(32):a=j*33+i;fs.append((a,a+1,a+34,a+33))
        brow=mesh('C01_Brow_'+side,vs,fs,lashes,sub=1)
        def brow_shape(key,co):
            t=(abs(co.x)-.027)/.101
            if key=='Surprise':co.z+=.023
            elif key=='Sad':co.z+=.019*(1-t)-.004*t
            elif key=='Angry':co.z-=.016*(1-t);co.z+=.005*t
            elif key=='Smile':co.z+=.004
            return co
        shapes(brow,brow_shape)
    # Hair cap is a connected sculptural shell, with a side-parted hairline.
    N=96;R=26;vs=[];fs=[]
    for j in range(R+1):
        u=.006+.994*j/R
        for i in range(N):
            t=2*pi*i/N
            # forehead at 1.65, ears/back lower and hidden by flowing locks
            limit=.87+1.22*(1-cos(t))/2+.27*abs(sin(t))
            a=limit*u
            ripple=.0018*sin(19*t+4*u)*u
            x=(.183+ripple)*sin(a)*sin(t)
            y=-(.158+ripple)*sin(a)*cos(t)+.013
            z=1.502+.245*cos(a)+.007*sin(t)*sin(a)
            vs.append((x,y,z))
    for j in range(R):
        for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
    cap=mesh('C01_Hair_Cap',vs,fs,hairdark,sub=1)
    # Curved elliptical swept locks, each with fine longitudinal ridge geometry.
    def catmull(points,t):
        n=len(points)-1;f=t*n;k=min(n-1,int(f));s=f-k
        a=Vector(points[max(0,k-1)]);b=Vector(points[k]);c=Vector(points[k+1]);d=Vector(points[min(n,k+2)])
        return .5*((2*b)+(-a+c)*s+(2*a-5*b+4*c-d)*s*s+(-a+3*b-3*c+d)*s*s*s)
    def lock(name,points,width,depth,mat,front=True):
        N=52;K=12;vs=[];fs=[]
        for j in range(N+1):
            t=j/N;center=catmull(points,t)
            tangent=(catmull(points,min(1,t+.001))-catmull(points,max(0,t-.001))).normalized()
            normal=Vector((0,-1 if front else 1,0));normal=(normal-tangent*normal.dot(tangent)).normalized()
            if normal.length<.01:normal=Vector((1,0,0))
            lateral=tangent.cross(normal).normalized()
            taper=(.43+.57*sin(pi*t)**.35)*(1-.65*t**8)
            for i in range(K):
                a=2*pi*i/K
                ridge=1+.07*cos(4*a+sin(t*9))
                co=center+lateral*(width*taper*cos(a)*ridge)+normal*(depth*taper*sin(a))
                vs.append(tuple(co))
        for j in range(N):
            for i in range(K):a=j*K+i;b=j*K+(i+1)%K;fs.append((a,b,b+K,a+K))
        fs.append(tuple(reversed(range(K))));fs.append(tuple(N*K+i for i in range(K)))
        return mesh(name,vs,fs,mat,sub=1)
    # Continuous shoulder-length hair mass closes the silhouette between outer waves.
    # Two nested curved shells plus boundary quads make one closed editable mesh.
    vs=[];fs=[];A=72;B=32
    for inner in (False,True):
        for j in range(B+1):
            t=j/B
            for i in range(A+1):
                angle=.78+(2*pi-1.56)*i/A
                bottom=1.205+.013*cos(7*angle)+.007*sin(13*angle)
                z=1.59*(1-t)+bottom*t
                radius=.172+.021*sin(pi*t)+.008*sin(3*pi*t+2*angle)
                if inner:radius-=.026
                vs.append((radius*sin(angle),.018-radius*cos(angle),z))
    stride=(A+1)*(B+1)
    for inner in (0,1):
        base=inner*stride
        for j in range(B):
            for i in range(A):
                q=base+j*(A+1)+i
                face=(q,q+1,q+A+2,q+A+1)
                fs.append(tuple(reversed(face)) if inner else face)
    for j in (0,B):
        for i in range(A):q=j*(A+1)+i;fs.append((q,q+1,q+1+stride,q+stride))
    for i in (0,A):
        for j in range(B):q=j*(A+1)+i;fs.append((q,q+A+1,q+A+1+stride,q+stride))
    mesh('C01_Hair_Continuous_Wavy_Mass',vs,fs,hair,sub=1)
    # Back cascade: broad layered waves instead of a ring of primitive cylinders.
    for k in range(19):
        angle=.92+(2*pi-1.84)*k/18
        points=[]
        for j in range(7):
            t=j/6;z=1.66-.475*t
            radius=.10+.092*sin(min(1,t*1.9)*pi/2)+.012*sin(3*pi*t+k*.65)
            phase=angle+.07*sin(3*pi*t+k*.75)
            x=radius*sin(phase);y=.016-radius*cos(phase)
            points.append((x,y,z+.015*sin(k*1.7)*t))
        lock('C01_Hair_BackWave_%02d'%k,points,.033,.008,hairlight if k%5==0 else hair,front=cos(angle)>0)
    # Side face-framing curls fall to the shoulders but leave cheeks unobstructed.
    for sign in (-1,1):
        for k in range(4):
            points=[(sign*(.095+.017*k),-.075+.015*k,1.702-.015*k),
                    (sign*(.166+.009*k),-.104+.018*k,1.62),
                    (sign*(.178+.009*k),-.083+.018*k,1.52),
                    (sign*(.161+.010*k),-.047+.018*k,1.42),
                    (sign*(.193+.010*k),-.038+.018*k,1.33),
                    (sign*(.165+.010*k),-.015+.018*k,1.235-.007*k)]
            lock('C01_Hair_Side_%s_%d'%(sign,k),points,.029,.007,hairlight if k==1 else hair)
    # Sculpted swept fringe defines an off-centre part and forehead silhouette.
    fringe=[
        [(.065,-.047,1.735),(.012,-.123,1.729),(-.064,-.16,1.687),(-.135,-.156,1.622),(-.170,-.112,1.55)],
        [(.078,-.034,1.735),(.015,-.106,1.747),(-.082,-.153,1.708),(-.151,-.14,1.642),(-.185,-.086,1.57)],
        [(.086,-.013,1.73),(.005,-.072,1.752),(-.102,-.126,1.717),(-.168,-.103,1.65),(-.187,-.045,1.59)],
        [(.081,-.045,1.72),(.125,-.114,1.689),(.158,-.128,1.624),(.171,-.096,1.57),(.166,-.071,1.51)],
    ]
    for i,points in enumerate(fringe):lock('C01_Hair_Swept_Fringe_%d'%i,points,.029 if i<3 else .023,.009,hairlight if i==1 else hair)
    # Discrete copper strands follow broad locks, preserving a soft grouped silhouette.
    for sign in (-1,1):
        for k in range(3):
            points=[(sign*(.13+.011*k),-.117+.014*k,1.67),(sign*(.18+.011*k),-.11+.014*k,1.56),(sign*(.173+.011*k),-.064+.014*k,1.45),(sign*(.19+.011*k),-.054+.014*k,1.35),(sign*(.177+.011*k),-.027+.014*k,1.25)]
            lock('C01_Hair_Copper_Accent_%s_%d'%(sign,k),points,.0015,.001,hairlight)
    for ob in objects:
        if ob.name.startswith('C01_Hair'):
            continue
        for vertex in ob.data.vertices:
            if vertex.co.z<1.49:
                vertex.co.z=1.32+(vertex.co.z-1.285)*(1.49-1.32)/(1.49-1.285)
        if ob.data.shape_keys:
            for block in ob.data.shape_keys.key_blocks:
                for vertex in block.data:
                    if vertex.co.z<1.49:
                        vertex.co.z=1.32+(vertex.co.z-1.285)*(1.49-1.32)/(1.49-1.285)
    return objects
