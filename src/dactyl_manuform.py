import numpy as np
from numpy import pi
import math
import os.path as path
import getopt, sys
import json
import os
from . import default_configuration
from scipy.spatial import ConvexHull as sphull


debug_exports = False
debug_trace = False
shape_config = default_configuration.shape_config
save_path = path.join(r"..", "things")
parts_path = path.join(r"..", "src", "parts")
column_style = "standard"
 
def debugprint(info):
    if debug_trace:
        print(info) 

def deg2rad(degrees: float) -> float:
    return degrees * pi / 180

def rad2deg(rad: float) -> float:
    return rad * 180 / pi

def setup(opts):
    global shape_config
    global save_path
    global parts_path
    global column_style

    with open(opts['config']['absolute_path'], mode='r') as fid:
        data = json.load(fid)
    for item in data:
        shape_config[item] = data[item]


    # Really rough setup.  Check for ENGINE, set it not present from configuration.
    try:
        print('Found Current Engine in Config = {}'.format(shape_config['ENGINE']))
    except Exception:
        print('Engine Not Found in Config')
        shape_config['ENGINE'] = 'solid'
        print('Setting Current Engine = {}'.format(shape_config['ENGINE']))

    if shape_config['save_dir'] not in ['', None, '.']:
        save_path = path.join(r"..", "things", shape_config['save_dir'])
        parts_path = path.join(r"..", r"..", "src", "parts")

    if shape_config['ENGINE'] == 'cadquery':
        from . import helpers_cadquery as helpers
    else:
        from . import helpers_solid as helpers

    column_style = shape_config['column_style']

    if shape_config['oled_mount_type'] is not None and shape_config['oled_mount_type'] != "NONE":
        for item in shape_config['oled_configurations'][shape_config['oled_mount_type']]:
            shape_config[item] = shape_config['oled_configurations'][shape_config['oled_mount_type']][item]

    if shape_config['nrows'] > 5:
        shape_config['column_style'] = shape_config['column_style_gt5']

    shape_config['centerrow'] = shape_config['nrows'] - shape_config['centerrow_offset']

    shape_config['lastrow'] = shape_config['nrows'] - 1
    shape_config['cornerrow'] = shape_config['lastrow'] - 1
    shape_config['lastcol'] = shape_config['ncols'] - 1


    # Derived values
    if shape_config['plate_style'] in ['NUB', 'HS_NUB']:
        shape_config['keyswitch_height'] = shape_config['nub_keyswitch_height']
        shape_config['keyswitch_width'] = shape_config['nub_keyswitch_width']
    elif shape_config['plate_style'] in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        shape_config['keyswitch_height'] = shape_config['undercut_keyswitch_height']
        shape_config['keyswitch_width'] = shape_config['undercut_keyswitch_width']
    else:
        shape_config['keyswitch_height'] = shape_config['hole_keyswitch_height']
        shape_config['keyswitch_width'] = shape_config['hole_keyswitch_width']

    if 'HS_' in shape_config['plate_style']:
        shape_config['symmetry'] = "asymmetric"
        shape_config['plate_file'] = path.join(parts_path, r"hot_swap_plate")
        shape_config['plate_offset'] = 0.0

    if (shape_config['trackball_in_wall'] or ('TRACKBALL' in shape_config['thumb_style'])) and not shape_config['ball_side'] == 'both':
        shape_config['symmetry'] = "asymmetric"

    shape_config['mount_width'] = shape_config['keyswitch_width'] + 2 * shape_config['plate_rim']
    shape_config['mount_height'] = shape_config['keyswitch_height'] + 2 * shape_config['plate_rim']
    shape_config['mount_thickness'] = shape_config['plate_thickness']

    if shape_config['default_1U_cluster'] and shape_config['thumb_style']=='DEFAULT':
        shape_config['double_plate_height'] = (.7*shape_config['sa_double_length'] - shape_config['mount_height']) / 3
    elif shape_config['thumb_style']=='DEFAULT':
        shape_config['double_plate_height'] = (.95*shape_config['sa_double_length'] - shape_config['mount_height']) / 3
    else:
        shape_config['double_plate_height'] = (shape_config['sa_double_length'] - shape_config['mount_height']) / 3



    if shape_config['oled_mount_type'] is not None and shape_config['oled_mount_type'] != "NONE":
        shape_config['left_wall_x_offset'] = shape_config['oled_left_wall_x_offset_override']
        shape_config['left_wall_z_offset'] = shape_config['oled_left_wall_z_offset_override']
        shape_config['left_wall_lower_y_offset'] = shape_config['oled_left_wall_lower_y_offset']
        shape_config['left_wall_lower_z_offset'] = shape_config['oled_left_wall_lower_z_offset']



    shape_config['cap_top_height'] = shape_config['plate_thickness'] + shape_config['sa_profile_key_height']
    shape_config['row_radius'] = ((shape_config['mount_height'] + shape_config['extra_height']) / 2) / (np.sin(shape_config['alpha'] / 2)) + shape_config['cap_top_height']
    shape_config['column_radius'] = (
                            ((shape_config['mount_width'] + shape_config['extra_width']) / 2) / (np.sin(shape_config['beta'] / 2))
                    ) + shape_config['cap_top_height']
    shape_config['column_x_delta'] = -1 - shape_config['column_radius'] * np.sin(shape_config['beta'])
    shape_config['column_base_angle'] = shape_config['beta'] * (shape_config['centercol'] - 2)


    shape_config['teensy_width'] = 20
    shape_config['teensy_height'] = 12
    shape_config['teensy_length'] = 33
    shape_config['teensy2_length'] = 53
    shape_config['teensy_pcb_thickness'] = 2
    shape_config['teensy_offset_height'] = 5
    shape_config['teensy_holder_top_length'] = 18
    shape_config['teensy_holder_width'] = 7 + shape_config['teensy_pcb_thickness']
    shape_config['teensy_holder_height'] = 6 + shape_config['teensy_width']


    shape_config['rj9_start'] = list(
        np.array([0, -3, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (shape_config['mount_height'] / 2), 0])),
                0,
                0,
            )
        )
    )
    rj9_position = (shape_config['rj9_start'][0], shape_config['rj9_start'][1], 11)

    shape_config['usb_holder_position'] = key_position(
        list(np.array(wall_locate2(0, 1)) + np.array([0, (shape_config['mount_height'] / 2), 0])), 1, 0
    )
    shape_config['usb_holder_size'] = [6.5, 10.0, 13.6]
    shape_config['usb_holder_thickness'] = 4


    external_start = list(
        # np.array([0, -3, 0])
        np.array([shape_config['external_holder_width'] / 2, 0, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (shape_config['mount_height'] / 2), 0])),
                0,
                0,
            )
        )
    )

    if not path.isdir(save_path):
        os.mkdir(save_path)



def column_offset(column: int) -> list:
    return column_offsets[column]

def single_plate(cylinder_segments=100, side="right"):

    if plate_style in ['NUB', 'HS_NUB']:
        tb_border = (mount_height-keyswitch_height)/2
        top_wall = box(mount_width, tb_border, plate_thickness)
        top_wall = translate(top_wall, (0, (tb_border / 2) + (keyswitch_height / 2), plate_thickness / 2))

        lr_border = (mount_width - keyswitch_width) / 2
        left_wall = box(lr_border, mount_height, plate_thickness)
        left_wall = translate(left_wall, ((lr_border / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

        side_nub = cylinder(radius=1, height=2.75)
        side_nub = rotate(side_nub, (90, 0, 0))
        side_nub = translate(side_nub, (keyswitch_width / 2, 0, 1))

        nub_cube = box(1.5, 2.75, plate_thickness)
        nub_cube = translate(nub_cube, ((1.5 / 2) + (keyswitch_width / 2),  0, plate_thickness / 2))

        side_nub2 = tess_hull(shapes=(side_nub, nub_cube))
        side_nub2 = union([side_nub2, side_nub, nub_cube])

        plate_half1 = union([top_wall, left_wall, side_nub2])
        plate_half2 = plate_half1
        plate_half2 = mirror(plate_half2, 'XZ')
        plate_half2 = mirror(plate_half2, 'YZ')

        plate = union([plate_half1, plate_half2])

    else:  # 'HOLE' or default, square cutout for non-nub designs.
        plate = box(mount_width, mount_height, mount_thickness)
        plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))

        shape_cut = box(keyswitch_width, keyswitch_height, mount_thickness * 2 +.02)
        shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness-.01))

        plate = difference(plate, [shape_cut])

    if plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        if plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
            undercut = box(
                keyswitch_width + 2 * clip_undercut,
                keyswitch_height + 2 * clip_undercut,
                mount_thickness
            )

        if plate_style in ['NOTCH', 'HS_NOTCH']:
            undercut = box(
                notch_width,
                keyswitch_height + 2 * clip_undercut,
                mount_thickness
            )
            undercut = union([undercut,
                box(
                    keyswitch_width + 2 * clip_undercut,
                    notch_width,
                    mount_thickness
                )
            ])

        undercut = translate(undercut, (0.0, 0.0, -clip_thickness + mount_thickness / 2.0))

        if ENGINE=='cadquery' and undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(undercut_transition, clip_undercut)

        plate = difference(plate, [undercut])

    if plate_file is not None:
        socket = import_file(plate_file)
        socket = translate(socket, [0, 0, plate_thickness + plate_offset])
        plate = union([plate, socket])


    if plate_holes:
        half_width = plate_holes_width/2.
        half_height = plate_holes_height/2.
        x_off = plate_holes_xy_offset[0]
        y_off = plate_holes_xy_offset[1]
        holes = [
            translate(
                cylinder(radius=plate_holes_diameter/2, height=plate_holes_depth+.01),
                (x_off+half_width, y_off+half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off-half_width, y_off+half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off-half_width, y_off-half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off+half_width, y_off-half_height, plate_holes_depth/2-.01)
            ),
        ]
        plate = difference(plate, holes)

    if side == "left":
        plate = mirror(plate, 'YZ')

    return plate

def trackball_cutout(segments=100, side="right"):
    shape = cylinder(trackball_hole_diameter / 2, trackball_hole_height)
    return shape

def trackball_socket(segments=100, side="right"):
    # shape = sphere(ball_diameter / 2)
    # cyl = cylinder(ball_diameter / 2 + 4, 20)
    # cyl = translate(cyl, (0, 0, -8))
    # shape = union([shape, cyl])

    tb_file = path.join(parts_path, r"trackball_socket_body_34mm")
    tbcut_file = path.join(parts_path, r"trackball_socket_cutter_34mm")
    sens_file = path.join(parts_path, r"trackball_sensor_mount")
    senscut_file = path.join(parts_path, r"trackball_sensor_cutter")


    # shape = import_file(tb_file)
    # # shape = difference(shape, [import_file(senscut_file)])
    # # shape = union([shape, import_file(sens_file)])
    # cutter = import_file(tbcut_file)

    shape = import_file(tb_file)
    sensor = import_file(sens_file)
    cutter = import_file(tbcut_file)
    cutter = union([cutter, import_file(senscut_file)])

    # return shape, cutter
    return shape, cutter, sensor

def trackball_ball(segments=100, side="right"):
    shape = sphere(ball_diameter / 2)
    return shape

################
## SA Keycaps ##
################




def sa_cap(Usize=1):
    # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
    # sa_length = 18.25

    if Usize == 1:
        bl2 = 18.5/2
        bw2 = 18.5/2
        m = 17 / 2
        pl2 = 6
        pw2 = 6

    elif Usize == 2:
        bl2 = sa_length
        bw2 = sa_length / 2
        m = 0
        pl2 = 16
        pw2 = 6

    elif Usize == 1.5:
        bl2 = sa_length / 2
        bw2 = 27.94 / 2
        m = 0
        pl2 = 6
        pw2 = 11

    k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
    k1 = extrude_poly(outer_poly=k1, height=0.1)
    k1 = translate(k1, (0, 0, 0.05))
    k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
    k2 = extrude_poly(outer_poly=k2, height=0.1)
    k2 = translate(k2, (0, 0, 12.0))
    if m > 0:
        m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
        m1 = extrude_poly(outer_poly=m1, height=0.1)
        m1 = translate(m1, (0, 0, 6.0))
        key_cap = hull_from_shapes((k1, k2, m1))
    else:
        key_cap = hull_from_shapes((k1, k2))

    key_cap = translate(key_cap, (0, 0, 5 + plate_thickness))

    if show_pcbs:
        key_cap = add([key_cap, key_pcb()])

    return key_cap

