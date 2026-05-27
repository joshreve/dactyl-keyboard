import cadquery as cq
from scipy.spatial import ConvexHull as sphull
import numpy as np


debug_trace = False

def debugprint(info):
    if debug_trace:
        print(info)


def box(width, height, depth):
    return cq.Workplane("XY").box(width, height, depth)


def cylinder(radius, height, segments=100):
    shape = cq.Workplane("XY").union(cq.Solid.makeCylinder(radius=radius, height=height))
    shape = translate(shape, (0, 0, -height/2))
    return shape


def sphere(radius):
    return cq.Workplane('XY').union(cq.Solid.makeSphere(radius))


def cone(r1, r2, height):
    return cq.Workplane('XY').union(
        cq.Solid.makeCone(radius1=r1, radius2=r2, height=height))


def rotate(shape, angle):
    if shape is None:
        return None
    origin = (0, 0, 0)
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(1, 0, 0), angleDegrees=angle[0])
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 1, 0), angleDegrees=angle[1])
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 0, 1), angleDegrees=angle[2])
    return shape


def translate(shape, vector):
    if shape is None:
        return None
    return shape.translate(tuple(vector))


def mirror(shape, plane=None):
    debugprint('mirror()')
    return shape.mirror(mirrorPlane=plane)


def union(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if item is not None:
            if shape is None:
                shape = item
            else:
                shape = shape.union(item)
    return shape


def add(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if item is not None:
            if shape is None:
                shape = item
            else:
                shape = shape.add(item)
    return shape


def difference(shape, shapes):
    debugprint('difference()')
    for item in shapes:
        if item is not None:
            shape = shape.cut(item)
    return shape


def intersect(shape1, shape2):
    if shape2 is not None:
        return shape1.intersect(shape2)
    else:
        return shape1

def face_from_points(points):
    # debugprint('face_from_points()')
    edges = []
    num_pnts = len(points)
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % num_pnts]
        edges.append(
            cq.Edge.makeLine(
                cq.Vector(p1[0], p1[1], p1[2]),
                cq.Vector(p2[0], p2[1], p2[2]),
            )
        )

    face = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))

    return face


def hull_from_points(points):
    # debugprint('hull_from_points()')
    hull_calc = sphull(points)
    n_faces = len(hull_calc.simplices)

    faces = []
    for i in range(n_faces):
        face_items = hull_calc.simplices[i]
        fpnts = []
        for item in face_items:
            fpnts.append(points[item])
        faces.append(face_from_points(fpnts))

    shape = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    shape = cq.Workplane('XY').union(shape)
    return shape


def hull_from_shapes(shapes, points=None):
    # debugprint('hull_from_shapes()')
    vertices = []
    for shape in shapes:
        verts = shape.vertices()
        for vert in verts.objects:
            vertices.append(np.array(vert.toTuple()))
    if points is not None:
        for point in points:
            vertices.append(np.array(point))

    shape = hull_from_points(vertices)
    return shape


def tess_hull(shapes, sl_tol=.5, sl_angTol=1):
    # debugprint('hull_from_shapes()')
    vertices = []
    solids = []
    for wp in shapes:
        for item in wp.solids().objects:
            solids.append(item)

    for shape in solids:
        verts = shape.tessellate(sl_tol, sl_angTol)[0]
        for vert in verts:
            vertices.append(np.array(vert.toTuple()))

    shape = hull_from_points(vertices)
    return shape


def triangle_hulls(shapes):
    debugprint('triangle_hulls()')
    hulls = [cq.Workplane('XY')]
    for i in range(len(shapes) - 2):
        hulls.append(hull_from_shapes(shapes[i: (i + 3)]))

    return union(hulls)





def bottom_hull(p, height=0.001):
    debugprint("bottom_hull()")
    shape = None
    for item in p:
        vertices = []
        # verts = item.faces('<Z').vertices()
        verts = item.faces().vertices()
        for vert in verts.objects:
            v0 = vert.toTuple()
            v1 = [v0[0], v0[1], -10]
            vertices.append(np.array(v0))
            vertices.append(np.array(v1))

        t_shape = hull_from_points(vertices)

        # t_shape = translate(t_shape, [0, 0, height / 2 - 10])

        if shape is None:
            shape = t_shape

        for shp in (*p, shape, t_shape):
            try:
                shp.vertices()
            except:
                0
        shape = union([shape, hull_from_shapes((shape, t_shape))])

    return shape


def polyline(point_list):
    return cq.Workplane('XY').polyline(point_list)


# def project_to_plate():
#     square = cq.Workplane('XY').rect(1000, 1000)
#     for wire in square.wires().objects:
#         plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))


def extrude_poly(outer_poly, inner_polys=None, height=1):  # vector=(0,0,1)):
    outer_wires = cq.Wire.assembleEdges(outer_poly.edges().objects)
    inner_wires = []
    if inner_polys is not None:
        for item in inner_polys:
            inner_wires.append(cq.Wire.assembleEdges(item.edges().objects))

    return cq.Workplane('XY').add(
        cq.Solid.extrudeLinear(outer_wires, inner_wires, cq.Vector(0, 0, height)))


def import_file(fname, convexity=None):
    print("IMPORTING FROM {}".format(fname))
    return cq.Workplane('XY').add(cq.importers.importShape(
        cq.exporters.ExportTypes.STEP,
        fname + ".step"))


def export_file(shape, fname):
    print("EXPORTING TO {}".format(fname))
    cq.exporters.export(w=shape, fname=fname + ".step",
                        exportType='STEP')


def export_dxf(shape, fname):
    print("EXPORTING TO {}".format(fname))
    cq.exporters.export(w=shape, fname=fname + ".dxf",
                        exportType='DXF')
