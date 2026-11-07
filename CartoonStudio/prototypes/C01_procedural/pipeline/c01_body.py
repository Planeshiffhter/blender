"""Original C01 clothing and body surfaces, authored as editable ring lofts.

Coordinates use metres, +Z up, and -Y forward. No downloaded character meshes.
"""
import math
import bpy
from mathutils import Vector


def build_body(collection):
    objects = []

    def material(name, color, roughness=.45, weave=False, metallic=0):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if weave:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 450
            noise.inputs['Detail'].default_value = 2
            bump = nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = .15
            bump.inputs['Distance'].default_value = .00065
            mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
            mat.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        return mat

    skin = material('C01 / warm peach skin', (.64, .33, .19), .47)
    skin.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = .075
    tee = material('C01 / cornflower cotton', (.23, .49, .78), .76, True)
    tee_trim = material('C01 / bound cotton edges', (.18, .37, .64), .78, True)
    denim = material('C01 / indigo denim', (.035, .092, .20), .79, True)
    denim_edge = material('C01 / denim seam', (.05, .13, .25), .8)
    thread = material('C01 / warm denim topstitch', (.48, .29, .13), .8)
    leather = material('C01 / ivory sneaker leather', (.88, .87, .82), .53)
    sole = material('C01 / cream rubber soles', (.72, .73, .71), .8)
    lace = material('C01 / cotton laces', (.94, .93, .88), .8)
    nail = material('C01 / natural nails', (.76, .47, .36), .3)
    brass = material('C01 / aged brass hardware', (.53, .31, .10), .3, metallic=.7)

    def mesh(name, verts, faces, mat, bind, sub=1):
        data = bpy.data.meshes.new(name)
        data.from_pydata(verts, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
        obj.data.materials.append(mat)
        obj['c01_bind'] = bind
        obj['c01_surface'] = 'authored quad loft'
        for polygon in data.polygons:
            polygon.use_smooth = True
        if sub:
            modifier = obj.modifiers.new('Surface smoothing', 'SUBSURF')
            modifier.levels = sub
            modifier.render_levels = sub
        objects.append(obj)
        return obj

    def loft(name, rings, mat, bind, sides=24, caps=True, sub=1, deform=None):
        # rings: centre xyz, local width radius, depth radius.
        verts = []
        faces = []
        for j, (center, width, depth) in enumerate(rings):
            center = Vector(center)
            first = Vector(rings[max(0,j-1)][0])
            last = Vector(rings[min(len(rings)-1,j+1)][0])
            tangent = (last-first).normalized()
            u = Vector((1,0,0))
            if abs(tangent.dot(u)) > .95:
                u = Vector((0,0,1))
            u = (u-tangent*u.dot(tangent)).normalized()
            v = tangent.cross(u).normalized()
            for i in range(sides):
                theta = 2*math.pi*i/sides
                point = center + u*(width*math.cos(theta)) + v*(depth*math.sin(theta))
                if deform:
                    point = deform(point, theta, j)
                verts.append(tuple(point))
        for j in range(len(rings)-1):
            for i in range(sides):
                a=j*sides+i; b=j*sides+(i+1)%sides
                faces.append((a,b,b+sides,a+sides))
        if caps is True:
            faces.append(tuple(range(sides-1,-1,-1)))
        if caps:
            faces.append(tuple((len(rings)-1)*sides+i for i in range(sides)))
        return mesh(name, verts, faces, mat, bind, sub)

    def line(name, points, radius, mat, bind, cyclic=False):
        data = bpy.data.curves.new(name, 'CURVE')
        data.dimensions='3D'; data.resolution_u=8
        data.bevel_depth=radius; data.bevel_resolution=2
        spline=data.splines.new('BEZIER')
        spline.bezier_points.add(len(points)-1)
        for p, co in zip(spline.bezier_points, points):
            p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
        spline.use_cyclic_u=cyclic
        obj=bpy.data.objects.new(name,data)
        collection.objects.link(obj)
        obj.data.materials.append(mat)
        # Convert so the rig can use regular vertex weights on all accessories.
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        obj=bpy.context.object
        obj['c01_bind']=bind
        for p in obj.data.polygons: p.use_smooth=True
        objects.append(obj)
        return obj

    def circle(name, center, rx, ry, radius, mat, bind, z_wave=0):
        cx,cy,cz=center
        return line(name, [(cx+rx*math.cos(t),cy+ry*math.sin(t),cz+z_wave*math.sin(t))
                          for t in [i*2*math.pi/32 for i in range(32)]],
                    radius,mat,bind,True)

    # The shirt uses variable cross-sections and an integrated neckline/shoulder slope.
    shirt_sections=[(.903,.161,.097),(.910,.162,.098),(.935,.157,.094),
                    (.980,.145,.089),(1.030,.139,.087),(1.080,.145,.091),
                    (1.130,.159,.102),(1.180,.178,.116),(1.220,.190,.112),
                    (1.258,.207,.090),(1.282,.219,.074),(1.294,.211,.069),
                    (1.313,.125,.063),(1.323,.069,.058),(1.326,.067,.057)]
    def cloth_wave(point, theta, j):
        if 2<=j<=6:
            point.y += .0018*math.sin(theta*5+j*1.4)
            point.x += .001*math.sin(theta*3+j)
        if j>=12:
            point.z += .022*math.sin(theta) # lower scooped front neckline
        return point
    loft('C01_TShirt', [((0,0,z),x,y) for z,x,y in shirt_sections], tee,'body',32,False,2,cloth_wave)
    circle('C01_TShirt_neck_binding',(0,0,1.326),.067,.057,.0035,tee_trim,'body',.022)
    circle('C01_TShirt_bottom_hem',(0,0,.911),.162,.099,.0023,tee_trim,'body')
    loft('C01_Neck',[((0,0,z),x,y) for z,x,y in
                    [(1.25,.064,.054),(1.29,.056,.050),(1.34,.050,.047),
                     (1.39,.052,.049),(1.405,.061,.054)]],skin,'body',28,True,2)

    # Jeans waist and pelvis; overlapping upper thigh sections are concealed by the hip shell.
    loft('C01_Jeans_hips',[((0,y,z),rx,ry) for z,rx,ry,y in
                          [(.793,.020,.058,.007),(.825,.130,.098,.008),
                           (.860,.180,.114,.010),(.895,.177,.107,.005),
                           (.930,.162,.099,0),(.943,.160,.097,0),(.948,.160,.097,0)]],
         denim,'body',40,False,2)
    circle('C01_Jeans_waistband_top',(0,0,.945),.161,.099,.0025,denim_edge,'body')
    circle('C01_Jeans_waistband_stitch',(0,0,.925),.165,.101,.0009,thread,'body')
    line('C01_Jeans_fly',[(-.008,-.101,.933),(-.008,-.111,.882),(-.008,-.105,.83),(.014,-.100,.812)],.0011,thread,'body')
    # A small low-poly bevelled circular button, placed flat against the denim front.
    button=loft('C01_Jeans_button', [((0,-.104+i*.001,.935),.0055,.0055) for i in (0,1,2)],brass,'body',16,True,1)

    for side, s in [('L',1),('R',-1)]:
        arm='arm.'+side; leg='leg.'+side; hand='hand.'+side; foot='foot.'+side
        # Arms have many supporting rings around elbow and wrist for deformation.
        arms=[((s*.232,0,1.278),.063,.062),((s*.251,0,1.251),.062,.060),
              ((s*.275,0,1.210),.057,.055),((s*.306,0,1.158),.049,.048),
              ((s*.345,0,1.098),.042,.043),((s*.371,0,1.061),.037,.039),
              ((s*.380,0,1.045),.035,.037),((s*.389,-.003,1.022),.036,.037),
              ((s*.402,-.008,.973),.034,.036),((s*.416,-.012,.913),.029,.031),
              ((s*.429,-.015,.853),.023,.026),((s*.433,-.016,.832),.022,.025)]
        loft('C01_Arm.'+side,list(reversed(arms)),skin,arm,24,True,2)
        sleeve=[((s*.180,0,1.305),.040,.055),((s*.210,0,1.295),.070,.075),
                ((s*.235,0,1.270),.075,.075),((s*.260,0,1.230),.069,.068),
                ((s*.275,0,1.208),.065,.064)]
        loft('C01_TShirt_sleeve.'+side,list(reversed(sleeve)),tee,arm,28,'last',2)
        # Sleeve hem follows a perpendicular ring around the arm's natural direction.
        cuff=[((s*.274,0,1.212),.066,.065),((s*.278,0,1.206),.066,.065)]
        loft('C01_TShirt_sleeve_hem.'+side,list(reversed(cuff)),tee_trim,arm,28,False,1)

        leg_sections=[(.128,.041,.041,.120,0),(.135,.043,.044,.120,0),
                      (.180,.045,.046,.120,0),(.260,.048,.049,.121,.004),
                      (.340,.052,.053,.122,.007),(.420,.055,.056,.122,.004),
                      (.495,.053,.057,.121,-.007),(.525,.053,.058,.120,-.014),
                      (.550,.056,.059,.118,-.012),(.600,.066,.068,.116,-.005),
                      (.680,.079,.081,.112,.002),(.750,.089,.088,.106,.006),
                      (.800,.092,.095,.099,.009),(.850,.091,.099,.094,.009),
                      (.880,.087,.098,.093,.008)]
        def denim_folds(point,theta,j):
            if 5<=j<=9:
                point.y += .0018*math.sin(j*2.3+theta*3)
            return point
        loft('C01_Jeans_leg.'+side,[((s*x,y,z),rx,ry) for z,rx,ry,x,y in leg_sections],denim,leg,32,False,2,denim_folds)
        circle('C01_Jeans_cuff.'+side,(s*.120,0,.138),.043,.045,.0024,denim_edge,leg)
        circle('C01_Jeans_cuff_stitch.'+side,(s*.120,0,.145),.044,.046,.0008,thread,leg)
        line('C01_Jeans_outseam.'+side,[(s*(x+rx),y,z) for z,rx,ry,x,y in leg_sections[1:-1]],.0011,thread,leg)
        # Front curved pockets, coin pocket, and back pocket topstitching.
        line('C01_Jeans_front_pocket.'+side,[(s*.059,-.096,.932),(s*.086,-.101,.899),
              (s*.117,-.093,.888),(s*.147,-.068,.899)],.0012,thread,'body')
        line('C01_Jeans_back_pocket.'+side,[(s*.042,.111,.900),(s*.127,.090,.895),
              (s*.134,.096,.829),(s*.090,.114,.808),(s*.044,.119,.830)],.00125,thread,'body')
        line('C01_Jeans_back_pocket_top.'+side,[(s*.043,.114,.889),(s*.086,.111,.887),(s*.126,.095,.884)],.0008,thread,'body')
        for x,y in ((.115,-.075),(.140,.060),(.045,.095)):
            line('C01_Jeans_belt_loop.'+side,[(s*x,y,.947),(s*(x+.001),y*1.01,.934),(s*(x+.002),y*1.02,.920)],.0028,denim_edge,'body')

        # Lofts form a tapered palm, individual fingers with knuckle rings and nails.
        loft('C01_Palm.'+side,[((s*x,y,z),rx,ry) for x,y,z,rx,ry in
                              [(.431,-.016,.857,.023,.024),(.439,-.018,.825,.027,.022),
                               (.449,-.018,.799,.038,.019),(.452,-.018,.778,.039,.017),
                               (.454,-.020,.765,.035,.014)]],skin,hand,24,True,2)
        for label,fx,tip_z in [('index',.426,.700),('middle',.446,.690),
                                ('ring',.466,.699),('pinky',.484,.718)]:
            binding='finger_'+label+'.'+side
            root_z=.772 if label!='pinky' else .766
            length=root_z-tip_z
            radius=.009 if label!='pinky' else .0076
            rings=[]
            for t,r in [(0,.85),(.10,1),(.32,.98),(.48,.93),(.55,.90),(.75,.82),(.90,.69),(.98,.40),(1,.15)]:
                x=s*(fx+.006*t)
                y=-.018-.017*t*t
                z=root_z-length*t
                rings.append(((x,y,z),radius*r,radius*r*.85))
            loft('C01_Finger_'+label+'.'+side,list(reversed(rings)),skin,binding,12,True,2)
            # A shallow convex nail patch built from its own small rounded loft.
            nz=tip_z+length*.14; nx=s*(fx+.005)
            loft('C01_Nail_'+label+'.'+side,[((nx,-.041,nz-.006),.002,.001),
                      ((nx,-.042,nz-.004),radius*.62,.0013),
                      ((nx,-.043,nz+.003),radius*.62,.0013),
                      ((nx,-.042,nz+.006),.002,.001)],nail,binding,12,True,1)
        thumb=[((s*.415,-.023,.795),.012,.011),((s*.405,-.029,.780),.011,.010),
               ((s*.398,-.035,.755),.009,.009),((s*.399,-.040,.744),.008,.008),
               ((s*.404,-.045,.732),.006,.006),((s*.405,-.046,.729),.002,.002)]
        loft('C01_Finger_thumb.'+side,list(reversed(thumb)),skin,'finger_thumb.'+side,16,True,2)

        # Sneakers: layered soles, sculpted upper, tongue, panel seams and laces.
        x=s*.120
        shoe_sections=[(.024,.049,.106,-.056),(.029,.056,.114,-.056),
                       (.040,.058,.116,-.056),(.052,.058,.116,-.056),
                       (.059,.056,.113,-.055)]
        loft('C01_Sneaker_sole.'+side,[((x,y,z),rx,ry) for z,rx,ry,y in shoe_sections],sole,foot,36,True,2)
        upper_sections=[(.052,.054,.111,-.055),(.058,.055,.111,-.055),
                        (.076,.053,.104,-.050),(.097,.050,.085,-.034),
                        (.118,.045,.059,-.010),(.139,.036,.037,.006),
                        (.144,.032,.031,.006)]
        loft('C01_Sneaker_upper.'+side,[((x,y,z),rx,ry) for z,rx,ry,y in upper_sections],leather,foot,36,True,2)
        circle('C01_Sneaker_sole_seam.'+side,(x,-.056,.049),.057,.115,.0011,lace,foot)
        line('C01_Sneaker_toecap.'+side,[(x-.047,-.105,.079),(x-.029,-.127,.087),
             (x,-.137,.089),(x+.029,-.127,.087),(x+.047,-.105,.079)],.001,sole,foot)
        # Side panel sewing, rising near heel.
        for sign in (-1,1):
            line('C01_Sneaker_panel.'+side,[(x+sign*.052,-.097,.068),
                 (x+sign*.052,-.042,.081),(x+sign*.043,.025,.105),
                 (x+sign*.031,.042,.122)],.0012,sole,foot)
        # Crossed laces follow the sloped instep. Each is real editable mesh.
        for i in range(5):
            y=-.095+i*.016
            z=.101+i*.006
            half=.025-i*.0014
            line('C01_Sneaker_lace.'+side,[(x-half,y,z),(x,y+.007,z+.004),
                 (x+half,y+.014,z+.006)],.0017,lace,foot)
            line('C01_Sneaker_lace.'+side,[(x+half,y,z),(x,y+.007,z+.005),
                 (x-half,y+.014,z+.006)],.0017,lace,foot)
        circle('C01_Sneaker_collar.'+side,(x,.006,.143),.032,.031,.0021,lace,foot)
    def weld_garment(names, result_name, binding):
        # Closing the thin garment walls before voxel union preserves the neck,
        # sleeve and ankle openings while removing intersecting pattern panels.
        panels=[obj for obj in objects if obj.name in names]
        bpy.ops.object.select_all(action='DESELECT')
        for obj in panels:
            bpy.context.view_layer.objects.active=obj
            obj.select_set(True)
            for modifier in list(obj.modifiers):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            shell=obj.modifiers.new('Sewn cloth thickness','SOLIDIFY')
            shell.thickness=.005
            shell.offset=0
            bpy.ops.object.modifier_apply(modifier=shell.name)
            obj.select_set(False)
        for obj in panels: obj.select_set(True)
        bpy.context.view_layer.objects.active=panels[0]
        bpy.ops.object.join()
        result=bpy.context.object
        result.name=result_name
        result['c01_bind']=binding
        result['c01_surface']='welded editable garment shell; voxel retopology'
        remesh=result.modifiers.new('Weld sewn pattern panels','REMESH')
        remesh.mode='VOXEL';remesh.voxel_size=.003
        remesh.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth=result.modifiers.new('Relax garment seams','SMOOTH')
        smooth.factor=.6;smooth.iterations=4
        bpy.ops.object.modifier_apply(modifier=smooth.name)
        # QuadriFlow provides a practical all-quad deformation cage instead of
        # retaining the dense voxel grid. Garment topology remains artist-reviewable.
        bpy.ops.object.quadriflow_remesh(target_faces=15000,
                use_mesh_symmetry=True,use_preserve_sharp=False,
                use_preserve_boundary=True,preserve_attributes=False,
                smooth_normals=True,seed=0)
        result['c01_surface']='welded garment shell; QuadriFlow deformation cage'
        result['retopology_target_faces']=15000
        result.data.materials.clear()
        result.data.materials.append(tee if result_name=='C01_TShirt' else denim)
        subdivision=result.modifiers.new('Garment finishing subdivision','SUBSURF')
        subdivision.levels=1;subdivision.render_levels=1
        for polygon in result.data.polygons: polygon.use_smooth=True
        for panel in panels:
            objects.remove(panel)
        objects.append(result)

    weld_garment({'C01_TShirt','C01_TShirt_sleeve.L','C01_TShirt_sleeve.R'},'C01_TShirt','body')
    weld_garment({'C01_Jeans_hips','C01_Jeans_leg.L','C01_Jeans_leg.R'},'C01_Jeans','pants')
    return objects