def key_pcb():
    shape = box(pcb_width, pcb_height, pcb_thickness)
    shape = translate(shape, (0, 0, -pcb_thickness/2))
    hole = cylinder(pcb_hole_diameter/2, pcb_thickness+.2)
    hole = translate(hole, (0, 0, -(pcb_thickness+.1)/2))
    holes = [
        translate(hole, (pcb_hole_pattern_width/2, pcb_hole_pattern_height/2, 0)),
        translate(hole, (-pcb_hole_pattern_width / 2, pcb_hole_pattern_height / 2, 0)),
        translate(hole, (-pcb_hole_pattern_width / 2, -pcb_hole_pattern_height / 2, 0)),
        translate(hole, (pcb_hole_pattern_width / 2, -pcb_hole_pattern_height / 2, 0)),
    ]
    shape = difference(shape, holes)

    return shape

#########################
## Placement Functions ##
#########################


def rotate_around_x(position, angle):
    # debugprint('rotate_around_x()')
    t_matrix = np.array(
        [
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)


def rotate_around_y(position, angle):
    # debugprint('rotate_around_y()')
    t_matrix = np.array(
        [
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)




def apply_key_geometry(
        shape,
        translate_fn,
        rotate_x_fn,
        rotate_y_fn,
        column,
        row,
        column_style=column_style,
):

    debugprint('apply_key_geometry()')

    column_angle = beta * (centercol - column)

    if column_style == "orthographic":
        column_z_delta = column_radius * (1 - np.cos(column_angle))
        shape = translate_fn(shape, [0, 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(
            shape, [-(column - centercol) * column_x_delta, 0, column_z_delta]
        )
        shape = translate_fn(shape, column_offset(column))

    elif column_style == "fixed":
        shape = rotate_y_fn(shape, fixed_angles[column])
        shape = translate_fn(shape, [fixed_x[column], 0, fixed_z[column]])
        shape = translate_fn(shape, [0, 0, -(row_radius + fixed_z[column])])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius + fixed_z[column]])
        shape = rotate_y_fn(shape, fixed_tenting)
        shape = translate_fn(shape, [0, column_offset(column)[1], 0])

    else:
        shape = translate_fn(shape, [0, 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = translate_fn(shape, [0, 0, -column_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(shape, [0, 0, column_radius])
        shape = translate_fn(shape, column_offset(column))

    shape = rotate_y_fn(shape, tenting_angle)
    shape = translate_fn(shape, [0, 0, keyboard_z_offset])

    return shape


def x_rot(shape, angle):
    # debugprint('x_rot()')
    return rotate(shape, [rad2deg(angle), 0, 0])


def y_rot(shape, angle):
    # debugprint('y_rot()')
    return rotate(shape, [0, rad2deg(angle), 0])


def key_place(shape, column, row):
    debugprint('key_place()')
    return apply_key_geometry(shape, translate, x_rot, y_rot, column, row)


def add_translate(shape, xyz):
    debugprint('add_translate()')
    vals = []
    for i in range(len(shape)):
        vals.append(shape[i] + xyz[i])
    return vals


def key_position(position, column, row):
    debugprint('key_position()')
    return apply_key_geometry(
        position, add_translate, rotate_around_x, rotate_around_y, column, row
    )


def key_holes(side="right"):
    debugprint('key_holes()')
    # hole = single_plate()
    holes = []
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                holes.append(key_place(single_plate(side=side), column, row))

    shape = union(holes)

    return shape


def caps():
    caps = None
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                if caps is None:
                    caps = key_place(sa_cap(), column, row)
                else:
                    caps = add([caps, key_place(sa_cap(), column, row)])

    return caps


####################
## Web Connectors ##
####################



def web_post():
    debugprint('web_post()')
    post = box(post_size, post_size, web_thickness)
    post = translate(post, (0, 0, plate_thickness - (web_thickness / 2)))
    return post


def web_post_tr(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0

    return translate(web_post(), ((mount_width / w_divide) - post_adj, (mount_height / 2) - post_adj, 0))


def web_post_tl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), (-(mount_width / w_divide) + post_adj, (mount_height / 2) - post_adj, 0))


def web_post_bl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), (-(mount_width / w_divide) + post_adj, -(mount_height / 2) + post_adj, 0))


def web_post_br(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), ((mount_width / w_divide) - post_adj, -(mount_height / 2) + post_adj, 0))



def connectors():
    debugprint('connectors()')
    hulls = []
    for column in range(ncols - 1):
        for row in range(lastrow):  # need to consider last_row?
            # for row in range(nrows):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_tl(), column + 1, row))
            places.append(key_place(web_post_tr(), column, row))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_br(), column, row))
            hulls.append(triangle_hulls(places))

    for column in range(ncols):
        # for row in range(nrows-1):
        for row in range(cornerrow):
            places = []
            places.append(key_place(web_post_bl(), column, row))
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tl(), column, row + 1))
            places.append(key_place(web_post_tr(), column, row + 1))
            hulls.append(triangle_hulls(places))

    for column in range(ncols - 1):
        # for row in range(nrows-1):  # need to consider last_row?
        for row in range(cornerrow):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tr(), column, row + 1))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_tl(), column + 1, row + 1))
            hulls.append(triangle_hulls(places))

    return union(hulls)


############
## Thumbs ##
############


def thumborigin():
    # debugprint('thumborigin()')
    origin = key_position([mount_width / 2, -(mount_height / 2), 0], 1, cornerrow)

    for i in range(len(origin)):
        origin[i] = origin[i] + thumb_offsets[i]

    if thumb_style == 'MINIDOX':
        origin[1] = origin[1] - .4*(trackball_Usize-1)*sa_length

    return origin


def default_thumb_tl_place(shape):
    debugprint('thumb_tl_place()')
    shape = rotate(shape, [7.5, -18, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-32.5, -14.5, -2.5])
    return shape


def default_thumb_tr_place(shape):
    debugprint('thumb_tr_place()')
    shape = rotate(shape, [10, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-12, -16, 3])
    return shape

def default_thumb_mr_place(shape):
    debugprint('thumb_mr_place()')
    shape = rotate(shape, [-6, -34, 48])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-29, -40, -13])
    return shape


def default_thumb_ml_place(shape):
    debugprint('thumb_ml_place()')
    shape = rotate(shape, [6, -34, 40])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -12])
    return shape


def default_thumb_br_place(shape):
    debugprint('thumb_br_place()')
    shape = rotate(shape, [-16, -33, 54])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-37.8, -55.3, -25.3])
    return shape


def default_thumb_bl_place(shape):
    debugprint('thumb_bl_place()')
    shape = rotate(shape, [-4, -35, 52])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-56.3, -43.3, -23.5])
    return shape


def default_thumb_1x_layout(shape, cap=False):
    debugprint('thumb_1x_layout()')
    if cap:
        shape_list = [
            default_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
            default_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
            default_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
            default_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
        ]

        if default_1U_cluster:
            shape_list.append(default_thumb_tr_place(rotate(rotate(shape, (0, 0, 90)), [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(default_thumb_tr_place(rotate(rotate(shape, (0, 0, 90)), [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(default_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])))
        shapes = add(shape_list)

    else:
        shape_list = [
                default_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
                default_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
                default_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
                default_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
            ]
        if default_1U_cluster:
            shape_list.append(default_thumb_tr_place(rotate(rotate(shape, (0, 0, 90)), [0, 0, thumb_plate_tr_rotation])))
        shapes = union(shape_list)
    return shapes


def default_thumb_15x_layout(shape, cap=False, plate=True):
    debugprint('thumb_15x_layout()')
    if plate:
        if cap:
            shape = rotate(shape, (0, 0, 90))
            cap_list = [default_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation]))]
            cap_list.append(default_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            return add(cap_list)
        else:
            shape_list = [default_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation]))]
            if not default_1U_cluster:
                shape_list.append(default_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            return union(shape_list)
    else:
        if cap:
            shape = rotate(shape, (0, 0, 90))
            shape_list = [
                default_thumb_tl_place(shape),
            ]
            shape_list.append(default_thumb_tr_place(shape))

            return add(shape_list)
        else:
            shape_list = [
                default_thumb_tl_place(shape),
            ]
            if not default_1U_cluster:
                shape_list.append(default_thumb_tr_place(shape))

            return union(shape_list)


def adjustable_plate_size(Usize=1.5):
    return (Usize * sa_length - mount_height) / 2


def adjustable_plate_half(Usize=1.5):
    debugprint('double_plate()')
    adjustable_plate_height = adjustable_plate_size(Usize)
    top_plate = box(mount_width, adjustable_plate_height, web_thickness)
    top_plate = translate(top_plate,
                          [0, (adjustable_plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
                          )
    return top_plate

def adjustable_plate(Usize=1.5):
    debugprint('double_plate()')
    top_plate = adjustable_plate_half(Usize)
    return union((top_plate, mirror(top_plate, 'XZ')))


def double_plate_half():
    debugprint('double_plate()')
    top_plate = box(mount_width, double_plate_height, web_thickness)
    top_plate = translate(top_plate,
                          [0, (double_plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
                          )
    return top_plate

def double_plate():
    debugprint('double_plate()')
    top_plate = double_plate_half()
    return union((top_plate, mirror(top_plate, 'XZ')))


def thumbcaps(side='right', style_override=None):
    if style_override is None:
        _thumb_style = thumb_style
    else:
        _thumb_style = style_override

    if _thumb_style == "MINI":
        return mini_thumbcaps()
    elif _thumb_style == "MINIDOX":
        return minidox_thumbcaps()
    elif _thumb_style == "CARBONFET":
        return carbonfet_thumbcaps()

    elif "TRACKBALL" in _thumb_style:
        if (side == ball_side or ball_side == 'both'):
            if _thumb_style == "TRACKBALL_ORBYL":
                return tbjs_thumbcaps()
            elif _thumb_style == "TRACKBALL_CJ":
                return tbcj_thumbcaps()
        else:
            return thumbcaps(side, style_override=other_thumb)

    else:
        return default_thumbcaps()


def thumb(side="right", style_override=None):
    if style_override is None:
        _thumb_style = thumb_style
    else:
        _thumb_style = style_override

    if _thumb_style == "MINI":
        return mini_thumb(side)
    elif _thumb_style == "MINIDOX":
        return minidox_thumb(side)
    elif _thumb_style == "CARBONFET":
        return carbonfet_thumb(side)

    elif "TRACKBALL" in _thumb_style:
        if (side == ball_side or ball_side == 'both'):
            if _thumb_style == "TRACKBALL_ORBYL":
                return tbjs_thumb(side)
            elif _thumb_style == "TRACKBALL_CJ":
                return tbcj_thumb(side)
        else:
            return thumb(side, style_override=other_thumb)

    else:
        return default_thumb(side)


def thumb_connectors(side='right', style_override=None):
    if style_override is None:
        _thumb_style = thumb_style
    else:
        _thumb_style = style_override

    if _thumb_style == "MINI":
        return mini_thumb_connectors()
    elif _thumb_style == "MINIDOX":
        return minidox_thumb_connectors()
    elif _thumb_style == "CARBONFET":
        return carbonfet_thumb_connectors()
      
    elif "TRACKBALL" in _thumb_style:
        if (side == ball_side or ball_side == 'both'):
            if _thumb_style == "TRACKBALL_ORBYL":
                return tbjs_thumb_connectors()
            elif _thumb_style == "TRACKBALL_CJ":
                return tbcj_thumb_connectors()
        else:
            return thumb_connectors(side, style_override=other_thumb)
          
    else:
        return default_thumb_connectors()


def default_thumbcaps():
    t1 = default_thumb_1x_layout(sa_cap(1), cap=True)
    if not default_1U_cluster:
        t1.add(default_thumb_15x_layout(sa_cap(1.5), cap=True))
    return t1


def default_thumb(side="right"):
    print('thumb()')
    shape = default_thumb_1x_layout(rotate(single_plate(side=side), (0, 0, -90)))
    shape = union([shape, default_thumb_15x_layout(rotate(single_plate(side=side), (0, 0, -90)))])
    shape = union([shape, default_thumb_15x_layout(double_plate(), plate=False)])
    return shape


def thumb_post_tr():
    debugprint('thumb_post_tr()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
                     )


def thumb_post_tl():
    debugprint('thumb_post_tl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
                     )


def thumb_post_bl():
    debugprint('thumb_post_bl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
                     )


def thumb_post_br():
    debugprint('thumb_post_br()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
                     )


def default_thumb_connectors():
    print('thumb_connectors()')
    hulls = []

    # Top two
    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tr()),
                    default_thumb_tl_place(thumb_post_br()),
                    default_thumb_tr_place(web_post_tl()),
                    default_thumb_tr_place(web_post_bl()),
                ]
            )
        )
    else:
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tr()),
                    default_thumb_tl_place(thumb_post_br()),
                    default_thumb_tr_place(thumb_post_tl()),
                    default_thumb_tr_place(thumb_post_bl()),
                ]
            )
        )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                default_thumb_br_place(web_post_tr()),
                default_thumb_br_place(web_post_br()),
                default_thumb_mr_place(web_post_tl()),
                default_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                default_thumb_br_place(web_post_tr()),
                default_thumb_br_place(web_post_br()),
                default_thumb_mr_place(web_post_tl()),
                default_thumb_mr_place(web_post_bl()),
            ]
        )
    )
    # centers of the bottom four
    hulls.append(
        triangle_hulls(
            [
                default_thumb_bl_place(web_post_tr()),
                default_thumb_bl_place(web_post_br()),
                default_thumb_ml_place(web_post_tl()),
                default_thumb_ml_place(web_post_bl()),
            ]
        )
    )

    # top two to the middle two, starting on the left
    hulls.append(
        triangle_hulls(
            [
                default_thumb_br_place(web_post_tl()),
                default_thumb_bl_place(web_post_bl()),
                default_thumb_br_place(web_post_tr()),
                default_thumb_bl_place(web_post_br()),
                default_thumb_mr_place(web_post_tl()),
                default_thumb_ml_place(web_post_bl()),
                default_thumb_mr_place(web_post_tr()),
                default_thumb_ml_place(web_post_br()),
            ]
        )
    )

    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tl()),
                    default_thumb_ml_place(web_post_tr()),
                    default_thumb_tl_place(thumb_post_bl()),
                    default_thumb_ml_place(web_post_br()),
                    default_thumb_tl_place(thumb_post_br()),
                    default_thumb_mr_place(web_post_tr()),
                    default_thumb_tr_place(web_post_bl()),
                    default_thumb_mr_place(web_post_br()),
                    default_thumb_tr_place(web_post_br()),
                ]
            )
        )
    else:
        # top two to the main keyboard, starting on the left
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tl()),
                    default_thumb_ml_place(web_post_tr()),
                    default_thumb_tl_place(thumb_post_bl()),
                    default_thumb_ml_place(web_post_br()),
                    default_thumb_tl_place(thumb_post_br()),
                    default_thumb_mr_place(web_post_tr()),
                    default_thumb_tr_place(thumb_post_bl()),
                    default_thumb_mr_place(web_post_br()),
                    default_thumb_tr_place(thumb_post_br()),
                ]
            )
        )

    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tl()),
                    key_place(web_post_bl(), 0, cornerrow),
                    default_thumb_tl_place(thumb_post_tr()),
                    key_place(web_post_br(), 0, cornerrow),
                    default_thumb_tr_place(web_post_tl()),
                    key_place(web_post_bl(), 1, cornerrow),
                    default_thumb_tr_place(web_post_tr()),
                    key_place(web_post_br(), 1, cornerrow),
                    key_place(web_post_tl(), 2, lastrow),
                    key_place(web_post_bl(), 2, lastrow),
                    default_thumb_tr_place(web_post_tr()),
                    key_place(web_post_bl(), 2, lastrow),
                    default_thumb_tr_place(web_post_br()),
                    key_place(web_post_br(), 2, lastrow),
                    key_place(web_post_bl(), 3, lastrow),
                    key_place(web_post_tr(), 2, lastrow),
                    key_place(web_post_tl(), 3, lastrow),
                    key_place(web_post_bl(), 3, cornerrow),
                    key_place(web_post_tr(), 3, lastrow),
                    key_place(web_post_br(), 3, cornerrow),
                    key_place(web_post_bl(), 4, cornerrow),
                ]
            )
        )
    else:
        hulls.append(
            triangle_hulls(
                [
                    default_thumb_tl_place(thumb_post_tl()),
                    key_place(web_post_bl(), 0, cornerrow),
                    default_thumb_tl_place(thumb_post_tr()),
                    key_place(web_post_br(), 0, cornerrow),
                    default_thumb_tr_place(thumb_post_tl()),
                    key_place(web_post_bl(), 1, cornerrow),
                    default_thumb_tr_place(thumb_post_tr()),
                    key_place(web_post_br(), 1, cornerrow),
                    key_place(web_post_tl(), 2, lastrow),
                    key_place(web_post_bl(), 2, lastrow),
                    default_thumb_tr_place(thumb_post_tr()),
                    key_place(web_post_bl(), 2, lastrow),
                    default_thumb_tr_place(thumb_post_br()),
                    key_place(web_post_br(), 2, lastrow),
                    key_place(web_post_bl(), 3, lastrow),
                    key_place(web_post_tr(), 2, lastrow),
                    key_place(web_post_tl(), 3, lastrow),
                    key_place(web_post_bl(), 3, cornerrow),
                    key_place(web_post_tr(), 3, lastrow),
                    key_place(web_post_br(), 3, cornerrow),
                    key_place(web_post_bl(), 4, cornerrow),
                ]
            )
        )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return union(hulls)

