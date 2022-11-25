import cadquery as cq
from scipy.spatial import ConvexHull as sphull


debug_trace = False

def debugprint(info):
    if debug_trace:
        print(info)


def box(width, height, depth):
    return 'shape'


def cylinder(radius, height, segments=100):
    return 'shape'


def sphere(radius):
    return 'shape'


def cone(r1, r2, height):
    return 'shape'


def rotate(shape, angle):
    return 'shape'


def translate(shape, vector):
    return 'shape'


def mirror(shape, plane=None):
    return 'shape'


def union(shapes):
    return 'shape'


def add(shapes):
    return 'shape'


def difference(shape, shapes):
    return 'shape'


def intersect(shape1, shape2):
    return 'shape'

def face_from_points(points):
    return 'face'


def hull_from_points(points):
    return 'shape'


def hull_from_shapes(shapes, points=None):
    return 'shape'


def tess_hull(shapes, sl_tol=.5, sl_angTol=1):
    return 'shape'


def triangle_hulls(shapes):
    return 'shape'

def bottom_hull(p, height=0.001):
    return 'shape'


def polyline(point_list):
    return 'shape'


# def project_to_plate():
#     return None


def extrude_poly(outer_poly, inner_polys=None, height=1):  # vector=(0,0,1)):
    return 'shape'


def import_file(fname, convexity=None):
    return 'shape'

def export_stl(shape, fname):
    return None

def export_file(shape, fname):
    return None

def export_dxf(shape, fname):
    return None
