import numpy as np
import bpy
import bmesh
import os
import sys
import time
import mathutils
from contextlib import contextmanager


debug_trace = False

def debugprint(info):
    if debug_trace:
        print(info)

def box(width, height, depth):
    return bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0), scale=(width, height, depth))


def cylinder(radius, height, segments=100):
    return bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments, radius=radius, depth=height, location=(0, 0, 0), rotation=(0, 0, 0)
    )



def sphere(radius):
    return sl.sphere(radius)


def cone(r1, r2, height):
    return sl.cylinder(r1=r1, r2=r2, h=height)  # , center=True)


def rotate(shape, angle):
    bpy.ops.transform.rotate(value=-np.deg2rad(angle[0]), orient_axis='X', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-np.deg2rad(angle[1]), orient_axis='Y', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-np.deg2rad(angle[2]), orient_axis='Z', center_override=(0.0, 0.0, 0.0))
    return

def translate(shape, vector):

    bpy.ops.transform.translate(value=vector, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    return

def mirror(shape, plane=None):
    debugprint('mirror()')
    planes = {
        'XY': [0, 0, 1],
        'YX': [0, 0, -1],
        'XZ': [0, 1, 0],
        'ZX': [0, -1, 0],
        'YZ': [1, 0, 0],
        'ZY': [-1, 0, 0],
    }
    return sl.mirror(planes[plane])(shape)


def union(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if shape is None:
            shape = item
        else:
            shape += item
    return shape


def add(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if shape is None:
            shape = item
        else:
            shape += item
    return shape


def difference(shape, shapes):
    debugprint('difference()')
    for item in shapes:
        if item is not None:
            shape -= item
    return shape


def intersect(shape1, shape2):
    return sl.intersect()(shape1, shape2)


def hull_from_points(points):
    return sl.hull()(*points)


def hull_from_shapes(shapes, points=None):
    hs = []
    if points is not None:
        hs.extend(points)
    if shapes is not None:
        hs.extend(shapes)
    return sl.hull()(*hs)


def tess_hull(shapes, sl_tol=.5, sl_angTol=1):
    return sl.hull()(*shapes)


def triangle_hulls(shapes):
    debugprint('triangle_hulls()')
    hulls = []
    for i in range(len(shapes) - 2):
        hulls.append(hull_from_shapes(shapes[i: (i + 3)]))

    return union(hulls)


def polyline(point_list):
    return sl.polygon(point_list)


# def project_to_plate():
#     square = cq.Workplane('XY').rect(1000, 1000)
#     for wire in square.wires().objects:
#         plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))

def extrude_poly(outer_poly, inner_polys=None, height=1):
    if inner_polys is not None:
        return sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(outer_poly, *inner_polys)
    else:
        return sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(outer_poly)


def import_file(fname, convexity=5):
    print("IMPORTING FROM {}".format(fname))
    return sl.import_(fname + ".stl", convexity=convexity)


def export_file(shape, fname):
    print("EXPORTING TO {}".format(fname))
    sl.scad_render_to_file(shape, fname + ".scad")


def export_dxf(shape, fname):
    print("NO DXF EXPORT FOR SOLID".format(fname))
    pass