############################
# MINI THUMB CLUSTER
############################


def mini_thumb_tr_place(shape):
    shape = rotate(shape, [14, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-15, -10, 5])
    return shape


def mini_thumb_tl_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-35, -16, -2])
    return shape


def mini_thumb_mr_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-23, -34, -6])
    return shape


def mini_thumb_br_place(shape):
    shape = rotate(shape, [6, -34, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-39, -43, -16])
    return shape


def mini_thumb_bl_place(shape):
    shape = rotate(shape, [6, -32, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -11.5])
    return shape


def mini_thumb_1x_layout(shape):
    return union([
        mini_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        mini_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
        mini_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        mini_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
    ])


def mini_thumb_15x_layout(shape):
    return union([mini_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation]))])


def mini_thumbcaps():
    t1 = mini_thumb_1x_layout(sa_cap(1))
    t15 = mini_thumb_15x_layout(rotate(sa_cap(1), [0, 0, rad2deg(pi / 2)]))
    return t1.add(t15)


def mini_thumb(side="right"):
    shape = mini_thumb_1x_layout(single_plate(side=side))
    shape = union([shape, mini_thumb_15x_layout(single_plate(side=side))])

    return shape


def mini_thumb_post_tr():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, (mount_height / 2) - post_adj, 0]
    )


def mini_thumb_post_tl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, (mount_height / 2) - post_adj, 0]
    )


def mini_thumb_post_bl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, -(mount_height / 2) + post_adj, 0]
    )


def mini_thumb_post_br():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )


def mini_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                mini_thumb_tr_place(mini_thumb_post_bl()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_br_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_mr_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tl()),
                mini_thumb_bl_place(web_post_bl()),
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tr_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                mini_thumb_bl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                mini_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    return union(hulls)


############################
# MINIDOX (3-key) THUMB CLUSTER
############################

def minidox_thumb_tl_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-35, -16, -2])
    return shape

def minidox_thumb_tr_place(shape):
    shape = rotate(shape, [14, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-15, -10, 5])
    return shape

def minidox_thumb_ml_place(shape):
    shape = rotate(shape, [6, -34, 40])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-53, -26, -12])
    return shape

def minidox_thumb_mr_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-23, -34, -6])
    return shape


def minidox_thumb_bl_place(shape):
    shape = rotate(shape, [6, -32, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -11.5])
    return shape


def minidox_thumb_br_place(shape):
    shape = rotate(shape, [6, -32, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -11.5])
    return shape


def minidox_thumb_1x_layout(shape):
    return union([
        minidox_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        minidox_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        minidox_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
    ])


def minidox_thumb_fx_layout(shape):
    return union([
        minidox_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        minidox_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        minidox_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
    ])

def minidox_thumbcaps():
    t1 = minidox_thumb_1x_layout(sa_cap(1))
    # t1.add(minidox_thumb_15x_layout(rotate(sa_cap(1), [0, 0, rad2deg(pi / 2)])))
    return t1


def minidox_thumb(side="right"):

    shape = minidox_thumb_fx_layout(rotate(single_plate(side=side), [0.0, 0.0, -90]))
    shape = union([shape, minidox_thumb_fx_layout(adjustable_plate(minidox_Usize))])
    # shape = minidox_thumb_1x_layout(single_plate(side=side))



    return shape

def minidox_thumb_post_tr():
    debugprint('thumb_post_tr()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, ((mount_height/2) + adjustable_plate_size(minidox_Usize)) - post_adj, 0]
                     )


def minidox_thumb_post_tl():
    debugprint('thumb_post_tl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, ((mount_height/2) + adjustable_plate_size(minidox_Usize)) - post_adj, 0]
                     )


def minidox_thumb_post_bl():
    debugprint('thumb_post_bl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, -((mount_height/2) + adjustable_plate_size(minidox_Usize)) + post_adj, 0]
                     )


def minidox_thumb_post_br():
    debugprint('thumb_post_br()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, -((mount_height/2) + adjustable_plate_size(minidox_Usize)) + post_adj, 0]
                     )


def minidox_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                minidox_thumb_tl_place(minidox_thumb_post_tr()),
                minidox_thumb_tl_place(minidox_thumb_post_br()),
                minidox_thumb_tr_place(minidox_thumb_post_tl()),
                minidox_thumb_tr_place(minidox_thumb_post_bl()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                minidox_thumb_tl_place(minidox_thumb_post_tl()),
                minidox_thumb_tl_place(minidox_thumb_post_bl()),
                minidox_thumb_ml_place(minidox_thumb_post_tr()),
                minidox_thumb_ml_place(minidox_thumb_post_br()),
            ]
        )
    )


    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                minidox_thumb_tl_place(minidox_thumb_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                minidox_thumb_tl_place(minidox_thumb_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                minidox_thumb_tr_place(minidox_thumb_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                minidox_thumb_tr_place(minidox_thumb_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                minidox_thumb_tr_place(minidox_thumb_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                minidox_thumb_tr_place(minidox_thumb_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    return union(hulls)


############################
# Carbonfet THUMB CLUSTER
############################


def carbonfet_thumb_tl_place(shape):
    shape = rotate(shape, [10, -24, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-13, -9.8, 4])
    return shape

def carbonfet_thumb_tr_place(shape):
    shape = rotate(shape, [6, -25, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-7.5, -29.5, 0])
    return shape

def carbonfet_thumb_ml_place(shape):
    shape = rotate(shape, [8, -31, 14])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-30.5, -17, -6])
    return shape

def carbonfet_thumb_mr_place(shape):
    shape = rotate(shape, [4, -31, 14])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-22.2, -41, -10.3])
    return shape

def carbonfet_thumb_br_place(shape):
    shape = rotate(shape, [2, -37, 18])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-37, -46.4, -22])
    return shape

def carbonfet_thumb_bl_place(shape):
    shape = rotate(shape, [6, -37, 18])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-47, -23, -19])
    return shape


def carbonfet_thumb_1x_layout(shape):
    return union([
        carbonfet_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        carbonfet_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        carbonfet_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
        carbonfet_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
    ])


def carbonfet_thumb_15x_layout(shape, plate=True):
    if plate:
        return union([
            carbonfet_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
            carbonfet_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation]))
        ])
    else:
        return union([
            carbonfet_thumb_bl_place(shape),
            carbonfet_thumb_ml_place(shape)
        ])


def carbonfet_thumbcaps():
    t1 = carbonfet_thumb_1x_layout(sa_cap(1))
    t15 = carbonfet_thumb_15x_layout(rotate(sa_cap(1.5), [0, 0, rad2deg(pi / 2)]))
    return t1.add(t15)


def carbonfet_thumb(side="right"):
    shape = carbonfet_thumb_1x_layout(single_plate(side=side))
    shape = union([shape, carbonfet_thumb_15x_layout(double_plate_half(), plate=False)])
    shape = union([shape, carbonfet_thumb_15x_layout(single_plate(side=side))])

    return shape

def carbonfet_thumb_post_tr():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, (mount_height / 1.15) - post_adj, 0]
    )


def carbonfet_thumb_post_tl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, (mount_height / 1.15) - post_adj, 0]
    )


