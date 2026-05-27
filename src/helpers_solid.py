import solid as sl

debug_trace = False


def debugprint(info):
    if debug_trace:
        print(info)


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
        if item is not None:
            if shape is None:
                shape = item
            else:
                shape += item
    return shape


def add(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if item is not None:
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
    debugprint('triangle_hulls()')
    hulls = []
    for i in range(len(shapes) - 2):
        hulls.append(hull_from_shapes(shapes[i: (i + 3)]))

    return union(hulls)


def bottom_hull(p, height=0.001):
    debugprint("bottom_hull()")
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


def import_file(fname, convexity=2):
    print("IMPORTING FROM {}".format(fname))
    return sl.import_stl(fname.replace("\\", "/") + ".stl", convexity=convexity)


def export_file(shape, fname):
    print("EXPORTING TO {}".format(fname))
    sl.scad_render_to_file(shape, fname + ".scad")


def export_dxf(shape, fname):
    print("NO DXF EXPORT FOR SOLID".format(fname))
    pass
