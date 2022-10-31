import logging
import pathlib
import sys
if sys.version_info[:2] > (3, 9):
    import importlib.resources as resources
else:
    import importlib_resources as resources

import solid as sl


def box(width, height, depth):
    return sl.cube([width, height, depth], center=True)


def cylinder(radius, height, segments=100):
    return sl.cylinder(r=radius, h=height, segments=segments, center=True)


def sphere(radius):
    return sl.sphere(radius)


def cone(r1, r2, height):
    return sl.cylinder(r1=r1, r2=r2, h=height)  # , center=True)


def rotate(shape, angle):
    if shape is None:
        return None
    return sl.rotate(angle)(shape)


def translate(shape, vector):
    if shape is None:
        return None
    return sl.translate(tuple(vector))(shape)


def mirror(shape, plane=None):
    logging.debug("mirror()")
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
    logging.debug("union()")
    shape = None
    for item in shapes:
        if item is not None:
            if shape is None:
                shape = item
            else:
                shape += item
    return shape


def add(shapes):
    logging.debug("union()")
    shape = None
    for item in shapes:
        if item is not None:
            if shape is None:
                shape = item
            else:
                shape += item
    return shape


def difference(shape, shapes):
    logging.debug("difference()")
    for item in shapes:
        if item is not None:
            shape -= item
    return shape


def intersect(shape1, shape2):
    if shape2 is not None:
        return sl.intersection()(shape1, shape2)
    else:
        return shape1


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
    logging.debug("triangle_hulls()")
    hulls = []
    for i in range(len(shapes) - 2):
        hulls.append(hull_from_shapes(shapes[i: (i + 3)]))

    return union(hulls)


def bottom_hull(p, height=0.001):
    logging.debug("bottom_hull()")
    shape = None
    for item in p:
        proj = sl.projection()(p)
        t_shape = sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(
            proj
        )
        t_shape = sl.translate([0, 0, height / 2 - 10])(t_shape)
        if shape is None:
            shape = t_shape
        shape = sl.hull()(p, shape, t_shape)
    return shape


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


def import_resource(parts_path: resources.abc.Traversable, fname: str, convexity=2):
    logging.info("IMPORTING FROM %s", fname)
    with resources.as_file(parts_path.joinpath(fname + ".stl")) as extracted:
        return sl.import_stl(str(extracted), convexity=convexity)


def import_file(fname: pathlib.Path, convexity=2):
    logging.info("IMPORTING FROM %s", fname)
    return sl.import_stl(str(fname), convexity=convexity)


def export_file(shape, fname):
    logging.info("EXPORTING TO %s", fname)
    sl.scad_render_to_file(shape, fname + ".scad")


def export_dxf(shape, fname):
    logging.warn("NO DXF EXPORT FOR SOLID %s", fname)