def carbonfet_thumb_post_bl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, -(mount_height / 1.15) + post_adj, 0]
    )


def carbonfet_thumb_post_br():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )

def carbonfet_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tl_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_bl_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_br_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_mr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tr_place(web_post_bl()),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tl()),
                carbonfet_thumb_bl_place(web_post_bl()),
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_tr_place(web_post_tr()),
                carbonfet_thumb_tl_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                carbonfet_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return union(hulls)


############################
# Trackball (Ball + 4-key) THUMB CLUSTER
############################

def tbjs_thumb_position_rotation():
    rot = [10, -15, 5]
    pos = thumborigin()
    # Changes size based on key diameter around ball, shifting off of the top left cluster key.
    shift = [-.9*tbjs_key_diameter/2+27-42, -.1*tbjs_key_diameter/2+3-20, -5]
    for i in range(len(pos)):
        pos[i] = pos[i] + shift[i] + tbjs_translation_offset[i]

    for i in range(len(rot)):
        rot[i] = rot[i] + tbjs_rotation_offset[i]

    return pos, rot


def tbjs_place(shape):
    pos, rot = tbjs_thumb_position_rotation()
    shape = rotate(shape, rot)
    shape = translate(shape, pos)
    return shape


def tbjs_thumb_tl_place(shape):
    debugprint('thumb_tr_place()')
    # Modifying to make a "ring" of keys
    shape = rotate(shape, [0, 0, 0])
    t_off = tbjs_key_translation_offsets[0]
    shape = rotate(shape, tbjs_key_rotation_offsets[0])
    shape = translate(shape, (t_off[0], t_off[1]+tbjs_key_diameter/2, t_off[2]))
    shape = rotate(shape, [0,0,-80])
    shape = tbjs_place(shape)
    # shape = rotate(shape, [5, 10, -65])
    # shape = translate(shape, thumborigin())
    # shape = translate(shape, [-14, -9, 0])
    return shape

def tbjs_thumb_mr_place(shape):
    debugprint('thumb_mr_place()')
    shape = rotate(shape, [0, 0, 0])
    shape = rotate(shape, tbjs_key_rotation_offsets[1])
    t_off = tbjs_key_translation_offsets[1]
    shape = translate(shape, (t_off[0], t_off[1]+tbjs_key_diameter/2, t_off[2]))
    shape = rotate(shape, [0,0,-130])
    shape = tbjs_place(shape)

    # shape = rotate(shape, [7, 20, -105])
    # shape = translate(shape, thumborigin())
    # shape = translate(shape, [-12, -32, -5])
    return shape

def tbjs_thumb_br_place(shape):
    debugprint('thumb_br_place()')

    shape = rotate(shape, [0, 0, 180])
    shape = rotate(shape, tbjs_key_rotation_offsets[2])
    t_off = tbjs_key_translation_offsets[2]
    shape = translate(shape, (t_off[0], t_off[1]+tbjs_key_diameter/2, t_off[2]))
    shape = rotate(shape, [0,0,-180])
    shape = tbjs_place(shape)

    # shape = rotate(shape, [25, -11, 0])
    # shape = translate(shape, thumborigin())
    # shape = translate(shape, [-40, -50, -16])
    return shape


def tbjs_thumb_bl_place(shape):
    debugprint('thumb_bl_place()')
    shape = rotate(shape, [0, 0, 180])
    shape = rotate(shape, tbjs_key_rotation_offsets[3])
    t_off = tbjs_key_translation_offsets[3]
    shape = translate(shape, (t_off[0], t_off[1]+tbjs_key_diameter/2, t_off[2]))
    shape = rotate(shape, [0,0,-230])
    shape = tbjs_place(shape)

    # shape = rotate(shape, [25, 0, -45])
    # shape = translate(shape, thumborigin())
    # shape = translate(shape, [-63, -41, -18])
    return shape


# def tbjs_thumb_tlold_place(shape):
#     debugprint('thumb_tl_place()')
#     shape = rotate(shape, [7.5, -10, 10])
#     shape = translate(shape, thumborigin())
#     shape = translate(shape, [-32.5, -14.5, -4])
#     return shape
#
#
# def tbjs_thumb_mlold_place(shape):
#     debugprint('thumb_ml_place()')
#     shape = rotate(shape, [6, -34, 40])
#     shape = translate(shape, thumborigin())
#     shape = translate(shape, [-51, -25, -12])
#     return shape


def tbjs_thumb_1x_layout(shape):
    return union([
        tbjs_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        # tbjs_thumb_tlold_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        # tbjs_thumb_mlold_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
        tbjs_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        tbjs_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
        tbjs_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
    ])


def tbjs_thumb_fx_layout(shape):
    return union([
        # tbjs_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        # tbjs_thumb_tlold_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        # tbjs_thumb_mlold_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
        # tbjs_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        # tbjs_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
        # tbjs_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
    ])

def trackball_layout(shape):
    return union([
        # Relocating positioning to individual parts due to complexity.
        # tbjs_place(rotate(shape, [0, 0, trackball_rotation])),
        tbjs_place(shape),
    ])


def tbjs_thumbcaps():
    t1 = tbjs_thumb_1x_layout(sa_cap(1))
    # t1.add(tbjs_thumb_15x_layout(rotate(sa_cap(1), [0, 0, rad2deg(pi / 2)])))
    return t1


def tbjs_thumb(side="right"):
    shape = tbjs_thumb_fx_layout(rotate(single_plate(side=side), [0.0, 0.0, -90]))
    shape = union([shape, tbjs_thumb_fx_layout(double_plate())])
    shape = union([shape, tbjs_thumb_1x_layout(single_plate(side=side))])

    # shape = union([shape, trackball_layout(trackball_socket())])
    # shape = tbjs_thumb_1x_layout(single_plate(side=side))
    return shape


def tbjs_thumb_post_tr():
    debugprint('thumb_post_tr()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, ((mount_height/2) + adjustable_plate_size(trackball_Usize)) - post_adj, 0]
                     )


def tbjs_thumb_post_tl():
    debugprint('thumb_post_tl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, ((mount_height/2) + adjustable_plate_size(trackball_Usize)) - post_adj, 0]
                     )


def tbjs_thumb_post_bl():
    debugprint('thumb_post_bl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, -((mount_height/2) + adjustable_plate_size(trackball_Usize)) + post_adj, 0]
                     )


def tbjs_thumb_post_br():
    debugprint('thumb_post_br()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, -((mount_height/2) + adjustable_plate_size(trackball_Usize)) + post_adj, 0]
                     )


def tbjs_post_r():
    debugprint('tbjs_post_r()')
    radius = ball_diameter/2 + ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [1.0*(radius - post_adj), 0.0*(radius - post_adj), 0]
                     )


def tbjs_post_tr():
    debugprint('tbjs_post_tr()')
    radius = ball_diameter/2+ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [0.5*(radius - post_adj), 0.866*(radius - post_adj), 0]
                     )


def tbjs_post_tl():
    debugprint('tbjs_post_tl()')
    radius = ball_diameter/2+ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [-0.5*(radius - post_adj), 0.866*(radius - post_adj), 0]
                     )


def tbjs_post_l():
    debugprint('tbjs_post_l()')
    radius = ball_diameter/2+ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [-1.0*(radius - post_adj), 0.0*(radius - post_adj), 0]
                     )

def tbjs_post_bl():
    debugprint('tbjs_post_bl()')
    radius = ball_diameter/2+ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [-0.5*(radius - post_adj), -0.866*(radius - post_adj), 0]
                     )


def tbjs_post_br():
    debugprint('tbjs_post_br()')
    radius = ball_diameter/2+ball_wall_thickness + ball_gap
    return translate(web_post(),
                     [0.5*(radius - post_adj), -0.866*(radius - post_adj), 0]
                     )



def tbjs_thumb_connectors():
    print('thumb_connectors()')
    hulls = []

    # bottom 2 to tb
    hulls.append(
        triangle_hulls(
            [
                tbjs_place(tbjs_post_l()),
                tbjs_thumb_bl_place(web_post_tl()),
                tbjs_place(tbjs_post_bl()),
                tbjs_thumb_bl_place(web_post_tr()),
                tbjs_thumb_br_place(web_post_tl()),
                tbjs_place(tbjs_post_bl()),
                tbjs_thumb_br_place(web_post_tr()),
                tbjs_place(tbjs_post_br()),
                tbjs_thumb_br_place(web_post_tr()),
                tbjs_place(tbjs_post_br()),
                tbjs_thumb_mr_place(web_post_br()),
                tbjs_place(tbjs_post_r()),
                tbjs_thumb_mr_place(web_post_bl()),
                tbjs_thumb_tl_place(web_post_br()),
                tbjs_place(tbjs_post_r()),
                tbjs_thumb_tl_place(web_post_bl()),
                tbjs_place(tbjs_post_tr()),
                key_place(web_post_bl(), 0, cornerrow),
                tbjs_place(tbjs_post_tl()),
            ]
        )
    )

    # bottom left
    hulls.append(
        triangle_hulls(
            [
                tbjs_thumb_bl_place(web_post_tr()),
                tbjs_thumb_br_place(web_post_tl()),
                tbjs_thumb_bl_place(web_post_br()),
                tbjs_thumb_br_place(web_post_bl()),
            ]
        )
    )

    # bottom right
    hulls.append(
        triangle_hulls(
            [
                tbjs_thumb_br_place(web_post_tr()),
                tbjs_thumb_mr_place(web_post_br()),
                tbjs_thumb_br_place(web_post_br()),
                tbjs_thumb_mr_place(web_post_tr()),
            ]
        )
    )
    # top right
    hulls.append(
        triangle_hulls(
            [
                tbjs_thumb_mr_place(web_post_bl()),
                tbjs_thumb_tl_place(web_post_br()),
                tbjs_thumb_mr_place(web_post_tl()),
                tbjs_thumb_tl_place(web_post_tr()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return union(hulls)





############################
# TRACKBALL THUMB CLUSTER
############################

# single_plate = the switch shape

def tbcj_thumb_tr_place(shape):
    shape = rotate(shape, [10, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-12, -16, 3])
    return shape

def tbcj_thumb_tl_place(shape):
    shape = rotate(shape, [7.5, -18, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-32.5, -14.5, -2.5])
    return shape

def tbcj_thumb_ml_place(shape):
    shape = rotate(shape, [6, -34, 40])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -12])
    return shape

def tbcj_thumb_bl_place(shape):
    shape = rotate(shape, [-4, -35, 52])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-56.3, -43.3, -23.5])
    return shape

def tbcj_thumb_layout(shape):
    return union([
            tbcj_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
            tbcj_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
            tbcj_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
            tbcj_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
            ])


#def oct_corner(i, radius, shape):
#    i = (i+1)%8
#    
#    points_x = [1, 2, 2, 1, -1, -2, -2, -1]
#    points_y = [2, 1, -1, -2, -2, -1, 1, 2]
#
#    return translate(shape, (points_x[i] * radius / 2, points_y[i] * radius / 2, 0))

def oct_corner(i, diameter, shape):
    radius = diameter / 2
    i = (i+1)%8

    r = radius
    m = radius * math.tan(math.pi / 8)
    
    points_x = [m, r, r, m, -m, -r, -r, -m]
    points_y = [r, m, -m, -r, -r, -m, m, r]

    return translate(shape, (points_x[i], points_y[i], 0))

def tbcj_edge_post(i):
    shape = box(post_size, post_size, tbcj_thickness)
    shape = oct_corner(i, tbcj_outer_diameter, shape)
    return shape

def tbcj_web_post(i):
    shape = box(post_size, post_size, tbcj_thickness)
    shape = oct_corner(i, tbcj_outer_diameter, shape)
    return shape

def tbcj_holder():
    center = box(post_size, post_size, tbcj_thickness)

    shape = []
    for i in range(8):
        shape_ = hull_from_shapes([
            center,
            tbcj_edge_post(i),
            tbcj_edge_post(i + 1),
            ])
        shape.append(shape_)
    shape = union(shape)

    shape = difference(
            shape,
            [cylinder(tbcj_inner_diameter/2, tbcj_thickness + 0.1)]
            )

    return shape

def tbcj_thumb_position_rotation():
    # loc = np.array([-15, -60, -12]) + thumborigin()
    # shape = translate(shape, loc)
    # shape = rotate(shape, (0,0,0))
    pos = np.array([-15, -60, -12]) + thumborigin()
    rot = (0,0,0)
    return pos, rot


def tbcj_place(shape):
    loc = np.array([-15, -60, -12]) + thumborigin()
    shape = translate(shape, loc)
    shape = rotate(shape, (0,0,0))
    return shape

def tbcj_thumb(side="right"):
    t = tbcj_thumb_layout(single_plate(side=side))
    tb = tbcj_place(tbcj_holder())
    return union([t, tb])

def tbcj_thumbcaps():
    t = tbcj_thumb_layout(sa_cap(1))
    return t


# TODO:  VERIFY THEY CAN BE DELETED.  THEY LOOK LIKE REPLICATES.
# def thumb_post_tr():
#     return translate(web_post(),
#                      [(mount_width / 2) - post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
#                      )
#
#
# def thumb_post_tl():
#     return translate(web_post(),
#                      [-(mount_width / 2) + post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
#                      )
#
#
# def thumb_post_bl():
#     return translate(web_post(),
#                      [-(mount_width / 2) + post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
#                      )
#
#
# def thumb_post_br():
#     return translate(web_post(),
#                      [(mount_width / 2) - post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
#                      )

def tbcj_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_tl_place(web_post_tr()),
                tbcj_thumb_tl_place(web_post_br()),
                tbcj_thumb_tr_place(web_post_tl()),
                tbcj_thumb_tr_place(web_post_bl()),
            ]
        )
    )

    # centers of the bottom four
    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_bl_place(web_post_tr()),
                tbcj_thumb_bl_place(web_post_br()),
                tbcj_thumb_ml_place(web_post_tl()),
                tbcj_thumb_ml_place(web_post_bl()),
            ]
        )
    )

    # top two to the middle two, starting on the left

    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_tl_place(web_post_tl()),
                tbcj_thumb_ml_place(web_post_tr()),
                tbcj_thumb_tl_place(web_post_bl()),
                tbcj_thumb_ml_place(web_post_br()),
                tbcj_thumb_tl_place(web_post_br()),
                tbcj_thumb_tr_place(web_post_bl()),
                tbcj_thumb_tr_place(web_post_br()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                tbcj_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                tbcj_thumb_tr_place(web_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                tbcj_thumb_tr_place(web_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                tbcj_thumb_tr_place(web_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                tbcj_thumb_tr_place(web_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                tbcj_place(tbcj_web_post(4)),
                tbcj_thumb_bl_place(web_post_bl()),
                tbcj_place(tbcj_web_post(5)),
                tbcj_thumb_bl_place(web_post_br()),
                tbcj_place(tbcj_web_post(6)),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_bl_place(web_post_br()),
                tbcj_place(tbcj_web_post(6)),
                tbcj_thumb_ml_place(web_post_bl()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                tbcj_thumb_ml_place(web_post_bl()),
                tbcj_place(tbcj_web_post(6)),
                tbcj_thumb_ml_place(web_post_br()),
                tbcj_thumb_tr_place(web_post_bl()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                tbcj_place(tbcj_web_post(6)),
                tbcj_thumb_tr_place(web_post_bl()),
                tbcj_place(tbcj_web_post(7)),
                tbcj_thumb_tr_place(web_post_br()),
                tbcj_place(tbcj_web_post(0)),
                tbcj_thumb_tr_place(web_post_br()),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    return union(hulls)



##########
## Case ##
##########

def left_key_position(row, direction, low_corner=False, side='right'):
    debugprint("left_key_position()")
    pos = np.array(
        key_position([-mount_width * 0.5, direction * mount_height * 0.5, 0], 0, row)
    )
    if trackball_in_wall and (side == ball_side or ball_side == 'both'):

        if low_corner:
            y_offset = tbiw_left_wall_lower_y_offset
            z_offset = tbiw_left_wall_lower_z_offset
        else:
            y_offset = 0.0
            z_offset = 0.0


        return list(pos - np.array([
            tbiw_left_wall_x_offset_override,
            -y_offset,
            tbiw_left_wall_z_offset_override + z_offset
        ]))

    if low_corner:
        y_offset = left_wall_lower_y_offset
        z_offset = left_wall_lower_z_offset
    else:
        y_offset = 0.0
        z_offset = 0.0

    return list(pos - np.array([left_wall_x_offset, -y_offset, left_wall_z_offset + z_offset]))


def left_key_place(shape, row, direction, low_corner=False, side='right'):
    debugprint("left_key_place()")
    pos = left_key_position(row, direction, low_corner=low_corner, side=side)
    return translate(shape, pos)


def wall_locate1(dx, dy):
    debugprint("wall_locate1()")
    return [dx * wall_thickness, dy * wall_thickness, -1]


def wall_locate2(dx, dy):
    debugprint("wall_locate2()")
    return [dx * wall_x_offset, dy * wall_y_offset, -wall_z_offset]


def wall_locate3(dx, dy, back=False):
    debugprint("wall_locate3()")
    if back:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_back_thickness),
            -wall_z_offset,
        ]
    else:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_y_thickness),
            -wall_z_offset,
        ]
    # return [
    #     dx * (wall_xy_offset + wall_thickness),
    #     dy * (wall_xy_offset + wall_thickness),
    #     -wall_z_offset,
    # ]


def wall_brace(place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
    debugprint("wall_brace()")
    hulls = []

    hulls.append(place1(post1))
    hulls.append(place1(translate(post1, wall_locate1(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))

    hulls.append(place2(post2))
    hulls.append(place2(translate(post2, wall_locate1(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
    shape1 = hull_from_shapes(hulls)

    hulls = []
    hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))
    hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
    shape2 = bottom_hull(hulls)

    return union([shape1, shape2])
    # return shape1


def key_wall_brace(x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
    debugprint("key_wall_brace()")
    return wall_brace(
        (lambda shape: key_place(shape, x1, y1)),
        dx1,
        dy1,
        post1,
        (lambda shape: key_place(shape, x2, y2)),
        dx2,
        dy2,
        post2,
        back
    )


def back_wall():
    print("back_wall()")
    x = 0
    shape = union([key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
    for i in range(ncols - 1):
        x = i + 1
        shape = union([shape, key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
        shape = union([shape, key_wall_brace(
            x, 0, 0, 1, web_post_tl(), x - 1, 0, 0, 1, web_post_tr(), back=True
        )])
    shape = union([shape, key_wall_brace(
        lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(), back=True
    )])
    return shape


def right_wall():
    print("right_wall()")
    y = 0
    shape = union([
        key_wall_brace(
            lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br()
        )
    ])

    for i in range(lastrow - 1):
        y = i + 1
        shape = union([shape, key_wall_brace(
            lastcol, y - 1, 1, 0, web_post_br(), lastcol, y, 1, 0, web_post_tr()
        )])

        shape = union([shape, key_wall_brace(
            lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br()
        )])
        #STRANGE PARTIAL OFFSET

    shape = union([
        shape,
        key_wall_brace(lastcol, cornerrow, 0, -1, web_post_br(), lastcol, cornerrow, 1, 0, web_post_br())
    ])
    return shape


def left_wall(side='right'):
    print('left_wall()')
    shape = union([wall_brace(
        (lambda sh: key_place(sh, 0, 0)), 0, 1, web_post_tl(),
        (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
    )])

    shape = union([shape, wall_brace(
        (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
        (lambda sh: left_key_place(sh, 0, 1, side=side)), -1, 0, web_post(),
    )])

    for i in range(lastrow):
        y = i
        low = (y == (lastrow-1))
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y, 1, side=side)), -1, 0, web_post(),
            (lambda sh: left_key_place(sh, y, -1, low_corner=low, side=side)), -1, 0, web_post(),
        )
        temp_shape2 = hull_from_shapes((
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y),
            left_key_place(web_post(), y, 1, side=side),
            left_key_place(web_post(), y, -1, low_corner=low, side=side),
        ))
        shape = union([shape, temp_shape1])
        shape = union([shape, temp_shape2])

    for i in range(lastrow - 1):
        y = i + 1
        low = (y == (lastrow-1))
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y - 1, -1, side=side)), -1, 0, web_post(),
            (lambda sh: left_key_place(sh, y, 1, side=side)), -1, 0, web_post(),
        )
        temp_shape2 = hull_from_shapes((
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y - 1),
            left_key_place(web_post(), y, 1, side=side),
            left_key_place(web_post(), y - 1, -1, side=side),
        ))
        shape = union([shape, temp_shape1])
        shape = union([shape, temp_shape2])

    return shape


def front_wall():
    print('front_wall()')
    shape = union([
        key_wall_brace(
            lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr()
        )
    ])
    shape = union([shape,key_wall_brace(
        3, lastrow, 0, -1, web_post_bl(), 3, lastrow, 0.5, -1, web_post_br()
    )])
    shape = union([shape,key_wall_brace(
        3, lastrow, 0.5, -1, web_post_br(), 4, cornerrow, 1, -1, web_post_bl()
    )])
    for i in range(ncols - 4):
        x = i + 4
        shape = union([shape,key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x, cornerrow, 0, -1, web_post_br()
        )])
    for i in range(ncols - 5):
        x = i + 5
        shape = union([shape, key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x - 1, cornerrow, 0, -1, web_post_br()
        )])

    return shape


def thumb_walls(side='right', style_override=None):
    if style_override is None:
        _thumb_style = thumb_style
    else:
        _thumb_style = style_override

    if _thumb_style == "MINI":
        return mini_thumb_walls()
    elif _thumb_style == "MINIDOX":
        return minidox_thumb_walls()
    elif _thumb_style == "CARBONFET":
        return carbonfet_thumb_walls()

    elif "TRACKBALL" in _thumb_style:
        if (side == ball_side or ball_side == 'both'):
            if _thumb_style == "TRACKBALL_ORBYL":
                return tbjs_thumb_walls()
            elif thumb_style == "TRACKBALL_CJ":
                return tbcj_thumb_walls()

        else:
            return thumb_walls(side, style_override=other_thumb)
    else:
        return default_thumb_walls()

def thumb_connection(side='right', style_override=None):
    if style_override is None:
        _thumb_style = thumb_style
    else:
        _thumb_style = style_override

    if _thumb_style == "MINI":
        return mini_thumb_connection(side=side)
    elif _thumb_style == "MINIDOX":
        return minidox_thumb_connection(side=side)
    elif _thumb_style == "CARBONFET":
        return carbonfet_thumb_connection(side=side)
      
    elif "TRACKBALL" in _thumb_style:
        if (side == ball_side or ball_side == 'both'):
            if _thumb_style == "TRACKBALL_ORBYL":
                return tbjs_thumb_connection(side=side)
            elif thumb_style == "TRACKBALL_CJ":
                return tbcj_thumb_connection(side=side)
        else:
            return thumb_connection(side, style_override=other_thumb)
    else:
        return default_thumb_connection(side=side)


def default_thumb_walls():
    print('thumb_walls()')
    # thumb, walls
    if default_1U_cluster:
        shape = union([wall_brace(default_thumb_mr_place, 0, -1, web_post_br(), default_thumb_tr_place, 0, -1, web_post_br())])
    else:
        shape = union([wall_brace(default_thumb_mr_place, 0, -1, web_post_br(), default_thumb_tr_place, 0, -1, thumb_post_br())])
    shape = union([shape, wall_brace(default_thumb_mr_place, 0, -1, web_post_br(), default_thumb_mr_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(default_thumb_br_place, 0, -1, web_post_br(), default_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(default_thumb_ml_place, -0.3, 1, web_post_tr(), default_thumb_ml_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(default_thumb_bl_place, 0, 1, web_post_tr(), default_thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(default_thumb_br_place, -1, 0, web_post_tl(), default_thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(default_thumb_bl_place, -1, 0, web_post_tl(), default_thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(default_thumb_br_place, -1, 0, web_post_bl(), default_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(default_thumb_bl_place, -1, 0, web_post_tl(), default_thumb_bl_place, 0, 1, web_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(default_thumb_mr_place, 0, -1, web_post_bl(), default_thumb_br_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(default_thumb_ml_place, 0, 1, web_post_tl(), default_thumb_bl_place, 0, 1, web_post_tr())])
    shape = union([shape, wall_brace(default_thumb_bl_place, -1, 0, web_post_bl(), default_thumb_br_place, -1, 0, web_post_tl())])
    if default_1U_cluster:
        shape = union([shape, wall_brace(default_thumb_tr_place, 0, -1, web_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])
    else:
        shape = union([shape, wall_brace(default_thumb_tr_place, 0, -1, thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])

    return shape


def default_thumb_connection(side='right'):
    print('thumb_connection()')
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
            [
                left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
                default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
                default_thumb_tl_place(thumb_post_tl()),
            ]
        )
    ])  # )

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            default_thumb_tl_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            key_place(web_post_bl(), 0, cornerrow),
            default_thumb_tl_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            default_thumb_ml_place(web_post_tr()),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate1(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            default_thumb_tl_place(thumb_post_tl()),
        ]
    )])

    return shape


def tbjs_thumb_connection(side='right'):
    print('thumb_connection()')
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    hulls = []
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_bl(), 0, cornerrow),
                left_key_place(web_post(), lastrow - 1, -1, side=side, low_corner=True),                # left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
                tbjs_place(tbjs_post_tl()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_bl(), 0, cornerrow),
                tbjs_thumb_tl_place(web_post_bl()),
                key_place(web_post_br(), 0, cornerrow),
                tbjs_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                tbjs_thumb_tl_place(web_post_tl()),
                key_place(web_post_br(), 1, cornerrow),
                tbjs_thumb_tl_place(web_post_tr()),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                tbjs_thumb_tl_place(web_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                tbjs_thumb_mr_place(web_post_tl()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                tbjs_thumb_mr_place(web_post_tr()),
                tbjs_thumb_mr_place(web_post_tl()),
                key_place(web_post_br(), 2, lastrow),

                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )
    shape = union(hulls)
    return shape


def tbjs_thumb_walls():
    print('thumb_walls()')
    # thumb, walls
    shape = wall_brace(
        tbjs_thumb_mr_place, .5, 1, web_post_tr(),
        (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl(),
    )
    shape = union([shape, wall_brace(
        tbjs_thumb_mr_place, .5, 1, web_post_tr(),
        tbjs_thumb_br_place, 0, -1, web_post_br(),
    )])
    shape = union([shape, wall_brace(
        tbjs_thumb_br_place, 0, -1, web_post_br(),
        tbjs_thumb_br_place, 0, -1, web_post_bl(),
    )])
    shape = union([shape, wall_brace(
        tbjs_thumb_br_place, 0, -1, web_post_bl(),
        tbjs_thumb_bl_place, 0, -1, web_post_br(),
    )])
    shape = union([shape, wall_brace(
        tbjs_thumb_bl_place, 0, -1, web_post_br(),
        tbjs_thumb_bl_place, -1, -1, web_post_bl(),
    )])

    shape = union([shape, wall_brace(
        tbjs_place, -1.5, 0, tbjs_post_tl(),
        (lambda sh: left_key_place(sh, lastrow - 1, -1, side=ball_side, low_corner=True)), -1, 0, web_post(),
    )])
    shape = union([shape, wall_brace(
        tbjs_place, -1.5, 0, tbjs_post_tl(),
        tbjs_place, -1, 0, tbjs_post_l(),
    )])
    shape = union([shape, wall_brace(
        tbjs_place, -1, 0, tbjs_post_l(),
        tbjs_thumb_bl_place, -1, 0, web_post_tl(),
    )])
    shape = union([shape, wall_brace(
        tbjs_thumb_bl_place, -1, 0, web_post_tl(),
        tbjs_thumb_bl_place, -1, -1, web_post_bl(),
    )])

    return shape


def tbcj_thumb_connection(side='right'):
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
            [
                left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
                default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
                default_thumb_tl_place(web_post_tl()),
            ]
        )
    ])  # )

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            default_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            key_place(web_post_bl(), 0, cornerrow),
            default_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            default_thumb_ml_place(web_post_tr()),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate1(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            default_thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            default_thumb_tl_place(web_post_tl()),
        ]
    )])

    return shape

def tbcj_thumb_walls():
    shape = union([wall_brace(tbcj_thumb_ml_place, -0.3, 1, web_post_tr(), tbcj_thumb_ml_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(tbcj_thumb_bl_place, 0, 1, web_post_tr(), tbcj_thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(tbcj_thumb_bl_place, -1, 0, web_post_tl(), tbcj_thumb_bl_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(tbcj_thumb_bl_place, -1, 0, web_post_tl(), tbcj_thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(tbcj_thumb_ml_place, 0, 1, web_post_tl(), tbcj_thumb_bl_place, 0, 1, web_post_tr())])

    corner = box(1,1,tbcj_thickness)

    points = [
        (tbcj_thumb_bl_place, -1, 0, web_post_bl()),
        (tbcj_place, 0, -1, tbcj_web_post(4)),
        (tbcj_place, 0, -1, tbcj_web_post(3)),
        (tbcj_place, 0, -1, tbcj_web_post(2)),
        (tbcj_place, 1, -1, tbcj_web_post(1)),
        (tbcj_place, 1, 0, tbcj_web_post(0)),
        ((lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl()),
    ]
    for i,_ in enumerate(points[:-1]):
        (pa, dxa, dya, sa) = points[i]
        (pb, dxb, dyb, sb) = points[i + 1]

        shape = union([shape, wall_brace(pa, dxa, dya, sa, pb, dxb, dyb, sb)])

    return shape


def mini_thumb_walls():
    # thumb, walls
    shape = union([wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_tr_place, 0, -1, mini_thumb_post_br())])
    shape = union([shape, wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_mr_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_br_place, 0, -1, web_post_br(), mini_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, 0, 1, web_post_tr(), mini_thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(mini_thumb_br_place, -1, 0, web_post_tl(), mini_thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(mini_thumb_br_place, -1, 0, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, 0, 1, web_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(mini_thumb_mr_place, 0, -1, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_bl(), mini_thumb_br_place, -1, 0, web_post_tl())])
    shape = union([shape, wall_brace(mini_thumb_tr_place, 0, -1, mini_thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])

    return shape

def mini_thumb_connection(side='right'):
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            key_place(web_post_bl(), 0, cornerrow),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            mini_thumb_bl_place(web_post_tr()),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate1(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    return shape

def minidox_thumb_walls():

    # thumb, walls
    shape = union([wall_brace(minidox_thumb_tr_place, 0, -1, minidox_thumb_post_br(), minidox_thumb_tr_place, 0, -1, minidox_thumb_post_bl())])
    shape = union([shape, wall_brace(minidox_thumb_tr_place, 0, -1, minidox_thumb_post_bl(), minidox_thumb_tl_place, 0, -1, minidox_thumb_post_br())])
    shape = union([shape, wall_brace(minidox_thumb_tl_place, 0, -1, minidox_thumb_post_br(), minidox_thumb_tl_place, 0, -1, minidox_thumb_post_bl())])
    shape = union([shape, wall_brace(minidox_thumb_tl_place, 0, -1, minidox_thumb_post_bl(), minidox_thumb_ml_place, -1, -1, minidox_thumb_post_br())])
    shape = union([shape, wall_brace(minidox_thumb_ml_place, -1, -1, minidox_thumb_post_br(), minidox_thumb_ml_place, 0, -1, minidox_thumb_post_bl())])
    shape = union([shape, wall_brace(minidox_thumb_ml_place, 0, -1, minidox_thumb_post_bl(), minidox_thumb_ml_place, -1, 0, minidox_thumb_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(minidox_thumb_ml_place, -1, 0, minidox_thumb_post_bl(), minidox_thumb_ml_place, -1, 0, minidox_thumb_post_tl())])
    shape = union([shape, wall_brace(minidox_thumb_ml_place, -1, 0, minidox_thumb_post_tl(), minidox_thumb_ml_place, 0, 1, minidox_thumb_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(minidox_thumb_ml_place, 0, 1, minidox_thumb_post_tr(), minidox_thumb_ml_place, 0, 1, minidox_thumb_post_tl())])
    shape = union([shape, wall_brace(minidox_thumb_tr_place, 0, -1, minidox_thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])


    return shape

def minidox_thumb_connection(side='right'):
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            minidox_thumb_bl_place(translate(minidox_thumb_post_tr(), wall_locate2(-0.3, 1))),
            minidox_thumb_bl_place(translate(minidox_thumb_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            minidox_thumb_ml_place(translate(minidox_thumb_post_tr(), wall_locate2(-0.3, 1))),
            minidox_thumb_ml_place(translate(minidox_thumb_post_tr(), wall_locate3(-0.3, 1))),
            minidox_thumb_tl_place(minidox_thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            minidox_thumb_tl_place(minidox_thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            key_place(web_post_bl(), 0, cornerrow),
            # key_place(translate(web_post_bl(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            minidox_thumb_tl_place(minidox_thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            minidox_thumb_ml_place(minidox_thumb_post_tr()),
            minidox_thumb_ml_place(translate(minidox_thumb_post_tr(), wall_locate1(0, 1))),
            minidox_thumb_ml_place(translate(minidox_thumb_post_tr(), wall_locate2(0, 1))),
            minidox_thumb_ml_place(translate(minidox_thumb_post_tr(), wall_locate3(0, 1))),
            minidox_thumb_tl_place(minidox_thumb_post_tl()),
        ]
    )])

    return shape



def carbonfet_thumb_walls():
    # thumb, walls
    shape = union([wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_tr_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_mr_place, 0, -1.15, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, 0, -1, web_post_br(), carbonfet_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -.3, 1, thumb_post_tr(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())])
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_tl(), carbonfet_thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(carbonfet_thumb_mr_place, 0, -1.15, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, -1, 0, web_post_tl())])
    shape = union([shape, wall_brace(carbonfet_thumb_tr_place, 0, -1, web_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])
    return shape

def carbonfet_thumb_connection(side='right'):
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True, side=side),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
            key_place(web_post_bl(), 0, cornerrow),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            carbonfet_thumb_bl_place(thumb_post_tr()),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate1(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    return shape

def case_walls(side='right'):
    print('case_walls()')
    return (
        union([
            back_wall(),
            left_wall(side=side),
            right_wall(),
            front_wall(),
            thumb_walls(side=side),
            thumb_connection(side=side),
        ])
    )


def rj9_cube():
    debugprint('rj9_cube()')
    shape = box(14.78, 13, 22.38)

    return shape


def rj9_space():
    debugprint('rj9_space()')
    return translate(rj9_cube(), rj9_position)


def rj9_holder():
    print('rj9_holder()')
    shape = union([translate(box(10.78, 9, 18.38), (0, 2, 0)), translate(box(10.78, 13, 5), (0, 0, 5))])
    shape = difference(rj9_cube(), [shape])
    shape = translate(shape, rj9_position)

    return shape





def usb_holder():
    print('usb_holder()')
    shape = box(
        usb_holder_size[0] + usb_holder_thickness,
        usb_holder_size[1],
        usb_holder_size[2] + usb_holder_thickness,
    )
    shape = translate(shape,
        (
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        )
    )
    return shape


def usb_holder_hole():
    debugprint('usb_holder_hole()')
    shape = box(*usb_holder_size)
    shape = translate(shape,
        (
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        )
    )
    return shape


def external_mount_hole():
    print('external_mount_hole()')
    shape = box(external_holder_width, 20.0, external_holder_height+.1)
    undercut = box(external_holder_width+8, 10.0, external_holder_height+8+.1)
    shape = union([shape, translate(undercut,(0, -5, 0))])

    shape = translate(shape,
        (
            external_start[0] + external_holder_xoffset,
            external_start[1] + external_holder_yoffset,
            external_holder_height / 2-.05,
        )
    )
    return shape

def generate_trackball(pos, rot):

    precut = trackball_cutout()
    precut = rotate(precut, tb_socket_rotation_offset)
    precut = translate(precut, tb_socket_translation_offset)
    precut = rotate(precut, rot)
    precut = translate(precut, pos)

    shape, cutout, sensor = trackball_socket()

    shape = rotate(shape, tb_socket_rotation_offset)
    shape = translate(shape, tb_socket_translation_offset)
    shape = rotate(shape, rot)
    shape = translate(shape, pos)

    cutout = rotate(cutout, tb_socket_rotation_offset)
    cutout = translate(cutout, tb_socket_translation_offset)
    # cutout = rotate(cutout, tb_sensor_translation_offset)
    # cutout = translate(cutout, tb_sensor_rotation_offset)
    cutout = rotate(cutout, rot)
    cutout = translate(cutout, pos)

    # Small adjustment due to line to line surface / minute numerical error issues
    # Creates small overlap to assist engines in union function later
    sensor = rotate(sensor, tb_socket_rotation_offset)
    sensor = translate(sensor, tb_socket_translation_offset)
    # sensor = rotate(sensor, tb_sensor_translation_offset)
    # sensor = translate(sensor, tb_sensor_rotation_offset)
    sensor = translate(sensor, (0, 0, .001))
    sensor = rotate(sensor, rot)
    sensor = translate(sensor, pos)

    ball = trackball_ball()
    ball = rotate(ball, tb_socket_rotation_offset)
    ball = translate(ball, tb_socket_translation_offset)
    ball = rotate(ball, rot)
    ball = translate(ball, pos)

    # return precut, shape, cutout, ball
    return precut, shape, cutout, sensor, ball

def generate_trackball_in_cluster():
    if thumb_style == 'TRACKBALL_ORBYL':
        pos, rot = tbjs_thumb_position_rotation()
    elif thumb_style == 'TRACKBALL_CJ':
        pos, rot = tbcj_thumb_position_rotation()
    return generate_trackball(pos, rot)



def tbiw_position_rotation():
    base_pt1 = key_position(
        list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
        0, cornerrow - tbiw_ball_center_row - 1
    )
    base_pt2 = key_position(
        list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
        0, cornerrow - tbiw_ball_center_row + 1
    )
    base_pt0 = key_position(
        list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
        0, cornerrow - tbiw_ball_center_row
    )

    left_wall_x_offset = tbiw_left_wall_x_offset_override

    tbiw_mount_location_xyz = (
            (np.array(base_pt1)+np.array(base_pt2))/2.
            + np.array(((-left_wall_x_offset/2), 0, 0))
            + np.array(tbiw_translational_offset)
    )

    # tbiw_mount_location_xyz[2] = (oled_translation_offset[2] + base_pt0[2])/2

    angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
    angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
    tbiw_mount_rotation_xyz = (rad2deg(angle_x), 0, rad2deg(angle_z)) + np.array(tbiw_rotation_offset)

    return tbiw_mount_location_xyz, tbiw_mount_rotation_xyz

def generate_trackball_in_wall():
    pos, rot = tbiw_position_rotation()
    return generate_trackball(pos, rot)



def oled_position_rotation(side='right'):
    _oled_center_row = None
    if trackball_in_wall and (side == ball_side or ball_side == 'both'):
        _oled_center_row = tbiw_oled_center_row
        _oled_translation_offset = tbiw_oled_translation_offset
        _oled_rotation_offset = tbiw_oled_rotation_offset

    elif oled_center_row is not None:
        _oled_center_row = oled_center_row
        _oled_translation_offset = oled_translation_offset
        _oled_rotation_offset = oled_rotation_offset

    if _oled_center_row is not None:
        base_pt1 = key_position(
            list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row-1
        )
        base_pt2 = key_position(
            list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row+1
        )
        base_pt0 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row
        )

        if trackball_in_wall and (side == ball_side or ball_side == 'both'):
            _left_wall_x_offset = tbiw_left_wall_x_offset_override
        else:
            _left_wall_x_offset = left_wall_x_offset

        oled_mount_location_xyz = (np.array(base_pt1)+np.array(base_pt2))/2. + np.array(((-_left_wall_x_offset/2), 0, 0)) + np.array(_oled_translation_offset)
        oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2])/2

        angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
        angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
        if trackball_in_wall and (side == ball_side or ball_side == 'both'):
            # oled_mount_rotation_xyz = (0, rad2deg(angle_x), -rad2deg(angle_z)-90) + np.array(oled_rotation_offset)
            # oled_mount_rotation_xyz = (rad2deg(angle_x)*.707, rad2deg(angle_x)*.707, -45) + np.array(oled_rotation_offset)
            oled_mount_rotation_xyz = (0, rad2deg(angle_x), -90) + np.array(_oled_rotation_offset)
        else:
            oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(_oled_rotation_offset)

    return oled_mount_location_xyz, oled_mount_rotation_xyz

def oled_sliding_mount_frame(side='right'):
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_edge_overlap_end
            + oled_edge_overlap_connector + oled_edge_overlap_clearance
            + 2 * oled_mount_rim
    )
    mount_ext_up_height = oled_mount_height + 2 * oled_mount_rim
    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height

    hole = box(mount_ext_width, mount_ext_up_height, oled_mount_cut_depth + .01)
    hole = translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

    hole_down = box(mount_ext_width, mount_ext_height, oled_mount_depth + oled_mount_cut_depth / 2)
    hole_down = translate(hole_down, (0., 0., -oled_mount_cut_depth / 4))
    hole = union([hole, hole_down])

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)

    conn_hole_start = -mount_ext_height / 2.0 + oled_mount_rim
    conn_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_connector
            + oled_edge_overlap_clearance + oled_thickness
    )
    conn_hole = box(oled_mount_width, conn_hole_length + .01, oled_mount_depth)
    conn_hole = translate(conn_hole, (
        0,
        conn_hole_start + conn_hole_length / 2,
        -oled_edge_overlap_thickness
    ))

    end_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_clearance
    )
    end_hole_start = mount_ext_height / 2.0 - oled_mount_rim - end_hole_length
    end_hole = box(oled_mount_width, end_hole_length + .01, oled_mount_depth)
    end_hole = translate(end_hole, (
        0,
        end_hole_start + end_hole_length / 2,
        -oled_edge_overlap_thickness
    ))

    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height
    top_hole = box(oled_mount_width, top_hole_length, oled_edge_overlap_thickness + oled_thickness - oled_edge_chamfer)
    top_hole = translate(top_hole, (
        0,
        top_hole_start + top_hole_length / 2,
        (oled_mount_depth - oled_edge_overlap_thickness - oled_thickness - oled_edge_chamfer) / 2.0
    ))

    top_chamfer_1 = box(
        oled_mount_width,
        top_hole_length,
        0.01
    )
    top_chamfer_2 = box(
        oled_mount_width + 2 * oled_edge_chamfer,
        top_hole_length + 2 * oled_edge_chamfer,
        0.01
    )
    top_chamfer_1 = translate(top_chamfer_1, (0, 0, -oled_edge_chamfer - .05))

    top_chamfer_1 = hull_from_shapes([top_chamfer_1, top_chamfer_2])

    top_chamfer_1 = translate(top_chamfer_1, (
        0,
        top_hole_start + top_hole_length / 2,
        oled_mount_depth / 2.0 + .05
    ))

    top_hole = union([top_hole, top_chamfer_1])

    shape = difference(shape, [conn_hole, top_hole, end_hole])

    oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )
    return hole, shape


def oled_clip_mount_frame(side='right'):
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness
            + 2 * oled_clip_undercut + 2 * oled_clip_overhang + 2 * oled_mount_rim
    )
    hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
    shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])

    clip_slot = box(
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang,
        oled_mount_depth + .1
    )

    shape = difference(shape, [clip_slot])

    clip_undercut = box(
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang + 2 * oled_clip_undercut,
        oled_mount_depth + .1
    )

    clip_undercut = translate(clip_undercut, (0., 0., oled_clip_undercut_thickness))
    shape = difference(shape, [clip_undercut])

    plate = box(
        oled_mount_width + .1,
        oled_mount_height - 2 * oled_mount_connector_hole,
        oled_mount_depth - oled_thickness
    )
    plate = translate(plate, (0., 0., -oled_thickness / 2.0))
    shape = union([shape, plate])

    oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    return hole, shape


def oled_clip():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang
            + 2 * oled_clip_undercut + 2 * oled_mount_rim
    )

    oled_leg_depth = oled_mount_depth + oled_clip_z_gap

    shape = box(mount_ext_width - .1, mount_ext_height - .1, oled_mount_bezel_thickness)
    shape = translate(shape, (0., 0., oled_mount_bezel_thickness / 2.))

    hole_1 = box(
        oled_screen_width + 2 * oled_mount_bezel_chamfer,
        oled_screen_length + 2 * oled_mount_bezel_chamfer,
        .01
    )
    hole_2 = box(oled_screen_width, oled_screen_length, 2.05 * oled_mount_bezel_thickness)
    hole = hull_from_shapes([hole_1, hole_2])

    shape = difference(shape, [translate(hole, (0., 0., oled_mount_bezel_thickness))])

    clip_leg = box(oled_clip_width, oled_clip_thickness, oled_leg_depth)
    clip_leg = translate(clip_leg, (
        0.,
        0.,
        # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
        -oled_leg_depth / 2.
    ))

    latch_1 = box(
        oled_clip_width,
        oled_clip_overhang + oled_clip_thickness,
        .01
    )
    latch_2 = box(
        oled_clip_width,
        oled_clip_thickness / 2,
        oled_clip_extension
    )
    latch_2 = translate(latch_2, (
        0.,
        -(-oled_clip_thickness / 2 + oled_clip_thickness + oled_clip_overhang) / 2,
        -oled_clip_extension / 2
    ))
    latch = hull_from_shapes([latch_1, latch_2])
    latch = translate(latch, (
        0.,
        oled_clip_overhang / 2,
        -oled_leg_depth
    ))

    clip_leg = union([clip_leg, latch])

    clip_leg = translate(clip_leg, (
        0.,
        (oled_mount_height + 2 * oled_clip_overhang + oled_clip_thickness) / 2 - oled_clip_y_gap,
        0.
    ))

    shape = union([shape, clip_leg, mirror(clip_leg, 'XZ')])

    return shape


def oled_undercut_mount_frame(side='right'):
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = oled_mount_height + 2 * oled_mount_rim
    hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
    shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])
    undercut = box(
        oled_mount_width + 2 * oled_mount_undercut,
        oled_mount_height + 2 * oled_mount_undercut,
        oled_mount_depth)
    undercut = translate(undercut, (0., 0., -oled_mount_undercut_thickness))
    shape = difference(shape, [undercut])

    oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    return hole, shape







def teensy_holder():
    print('teensy_holder()')
    teensy_top_xy = key_position(wall_locate3(-1, 0), 0, centerrow - 1)
    teensy_bot_xy = key_position(wall_locate3(-1, 0), 0, centerrow + 1)
    teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
    teensy_holder_offset = -teensy_holder_length / 2
    teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length

    s1 = box(3, teensy_holder_length, 6 + teensy_width)
    s1 = translate(s1, [1.5, teensy_holder_offset, 0])

    s2 = box(teensy_pcb_thickness, teensy_holder_length, 3)
    s2 = translate(s2,
                   (
                       (teensy_pcb_thickness / 2) + 3,
                       teensy_holder_offset,
                       -1.5 - (teensy_width / 2),
                   )
                   )

    s3 = box(teensy_pcb_thickness, teensy_holder_top_length, 3)
    s3 = translate(s3,
                   [
                       (teensy_pcb_thickness / 2) + 3,
                       teensy_holder_top_offset,
                       1.5 + (teensy_width / 2),
                   ]
                   )

    s4 = box(4, teensy_holder_top_length, 4)
    s4 = translate(s4,
                   [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
                   )

    shape = union((s1, s2, s3, s4))

    shape = translate(shape, [-teensy_holder_width, 0, 0])
    shape = translate(shape, [-1.4, 0, 0])
    shape = translate(shape,
                      [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + teensy_width) / 2]
                      )

    return shape


def screw_insert_shape(bottom_radius, top_radius, height):
    debugprint('screw_insert_shape()')
    if bottom_radius == top_radius:
        base = translate(cylinder(radius=bottom_radius, height=height),
            (0, 0, -height / 2)
        )
    else:
        base = translate(cone(r1=bottom_radius, r2=top_radius, height=height), (0, 0, -height / 2))

    shape = union((
        base,
        translate(sphere(top_radius), (0, 0, height / 2)),
    ))
    return shape


def screw_insert(column, row, bottom_radius, top_radius, height, side='right'):
    debugprint('screw_insert()')
    shift_right = column == lastcol
    shift_left = column == 0
    shift_up = (not (shift_right or shift_left)) and (row == 0)
    shift_down = (not (shift_right or shift_left)) and (row >= lastrow)

    if screws_offset == 'INSIDE':
        # debugprint('Shift Inside')
        shift_left_adjust = wall_base_x_thickness
        shift_right_adjust = -wall_base_x_thickness/2
        shift_down_adjust = -wall_base_y_thickness/2
        shift_up_adjust = -wall_base_y_thickness/3

    elif screws_offset == 'OUTSIDE':
        debugprint('Shift Outside')
        shift_left_adjust = 0
        shift_right_adjust = wall_base_x_thickness/2
        shift_down_adjust = wall_base_y_thickness*2/3
        shift_up_adjust = wall_base_y_thickness*2/3

    else:
        # debugprint('Shift Origin')
        shift_left_adjust = 0
        shift_right_adjust = 0
        shift_down_adjust = 0
        shift_up_adjust = 0

    if shift_up:
        position = key_position(
            list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2) + shift_up_adjust, 0])),
            column,
            row,
        )
    elif shift_down:
        position = key_position(
            list(np.array(wall_locate2(0, -1)) - np.array([0, (mount_height / 2) + shift_down_adjust, 0])),
            column,
            row,
        )
    elif shift_left:
        position = list(
            np.array(left_key_position(row, 0, side=side)) + np.array(wall_locate3(-1, 0)) + np.array((shift_left_adjust,0,0))
        )
    else:
        position = key_position(
            list(np.array(wall_locate2(1, 0)) + np.array([(mount_height / 2), 0, 0]) + np.array((shift_right_adjust,0,0))
                 ),
            column,
            row,
        )


    shape = screw_insert_shape(bottom_radius, top_radius, height)
    shape = translate(shape, [position[0], position[1], height / 2])

    return shape

def screw_insert_thumb(bottom_radius, top_radius, height):
    if thumb_style == 'MINI':
        position = thumborigin()
        position = list(np.array(position) + np.array([-29, -51, -16]))
        position[2] = 0

    elif thumb_style == 'MINIDOX':
        position = thumborigin()
        position = list(np.array(position) + np.array([-37, -32, -16]))
        position[1] = position[1] - .4 * (minidox_Usize - 1) * sa_length
        position[2] = 0

    elif thumb_style == 'CARBONFET':
        position = thumborigin()
        position = list(np.array(position) + np.array([-48, -37, 0]))
        position[2] = 0
    elif thumb_style == 'TRACKBALL':
        position = thumborigin()
        position = list(np.array(position) + np.array([-72, -40, -16]))
        position[2] = 0

    else:
        position = thumborigin()
        position = list(np.array(position) + np.array([-21, -58, 0]))
        position[2] = 0

    shape = screw_insert_shape(bottom_radius, top_radius, height)
    shape = translate(shape, [position[0], position[1], height / 2])
    return shape

def screw_insert_all_shapes(bottom_radius, top_radius, height, offset=0, side='right'):
    print('screw_insert_all_shapes()')
    shape = (
        translate(screw_insert(0, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
        translate(screw_insert(0, lastrow-1, bottom_radius, top_radius, height, side=side), (0, left_wall_lower_y_offset, offset)),
        translate(screw_insert(3, lastrow, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
        translate(screw_insert(3, 0, bottom_radius, top_radius, height, side=side), (0,0, offset)),
        translate(screw_insert(lastcol, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
        translate(screw_insert(lastcol, lastrow-1, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
        translate(screw_insert_thumb(bottom_radius, top_radius, height), (0, 0, offset)),
    )

    return shape




def screw_insert_holes(side='right'):
    return screw_insert_all_shapes(
        screw_insert_bottom_radius, screw_insert_top_radius, screw_insert_height+.02, offset=-.01, side=side
    )

def screw_insert_outers(side='right'):
    return screw_insert_all_shapes(
        screw_insert_bottom_radius + 1.6,
        screw_insert_top_radius + 1.6,
        screw_insert_height + 1.5,
        side=side
    )

def screw_insert_screw_holes(side='right'):
    return screw_insert_all_shapes(1.7, 1.7, 350, side=side)




def wire_post(direction, offset):
    debugprint('wire_post()')
    s1 = box(
        wire_post_diameter, wire_post_diameter, wire_post_height
    )
    s1 = translate(s1, [0, -wire_post_diameter * 0.5 * direction, 0])

    s2 = box(
        wire_post_diameter, wire_post_overhang, wire_post_diameter
    )
    s2 = translate(s2,
                   [0, -wire_post_overhang * 0.5 * direction, -wire_post_height / 2]
                   )

    shape = union((s1, s2))
    shape = translate(shape, [0, -offset, (-wire_post_height / 2) + 3])
    shape = rotate(shape, [-alpha / 2, 0, 0])
    shape = translate(shape, (3, -mount_height / 2, 0))

    return shape


def wire_posts():
    debugprint('wire_posts()')
    shape = default_thumb_ml_place(wire_post(1, 0).translate([-5, 0, -2]))
    shape = union([shape, default_thumb_ml_place(wire_post(-1, 6).translate([0, 0, -2.5]))])
    shape = union([shape, default_thumb_ml_place(wire_post(1, 0).translate([5, 0, -2]))])

    for column in range(lastcol):
        for row in range(lastrow - 1):
            shape = union([
                shape,
                key_place(wire_post(1, 0).translate([-5, 0, 0]), column, row),
                key_place(wire_post(-1, 6).translate([0, 0, 0]), column, row),
                key_place(wire_post(1, 0).translate([5, 0, 0]), column, row),
            ])
    return shape


def model_side(side="right"):
    print('model_right()')
    shape = union([key_holes(side=side)])
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_key_plates"))
    connector_shape = connectors()
    shape = union([shape, connector_shape])
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_connector_shape"))
    thumb_shape = thumb(side=side)
    if debug_exports:
        export_file(shape=thumb_shape, fname=path.join(r"..", "things", r"debug_thumb_shape"))
    shape = union([shape, thumb_shape])
    thumb_connector_shape = thumb_connectors(side=side)
    shape = union([shape, thumb_connector_shape])
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_thumb_connector_shape"))
    walls_shape = case_walls(side=side)
    if debug_exports:
        export_file(shape=walls_shape, fname=path.join(r"..", "things", r"debug_walls_shape"))
    s2 = union([walls_shape])
    s2 = union([s2, *screw_insert_outers(side=side)])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
        s2 = union([s2, teensy_holder()])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
        s2 = union([s2, usb_holder()])
        s2 = difference(s2, [usb_holder_hole()])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        s2 = difference(s2, [rj9_space()])

    if controller_mount_type in ['EXTERNAL']:
        s2 = difference(s2, [external_mount_hole()])

    if controller_mount_type in ['None']:
        0 # do nothing, only here to expressly state inaction.

    s2 = difference(s2, [union(screw_insert_holes(side=side))])
    shape = union([shape, s2])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        shape = union([shape, rj9_holder()])

    if oled_mount_type == "UNDERCUT":
        hole, frame = oled_undercut_mount_frame(side=side)
        shape = difference(shape, [hole])
        shape = union([shape, frame])

    elif oled_mount_type == "SLIDING":
        hole, frame = oled_sliding_mount_frame(side=side)
        shape = difference(shape, [hole])
        shape = union([shape, frame])

    elif oled_mount_type == "CLIP":
        hole, frame = oled_clip_mount_frame(side=side)
        shape = difference(shape, [hole])
        shape = union([shape, frame])

    if trackball_in_wall and (side == ball_side or ball_side == 'both'):
        tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_wall()

        shape = difference(shape, [tbprecut])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
        shape = union([shape, tb])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
        shape = difference(shape, [tbcutout])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
        # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
        shape = union([shape, sensor])

        if show_caps:
            shape = add([shape, ball])

    if (trackball_in_wall or ('TRACKBALL' in thumb_style)) and (side == ball_side or ball_side == 'both'):
        tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_cluster()

        shape = difference(shape, [tbprecut])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
        shape = union([shape, tb])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
        shape = difference(shape, [tbcutout])
        # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
        # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
        shape = union([shape, sensor])

        if show_caps:
            shape = add([shape, ball])

    block = box(350, 350, 40)
    block = translate(block, (0, 0, -20))
    shape = difference(shape, [block])

    if show_caps:
        shape = add([shape, thumbcaps(side=side)])
        shape = add([shape, caps()])

    if side == "left":
        shape = mirror(shape, 'YZ')

    return shape


# NEEDS TO BE SPECIAL FOR CADQUERY
def baseplate(wedge_angle=None, side='right'):
    if ENGINE == 'cadquery':
        # shape = mod_r
        shape = union([case_walls(side=side), *screw_insert_outers(side=side)])
        # tool = translate(screw_insert_screw_holes(side=side), [0, 0, -10])
        tool = screw_insert_all_shapes(screw_hole_diameter/2., screw_hole_diameter/2., 350, side=side)
        for item in tool:
            item = translate(item, [0, 0, -10])
            shape = difference(shape, [item])

        shape = translate(shape, (0, 0, -0.0001))

        square = cq.Workplane('XY').rect(1000, 1000)
        for wire in square.wires().objects:
            plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
        shape = intersect(shape, plane)

        outside = shape.vertices(cq.DirectionMinMaxSelector(cq.Vector(1, 0, 0), True)).objects[0]
        sizes = []
        max_val = 0
        inner_index = 0
        base_wires = shape.wires().objects
        for i_wire, wire in enumerate(base_wires):
            is_outside = False
            for vert in wire.Vertices():
                if vert.toTuple() == outside.toTuple():
                    outer_wire = wire
                    outer_index = i_wire
                    is_outside = True
                    sizes.append(0)
            if not is_outside:
                sizes.append(len(wire.Vertices()))
            if sizes[-1]>max_val:
                inner_index = i_wire
                max_val = sizes[-1]
        debugprint(sizes)
        inner_wire = base_wires[inner_index]

        # inner_plate = cq.Workplane('XY').add(cq.Face.makeFromWires(inner_wire))
        if wedge_angle is not None:
            cq.Workplane('XY').add(cq.Solid.revolve(outerWire, innerWires, angleDegrees, axisStart, axisEnd))
        else:
            inner_shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outerWire=inner_wire, innerWires=[], vecNormal=cq.Vector(0, 0, base_thickness)))
            inner_shape = translate(inner_shape, (0, 0, -base_rim_thickness))

            holes = []
            for i in range(len(base_wires)):
                if i not in [inner_index, outer_index]:
                    holes.append(base_wires[i])
            cutout = [*holes, inner_wire]

            shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outer_wire, cutout, cq.Vector(0, 0, base_rim_thickness)))
            hole_shapes=[]
            for hole in holes:
                loc = hole.Center()
                hole_shapes.append(
                    translate(
                        cylinder(screw_cbore_diameter/2.0, screw_cbore_depth),
                        (loc.x, loc.y, 0)
                        # (loc.x, loc.y, screw_cbore_depth/2)
                    )
                )
            shape = difference(shape, hole_shapes)
            shape = translate(shape, (0, 0, -base_rim_thickness))
            shape = union([shape, inner_shape])


        return shape
    else:

        shape = union([
            case_walls(side=side),
            *screw_insert_outers(side=side)
        ])

        tool = translate(union(screw_insert_screw_holes(side=side)), [0, 0, -10])
        base = box(1000, 1000, .01)
        shape = shape - tool
        shape = intersect(shape, base)

        shape = translate(shape, [0, 0, -0.001])

        return sl.projection(cut=True)(shape)

def run(opts):
    setup(opts)
    print(save_path)
    print(parts_path)
    exit(0)

    mod_r = model_side(side="right")
    export_file(shape=mod_r, fname=path.join(save_path, config_name + r"_right"))

    base = baseplate(side='right')
    export_file(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))
    export_dxf(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))

    if symmetry == "asymmetric":
        mod_l = model_side(side="left")
        export_file(shape=mod_l, fname=path.join(save_path, config_name + r"_left"))

        base_l = mirror(baseplate(side='left'), 'YZ')
        export_file(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))
        export_dxf(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))

    else:
        export_file(shape=mirror(mod_r, 'YZ'), fname=path.join(save_path, config_name + r"_left"))

        lbase = mirror(base, 'YZ')
        export_file(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))
        export_dxf(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))




    if oled_mount_type == 'UNDERCUT':
        export_file(shape=oled_undercut_mount_frame()[1], fname=path.join(save_path, config_name + r"_oled_undercut_test"))

    if oled_mount_type == 'SLIDING':
        export_file(shape=oled_sliding_mount_frame()[1], fname=path.join(save_path, config_name + r"_oled_sliding_test"))

    if oled_mount_type == 'CLIP':
        oled_mount_location_xyz = (0.0, 0.0, -oled_mount_depth / 2)
        oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
        export_file(shape=oled_clip(), fname=path.join(save_path, config_name + r"_oled_clip"))
        export_file(shape=oled_clip_mount_frame()[1],
                            fname=path.join(save_path, config_name + r"_oled_clip_test"))
        export_file(shape=union((oled_clip_mount_frame()[1], oled_clip())),
                            fname=path.join(save_path, config_name + r"_oled_clip_assy_test"))

# base = baseplate()
# export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))
