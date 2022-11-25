import numpy as np
import os.path as path
import os
import copy
import importlib
from helpers import helpers_abc, freecad_that as freecad
#from shapes.plates import
from dataclasses_json import dataclass_json
from dataclasses import dataclass

# from clusters.default_cluster import DefaultCluster
# from clusters.carbonfet import CarbonfetCluster
# from clusters.mini import MiniCluster
# from clusters.minidox import MinidoxCluster
# from clusters.trackball_orbyl import TrackballOrbyl
# from clusters.trackball_wilder import TrackballWild
# from clusters.trackball_cj import TrackballCJ
# from clusters.custom_cluster import CustomCluster

# CLUSTER_LOOKUP = {
#     'DEFAULT': {'package': 'default_cluster', 'class': 'DefaultCluster'},
#     'CARBONFET': {'package': 'carbonfet', 'class': 'CarbonfetCluster'},
#     'MINI': {'package': 'mini', 'class': 'MiniCluster'},
#     'MINIDOX': {'package': 'minidox', 'class': 'MinidoxCluster'},
#     'TRACKBALL_ORBYL': {'package': 'trackball_orbyl', 'class': 'TrackballOrbyl'},
#     'TRACKBALL_WILD': {'package': 'trackball_wilder', 'class': 'TrackballWild'},
#     'TRACKBALL_CJ': {'package': 'trackball_cj', 'class': 'TrackballCJ'},
#     'TRACKBALL_CUSTOM': {'package': 'custom_cluster', 'class': 'CustomCluster'},
# }

ENGINE_LOOKUP = {
    'solid': 'helpers.helpers_solid',
    'cadquery': 'helpers.helpers_cadquery',
}


debug_exports = False
debug_trace = False
def debugprint(info):
    if debug_trace:
        print(info)


def usize_dimension(Usize=1.5):
    sa_length = 18.5
    return Usize * sa_length


# # CREATING A BASE CLASS TO USE FOR ANY PARAMETER SET WITH ACCOMPANYING FUNCTIONS.
# # NEED A BASE CLASS TO LOOK FOR TO BUILD A LIST OF AVAILABLE MODULES.
# @dataclass_json
# @dataclass
# class ParametersBase:
#     name: str = 'NONE'
#     package: str = 'dactyl_manuform'
#     class_name: str = 'Base'


class DactylBase:
    g: helpers_abc

    def __init__(self, parameters):

        self.p_base = parameters
        self.p = None
        self._walls = None
        self._dish = None
        self._thumb_walls = None
        self._thumb_dish = None

        self.sh = importlib.import_module('shapes')

        self.extra_parts = {}

        # Below is used to allow IDE autofill from helpers_abc regardless of actual imported engine.
        if self.p_base.ENGINE is not None:
            self.g = importlib.import_module(ENGINE_LOOKUP[self.p_base.ENGINE])
        else:
            self.g = helpers_abc


        if self.p_base.right_cluster is None:
            self.p_base.right_cluster = self.p_base.left_cluster
        elif self.p_base.left_cluster is None:
            self.p_base.left_cluster = self.p_base.right_cluster

        if self.p_base.right_cluster != self.p_base.left_cluster:
            self.p_base.symmetric = False

        self.cluster = None
        self.ctrl = None
        self.oled = None
        self.pl = None
        self.modules = []

        # self.p.right_thumb_style = self.p.right_cluster.thumb_style
        # self.p.left_thumb_style = self.p.left_cluster.thumb_style

    def process_parameters(self, side='right'):
        # Reset saved geometry
        self._walls = None
        self._dish = None
        self._thumb_walls = None
        self._thumb_dish = None

        self.cluster = None
        self.ctrl = None
        self.oled = None
        self.pl = None
        self.modules = []

        self.side = side

        self.p = copy.deepcopy(self.p_base)

        self.p.column_style = None

        self.p.save_name = None
        self.p.override_name = None

        self.p.parts_path = path.join(r"..", r"..", "src", "parts")

        if self.p.nrows > 5:
            self.p.column_style = self.p.column_style_gt5

        self.p.lastrow = self.p.nrows - 1
        if self.p.reduced_outer_keys:
            self.p.cornerrow = self.p.lastrow - 1
        else:
            self.p.cornerrow = self.p.lastrow
        self.p.lastcol = self.p.ncols - 1

        self.p.centerrow = self.p.nrows - self.p.centerrow_offset

        # Loaded first to set the mount dimensions based on the switch dimensions
        self.load_plates()

        # self.p.cap_top_height = self.p.plate_thickness + self.p.sa_profile_key_height
        self.p.row_radius = ((self.p.mount_height + self.p.extra_height) / 2) / (
                np.sin(self.p.alpha / 2)) + self.p.cap_top_height
        self.p.column_radius = (
                ((self.p.mount_width + self.p.extra_width) / 2) / (np.sin(self.p.beta / 2))
                ) + self.p.cap_top_height
        self.p.column_x_delta = -1 - self.p.column_radius * np.sin(self.p.beta)
        self.p.column_base_angle = self.p.beta * (self.p.centercol - 2)

        self.p.save_path = path.join("..", "things", self.p.save_dir)
        if not path.isdir(self.p.save_path):
            os.mkdir(self.p.save_path)

        if self.p.override_name in ['', None, '.']:
            if self.p.save_dir in ['', None, '.']:
                self.p.save_path = path.join(r"..", "things")
            else:
                self.p.save_path = path.join(r"..", "things", self.p.save_dir)

        else:
            self.p.save_path = path.join(self.p.save_dir, self.p.override_name)

        dir_exists = os.path.isdir(self.p.save_path)
        if not dir_exists:
            os.makedirs(self.p.save_path, exist_ok=True)

        # self.sh = PlateShapes(self)
        self.load_controller()
        self.load_cluster()
        self.load_oled()
        self.load_modules()


    def load_module(self, config):
        if config is None:
            print("NO MODULE CONFIG")
            return None
        else:
            lib = importlib.import_module(config.package)
            obj = getattr(lib, config.class_name)
            print("LOADING: {}".format(obj))
            return obj(self, config)

    def load_modules(self):
        for config in self.p.module_configs:
            self.modules.append(self.load_module(config))


    def load_cluster(self):
        if self.side == 'left':
            clust_setup = self.p.left_cluster
        else:
            clust_setup = self.p.right_cluster

        self.cluster = self.load_module(clust_setup)
        # print(self.cluster)

    def load_oled(self):
        self.oled = self.load_module(self.p.oled_config)

    def load_controller(self):
        self.ctrl = self.load_module(self.p.controller_mount_config)

    def load_plates(self):
        self.pl = self.load_module(self.p.plate_config)



    def column_offset(self, column: int) -> list:
        result = self.p.column_offsets[column]
        # if (pinky_1_5U and column == lastcol):
        #     result[0] = result[0] + 1
        return result


    #########################
    ## Placement Functions ##
    #########################

    def rotate_around_x(self, position, angle):
        # debugprint('rotate_around_x()')
        t_matrix = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)

    def rotate_around_y(self, position, angle):
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
            self,
            shape,
            translate_fn,
            rotate_x_fn,
            rotate_y_fn,
            column,
            row,
            column_style=None,
    ):
        if column_style is None:
            column_style = self.p.column_style
        debugprint('apply_key_geometry()')

        column_angle = self.p.beta * (self.p.centercol - column)

        column_x_delta_actual = self.p.column_x_delta
        if self.p.pinky_1_5U and column == self.p.lastcol:
            if self.p.first_1_5U_row <= row <= self.p.last_1_5U_row:
                column_x_delta_actual = self.p.column_x_delta - 1.5
                column_angle = self.p.beta * (self.p.centercol - column - 0.27)

        if column_style == "orthographic":
            column_z_delta = self.p.column_radius * (1 - np.cos(column_angle))
            shape = translate_fn(shape, [0, 0, -self.p.row_radius])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(
                shape, [-(column - self.p.centercol) * column_x_delta_actual, 0, column_z_delta]
            )
            shape = translate_fn(shape, self.column_offset(column))

        elif column_style == "fixed":
            shape = rotate_y_fn(shape, self.p.fixed_angles[column])
            shape = translate_fn(shape, [self.p.fixed_x[column], 0, self.p.fixed_z[column]])
            shape = translate_fn(shape, [0, 0, -(self.p.row_radius + self.p.fixed_z[column])])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius + self.p.fixed_z[column]])
            shape = rotate_y_fn(shape, self.p.fixed_tenting)
            shape = translate_fn(shape, [0, self.column_offset(column)[1], 0])

        else:
            shape = translate_fn(shape, [0, 0, -self.p.row_radius])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius])
            shape = translate_fn(shape, [0, 0, -self.p.column_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(shape, [0, 0, self.p.column_radius])
            shape = translate_fn(shape, self.column_offset(column))

        shape = rotate_y_fn(shape, self.p.tenting_angle)
        shape = translate_fn(shape, [0, 0, self.p.keyboard_z_offset])

        return shape

    def valid_key(self, column, row):
        if not self.p.reduced_outer_keys:
            return (not (column in [0, 1])) or (not row == self.p.lastrow)

        return (column in [2, 3]) or (not row == self.p.lastrow)

    def x_rot(self, shape, angle):
        # debugprint('x_rot()')
        return self.g.rotate(shape, [np.rad2deg(angle), 0, 0])

    def y_rot(self, shape, angle):
        # debugprint('y_rot()')
        return self.g.rotate(shape, [0, np.rad2deg(angle), 0])

    def key_place(self, shape, column, row):
        debugprint('key_place()')
        return self.apply_key_geometry(shape, self.g.translate, self.x_rot, self.y_rot, column, row)

    def add_translate(self, shape, xyz):
        debugprint('add_translate()')
        vals = []
        for i in range(len(shape)):
            vals.append(shape[i] + xyz[i])
        return vals

    def plate_pcb_cutouts(self):
        debugprint('plate_pcb_cutouts()')
        # hole = single_plate()
        cutouts = []
        for column in range(self.p.ncols):
            for row in range(self.p.nrows):
                if (column in [2, 3]) or (not row == self.p.lastrow):
                    cutouts.append(self.key_place(self.pl.plate_pcb_cutout(), column, row))

        return cutouts

    def key_position(self, position, column, row):
        debugprint('key_position()')
        return self.apply_key_geometry(
            position, self.add_translate, self.rotate_around_x, self.rotate_around_y, column, row
        )

    def key_holes(self):
        debugprint('key_holes()')
        holes = []
        for column in range(self.p.ncols):
            for row in range(self.p.nrows):
                if self.valid_key(column, row):
                    holes.append(self.key_place(self.pl.single_plate(), column, row))

        shape = self.g.union(holes)

        return shape

    def caps(self):
        caps = None
        for column in range(self.p.ncols):
            size = 1
            if self.p.pinky_1_5U and column == self.p.lastcol:
                if row >= self.p.first_1_5U_row and row <= self.p.last_1_5U_row:
                    size = 1.5
            for row in range(self.p.nrows):
                if self.valid_key(column, row):
                    if caps is None:
                        caps = self.key_place(self.pl.sa_cap(size), column, row)
                    else:
                        caps = self.g.add([caps, self.key_place(self.pl.sa_cap(size), column, row)])

        return caps

    def get_torow(self, column):
        torow = self.p.lastrow
        if not self.p.reduced_outer_keys:
            torow = self.p.lastrow + 1
        if column in [0, 1]:
            torow = self.p.lastrow
        return torow

    def connectors(self):
        debugprint('connectors()')
        hulls = []
        for column in range(self.p.ncols - 1):
            if (column in [2]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow + 1
            else:
                iterrows = self.p.lastrow
            for row in range(iterrows):  # need to consider last_row?
                # for row in range(nrows):  # need to consider last_row?
                places = []
                places.append(self.key_place(self.pl.web_post_tl(), column + 1, row))
                places.append(self.key_place(self.pl.web_post_tr(), column, row))
                places.append(self.key_place(self.pl.web_post_bl(), column + 1, row))
                places.append(self.key_place(self.pl.web_post_br(), column, row))
                hulls.append(self.g.triangle_hulls(places))

        for column in range(self.p.ncols):
            if (column in [2, 3]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow
            else:
                iterrows = self.p.cornerrow
            for row in range(iterrows):
                places = []
                places.append(self.key_place(self.pl.web_post_bl(), column, row))
                places.append(self.key_place(self.pl.web_post_br(), column, row))
                places.append(self.key_place(self.pl.web_post_tl(), column, row + 1))
                places.append(self.key_place(self.pl.web_post_tr(), column, row + 1))
                hulls.append(self.g.triangle_hulls(places))

        for column in range(self.p.ncols - 1):
            if (column in [2]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow
            else:
                iterrows = self.p.cornerrow
            for row in range(iterrows):
                places = []
                places.append(self.key_place(self.pl.web_post_br(), column, row))
                places.append(self.key_place(self.pl.web_post_tr(), column, row + 1))
                places.append(self.key_place(self.pl.web_post_bl(), column + 1, row))
                places.append(self.key_place(self.pl.web_post_tl(), column + 1, row + 1))
                hulls.append(self.g.triangle_hulls(places))

            if self.p.reduced_outer_keys:
                if column == 1:
                    places = []
                    places.append(self.key_place(self.pl.web_post_bl(), column + 1, iterrows))
                    places.append(self.key_place(self.pl.web_post_br(), column, iterrows))
                    places.append(self.key_place(self.pl.web_post_tl(), column + 1, iterrows + 1))
                    places.append(self.key_place(self.pl.web_post_bl(), column + 1, iterrows + 1))
                    hulls.append(self.g.triangle_hulls(places))
                if column == 3:
                    places = []
                    places.append(self.key_place(self.pl.web_post_br(), column, iterrows))
                    places.append(self.key_place(self.pl.web_post_bl(), column + 1, iterrows))
                    places.append(self.key_place(self.pl.web_post_tr(), column, iterrows + 1))
                    places.append(self.key_place(self.pl.web_post_br(), column, iterrows + 1))
                    hulls.append(self.g.triangle_hulls(places))

        return self.g.union(hulls)

    ##########
    ## Case ##
    ##########

    def left_key_position(self, row, direction, low_corner=False):
        debugprint("left_key_position()")
        pos = np.array(
            self.key_position([-self.p.mount_width * 0.5, direction * self.p.mount_height * 0.5, 0], 0, row)
        )

        if low_corner:
            x_offset = self.p.left_wall_ext_lower_x_offset
            y_offset = self.p.left_wall_ext_lower_y_offset
            z_offset = self.p.left_wall_ext_lower_z_offset
        else:
            x_offset = 0.0
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([self.p.left_wall_ext_x_offset - x_offset, -y_offset, self.p.left_wall_ext_z_offset + z_offset]))

    def left_key_place(self, shape, row, direction, low_corner=False):
        debugprint("left_key_place()")
        pos = self.left_key_position(row, direction, low_corner=low_corner)
        return self.g.translate(shape, pos)

    def wall_locate1(self, dx, dy):
        debugprint("wall_locate1()")
#        return [dx * self.p.wall_thickness, dy * self.p.wall_thickness, -1]
        return [dx * self.p.wall_thickness, dy * self.p.wall_thickness, 0]

    def wall_locate2(self, dx, dy, offsets=None):
        debugprint("wall_locate2()")
        if offsets is None:
            return [dx * self.p.wall_x_offset, dy * self.p.wall_y_offset, -self.p.wall_z_offset]
        else:
            return [
                dx * offsets[0], dy * offsets[1], -offsets[2],
            ]

    def wall_locate3(self, dx, dy, offsets=None):
        debugprint("wall_locate3()")
        if offsets is None:
            return [
                dx * (self.p.wall_x_offset + self.p.wall_base_x_thickness),
                dy * (self.p.wall_y_offset + self.p.wall_base_y_thickness),
                -self.p.wall_z_offset,
            ]
        else:
            return [
                dx * (offsets[0] + self.p.wall_base_x_thickness),
                dy * (offsets[1] + self.p.wall_base_y_thickness),
                -offsets[2],
            ]


    def wall_brace(self, place1, dx1, dy1, post1, place2, dx2, dy2, post2, wall=None, wall2=None, skeleton=False,
                   skel_bottom=False):
        debugprint("wall_brace()")
        hulls = []
        offsets12 = (
            self.p.wall_x_offset, self.p.wall_y_offset, self.p.wall_z_offset
        )
        offsets13 = (
            self.p.wall_x_offset, self.p.wall_y_offset, self.p.wall_z_offset
        )
        offsets22 = (
            self.p.wall_x_offset, self.p.wall_y_offset, self.p.wall_z_offset
        )
        offsets23 = (
            self.p.wall_x_offset, self.p.wall_y_offset, self.p.wall_z_offset
        )
        if wall in ['back']:
            offsets12 = (
                self.p.wall_x_offset,
                self.p.back_wall_y_offset,
                self.p.back_wall_z_offset
            )
            offsets13 = (
                self.p.wall_x_offset,
                self.p.back_wall_y_offset + self.p.wall_base_back_thickness-self.p.wall_base_y_thickness,
                self.p.back_wall_z_offset
            )

        if wall2 is None:
            offsets22 = offsets12
            offsets23 = offsets13
        elif wall2 in ['back']:
            offsets22 = (
                self.p.wall_x_offset,
                self.p.back_wall_y_offset,
                self.p.back_wall_z_offset
            )
            offsets23 = (
                self.p.wall_x_offset,
                self.p.back_wall_y_offset + self.p.wall_base_back_thickness-self.p.wall_base_y_thickness,
                self.p.back_wall_z_offset
            )


        hulls.append(place1(post1))
        if not skeleton:
            hulls.append(place1(self.g.translate(post1, self.wall_locate1(dx1, dy1))))
            hulls.append(place1(self.g.translate(post1, self.wall_locate2(dx1, dy1, offsets12))))
        if not skeleton or skel_bottom:
            hulls.append(place1(self.g.translate(post1, self.wall_locate3(dx1, dy1, offsets13))))

        hulls.append(place2(post2))
        if not skeleton:
            hulls.append(place2(self.g.translate(post2, self.wall_locate1(dx2, dy2))))
            hulls.append(place2(self.g.translate(post2, self.wall_locate2(dx2, dy2, offsets22))))

        if not skeleton or skel_bottom:
            hulls.append(place2(self.g.translate(post2, self.wall_locate3(dx2, dy2, offsets23))))

        shape1 = self.g.hull_from_shapes(hulls)

        hulls = []
        if not skeleton:
            hulls.append(place1(self.g.translate(post1, self.wall_locate2(dx1, dy1, offsets12))))
        if not skeleton or skel_bottom:
            hulls.append(place1(self.g.translate(post1, self.wall_locate3(dx1, dy1, offsets13))))
        if not skeleton:
            hulls.append(place2(self.g.translate(post2, self.wall_locate2(dx2, dy2, offsets22))))
        if not skeleton or skel_bottom:
            hulls.append(place2(self.g.translate(post2, self.wall_locate3(dx2, dy2, offsets23))))

        if len(hulls) > 0:
            shape2 = self.g.bottom_hull(hulls)
            shape1 = self.g.union([shape1, shape2])
            # shape1 = add([shape1, shape2])

        return shape1

    def key_wall_brace(self, x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, wall=None, wall2=None, skeleton=False,
                       skel_bottom=False):
        debugprint("key_wall_brace()")
        return self.wall_brace(
            (lambda shape: self.key_place(shape, x1, y1)),
            dx1,
            dy1,
            post1,
            (lambda shape: self.key_place(shape, x2, y2)),
            dx2,
            dy2,
            post2,
            wall=wall,
            wall2=wall2,
            skeleton=skeleton,
            skel_bottom=False,
        )

    def back_wall(self, skeleton=False):
        print("back_wall()")
        x = 0
        shape = None
        shape = self.g.union([shape, self.key_wall_brace(
            x, 0, 0, 1, self.pl.web_post_tl(),
            x, 0, 0, 1, self.pl.web_post_tr(), wall='back',
        )])
        for i in range(self.p.ncols - 1):
            x = i + 1
            shape = self.g.union([shape, self.key_wall_brace(
                x, 0, 0, 1, self.pl.web_post_tl(),
                x, 0, 0, 1, self.pl.web_post_tr(), wall='back',
            )])

            skelly = skeleton and not x == 1
            shape = self.g.union([shape, self.key_wall_brace(
                x, 0, 0, 1, self.pl.web_post_tl(),
                x - 1, 0, 0, 1, self.pl.web_post_tr(), wall='back',
                skeleton=skelly, skel_bottom=True,
            )])

        if not skeleton:
            shape = self.g.union([shape,  self.key_wall_brace(
                self.p.lastcol, 0, 0, 1, self.pl.web_post_tr(),
                self.p.lastcol, 0, 1, 0, self.pl.web_post_tr(),
                wall='back', wall2='right'
            )])
        return shape

    def right_wall(self, skeleton=False):
        print("right_wall()")
        y = 0

        shape = None

        shape = self.g.union([shape, self.key_wall_brace(
            self.p.lastcol, y, 1, 0, self.pl.web_post_tr(),
            self.p.lastcol, y, 1, 0, self.pl.web_post_br(),
            skeleton=skeleton,
        )])

        for i in range(self.p.cornerrow):
            y = i + 1
            shape = self.g.union([shape, self.key_wall_brace(
                self.p.lastcol, y - 1, 1, 0, self.pl.web_post_br(),
                self.p.lastcol, y, 1, 0, self.pl.web_post_tr(),
                skeleton=skeleton,
            )])

            shape = self.g.union([shape, self.key_wall_brace(
                self.p.lastcol, y, 1, 0, self.pl.web_post_tr(),
                self.p.lastcol, y, 1, 0, self.pl.web_post_br(),
                skeleton=skeleton,
            )])
            # STRANGE PARTIAL OFFSET

        shape = self.g.union([
            shape,
            self.key_wall_brace(
                self.p.lastcol, self.p.cornerrow, 0, -1, self.pl.web_post_br(),
                self.p.lastcol, self.p.cornerrow, 1, 0, self.pl.web_post_br(),
                skeleton=skeleton
            ),
        ])

        return shape

    def left_wall(self, skeleton=False):
        print('left_wall()')
        shape = self.g.union([self.wall_brace(
            (lambda sh: self.key_place(sh, 0, 0)), 0, 1, self.pl.web_post_tl(),
            (lambda sh: self.left_key_place(sh, 0, 1)), 0, 1, self.pl.web_post(),
            wall='back',
        )])

        shape = self.g.union([shape, self.wall_brace(
            (lambda sh: self.left_key_place(sh, 0, 1)), 0, 1, self.pl.web_post(),
            (lambda sh: self.left_key_place(sh, 0, 1)), -1, 0, self.pl.web_post(),
            wall='back', wall2='left',
            skeleton=skeleton,
        )])

        # for i in range(lastrow):
        for i in range(self.p.cornerrow + 1):
            y = i
            low = (y == (self.p.cornerrow))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.left_key_place(sh, y, 1)), -1, 0, self.pl.web_post(),
                (lambda sh: self.left_key_place(sh, y, -1, low_corner=low)), -1, 0, self.pl.web_post(),
                skeleton=skeleton and (y < (self.p.cornerrow)),
            )
            shape = self.g.union([shape, temp_shape1])

            temp_shape2 = self.g.hull_from_shapes((
                self.key_place(self.pl.web_post_tl(), 0, y),
                self.key_place(self.pl.web_post_bl(), 0, y),
                self.left_key_place(self.pl.web_post(), y, 1),
                self.left_key_place(self.pl.web_post(), y, -1, low_corner=low),
            ))

            shape = self.g.union([shape, temp_shape2])

        for i in range(self.p.cornerrow):
            y = i + 1
            low = (y == (self.p.cornerrow))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.left_key_place(sh, y - 1, -1)), -1, 0, self.pl.web_post(),
                (lambda sh: self.left_key_place(sh, y, 1)), -1, 0, self.pl.web_post(),
                skeleton=skeleton and (y < (self.p.cornerrow)),
            )
            shape = self.g.union([shape, temp_shape1])

            temp_shape2 = self.g.hull_from_shapes((
                self.key_place(self.pl.web_post_tl(), 0, y),
                self.key_place(self.pl.web_post_bl(), 0, y - 1),
                self.left_key_place(self.pl.web_post(), y, 1),
                self.left_key_place(self.pl.web_post(), y - 1, -1),
            ))

            shape = self.g.union([shape, temp_shape2])

        return shape

    def front_wall(self, skeleton=False):
        print('front_wall()')
        shape = None

        shape = self.g.union([shape, self.key_wall_brace(
            3, self.p.lastrow, 0, -1, self.pl.web_post_bl(),
            3, self.p.lastrow, 0.5, -1, self.pl.web_post_br(), wall='front'
        )])

        shape = self.g.union([shape, self.key_wall_brace(
            3, self.p.lastrow, 0.5, -1, self.pl.web_post_br(),
            4, self.p.cornerrow, .5, -1, self.pl.web_post_bl()
        )])
        shape = self.g.union([shape, self.key_wall_brace(
            4, self.p.cornerrow, .5, -1, self.pl.web_post_bl(),
            4, self.p.cornerrow, 0, -1, self.pl.web_post_br()
        )])

        for i in range(self.p.ncols - 5):
            x = i + 5

            shape = self.g.union([shape, self.key_wall_brace(
                x, self.p.cornerrow, 0, -1, self.pl.web_post_bl(),
                x, self.p.cornerrow, 0, -1, self.pl.web_post_br()
            )])

            shape = self.g.union([shape, self.key_wall_brace(
                x, self.p.cornerrow, 0, -1, self.pl.web_post_bl(),
                x - 1, self.p.cornerrow, 0, -1, self.pl.web_post_br()
            )])

        return shape

    def case_walls(self, skeleton=False):
        print('case_walls()')
        return (
            self.g.union([
                self.back_wall(skeleton=skeleton),
                self.left_wall(skeleton=skeleton),
                self.right_wall(skeleton=skeleton),
                self.front_wall(skeleton=skeleton),
                # MOVED TO SEPARABLE THUMB SECTION
                # cluster().walls(),
                # cluster().connection(),
            ])
        )




    def screw_insert_shape(self, bottom_radius, top_radius, height):
        debugprint('screw_insert_shape()')
        if bottom_radius == top_radius:
            base = self.g.cylinder(radius=bottom_radius, height=height)
            # base = self.g.translate(cylinder(radius=bottom_radius, height=height),(0, 0, -height / 2))
        else:
            base = self.g.translate(self.g.cone(r1=bottom_radius, r2=top_radius, height=height), (0, 0, -height / 2))

        shape = self.g.union((
            base,
            self.g.translate(self.g.sphere(top_radius), (0, 0, height / 2)),
        ))
        return shape

    def screw_insert(self, column, row, bottom_radius, top_radius, height):
        debugprint('screw_insert()')
        shift_right = column == self.p.lastcol
        shift_left = column == 0
        shift_up = (not (shift_right or shift_left)) and (row == 0)
        shift_down = (not (shift_right or shift_left)) and (row >= self.p.lastrow)

        if self.p.screws_offset == 'INSIDE':
            # debugprint('Shift Inside')
            shift_left_adjust = self.p.wall_base_x_thickness
            shift_right_adjust = -self.p.wall_base_x_thickness / 2
            shift_down_adjust = -self.p.wall_base_y_thickness / 2
            shift_up_adjust = -self.p.wall_base_y_thickness / 3

        elif self.p.screws_offset == 'OUTSIDE':
            # debugprint('Shift Outside')
            shift_left_adjust = 0
            shift_right_adjust = self.p.wall_base_x_thickness / 2
            shift_down_adjust = self.p.wall_base_y_thickness * 2 / 3
            shift_up_adjust = self.p.wall_base_y_thickness * 2 / 3

        else:
            # debugprint('Shift Origin')
            shift_left_adjust = 0
            shift_right_adjust = 0
            shift_down_adjust = 0
            shift_up_adjust = 0

        if shift_up:
            position = self.key_position(
                list(np.array(self.wall_locate2(0, 1)) + np.array([0, (self.p.mount_height / 2) + shift_up_adjust, 0])),
                column,
                row,
            )
        elif shift_down:
            position = self.key_position(
                list(np.array(self.wall_locate2(0, -1)) - np.array([0, (self.p.mount_height / 2) + shift_down_adjust, 0])),
                column,
                row,
            )
        elif shift_left:
            position = list(
                np.array(self.left_key_position(row, 0)) + np.array(self.wall_locate3(-1, 0)) + np.array(
                    (shift_left_adjust, 0, 0))
            )
        else:
            position = self.key_position(
                list(np.array(self.wall_locate2(1, 0)) + np.array([(self.p.mount_height / 2), 0, 0]) + np.array(
                    (shift_right_adjust, 0, 0))
                     ),
                column,
                row,
            )

        shape = self.screw_insert_shape(bottom_radius, top_radius, height)
        shape = self.g.translate(shape, [position[0], position[1], height / 2])

        return shape

    def screw_insert_thumb_shapes(self, bottom_radius, top_radius, height, offset=0):
        positions = self.cluster.screw_positions(self.p.separable_thumb)
        # print(positions)
        shapes = []
        for position in positions:
            scr_shape = self.screw_insert_shape(bottom_radius, top_radius, height)
            scr_shape = self.g.translate(scr_shape, [position[0], position[1], height / 2])
            scr_shape = self.g.translate(scr_shape,(0, 0, offset))
            shapes.append(scr_shape)
        return shapes


    def screw_insert_all_shapes(self, bottom_radius, top_radius, height, offset=0.0):
        print('screw_insert_all_shapes()')
        shape = (
            self.g.translate(self.screw_insert(0, 0, bottom_radius, top_radius, height),
                             (0, 0, offset)),
            self.g.translate(self.screw_insert(0, self.p.cornerrow, bottom_radius, top_radius, height),
                             (0, self.p.left_wall_ext_lower_y_offset, offset)),
            self.g.translate(self.screw_insert(3, self.p.lastrow, bottom_radius, top_radius, height),
                             (0, 0, offset)),
            self.g.translate(self.screw_insert(3, 0, bottom_radius, top_radius, height),
                             (0, 0, offset)),
            self.g.translate(self.screw_insert(self.p.lastcol, 0, bottom_radius, top_radius, height),
                             (0, 0, offset)),
            self.g.translate(self.screw_insert(self.p.lastcol, self.p.cornerrow, bottom_radius, top_radius, height, ),
                             (0, 0, offset)),
            # self.g.translate(screw_insert_thumb(bottom_radius, top_radius, height), (0, 0, offset)),
        )

        return shape

    def screw_insert_holes(self):
        return self.screw_insert_all_shapes(
            self.p.screw_insert_bottom_radius, self.p.screw_insert_top_radius, self.p.screw_insert_height + .02,
            offset=-.01
        )



    def screw_insert_outers(self, offset=0.0, thumb=False):
        # screw_insert_bottom_radius + screw_insert_wall
        # screw_insert_top_radius + screw_insert_wall
        bottom_radius = self.p.screw_insert_outer_radius
        top_radius = self.p.screw_insert_outer_radius
        height = self.p.screw_insert_height + 1.5

        if thumb:
            return self.screw_insert_thumb_shapes(bottom_radius, top_radius, height, offset=offset)
        else:
            return self.screw_insert_all_shapes(bottom_radius, top_radius, height, offset=offset)


    def screw_insert_screw_holes(self, thumb=False):
        if thumb:
            return self.screw_insert_thumb_shapes(1.7, 1.7, 350)
        else:
            return self.screw_insert_all_shapes(1.7, 1.7, 350)

    ## TODO:  Find places to inject the thumb features.

    def model_side(self):
        print('model_right()')

        shape = self.g.union([self.key_holes()])
        if debug_exports:
            self.g. self.g.export_file(shape=shape, fname=path.join(r"..", "things", r"debug_key_plates"))
        connector_shape = self.connectors()
        shape = self.g.union([shape, connector_shape])
        if debug_exports:
             self.g.export_file(shape=shape, fname=path.join(r"..", "things", r"debug_connector_shape"))

        walls_shape = self.case_walls(skeleton=self.p.skeletal)
        if debug_exports:
             self.g.export_file(shape=walls_shape, fname=path.join(r"..", "things", r"debug_walls_shape"))

        s2 = self.g.union([walls_shape])
        s2 = self.g.union([s2, *self.screw_insert_outers()])

        if self.ctrl is not None:
            s2 = self.ctrl.generate_controller_mount(s2)

        s2 = self.g.difference(s2, [self.g.union(self.screw_insert_holes())])
        shape = self.g.union([shape, s2])

        if self.oled is not None:
            hole, frame = self.oled.oled_mount_frame()
            shape = self.g.difference(shape, [hole])
            shape = self.g.union([shape, frame])

        for module in self.modules:
            shape = module.update_main(shape)
        # if self.p.trackball_in_wall and (self.side == self.p.ball_side or self.p.ball_side == 'both') and self.p.separable_thumb:
        #     tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_wall()
        #
        #     shape = self.g.difference(shape, [tbprecut])
        #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
        #     shape = self.g.union([shape, tb])
        #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
        #     shape = self.g.difference(shape, [tbcutout])
        #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
        #     #  self.g.export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
        #     shape = self.g.union([shape, sensor])
        #
        #     if self.p.show_caps:
        #         shape = self.g.add([shape, ball])

        if self.pl.pp.plate_pcb_clear:
            shape = self.g.difference(shape, [self.plate_pcb_cutouts()])

        main_shape = shape

        thumb_section = self.cluster.generate_thumb()

        for module in self.modules:
            thumb_section = module.update_thumb(thumb_section)



        has_trackball = False
        if self.cluster.is_tb:
            print("Has Trackball")
            tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_cluster(self.cluster)
            has_trackball = True
            thumb_section = self.g.difference(thumb_section, [tbprecut])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_1_shape".format(self.side)))
            thumb_section = self.g.union([thumb_section, tb])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_2_shape".format(self.side)))
            thumb_section = self.g.difference(thumb_section, [tbcutout])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_3_shape".format(self.side)))
            thumb_section = self.g.union([thumb_section, sensor])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_4_shape".format(self.side)))

        if self.pl.pp.plate_pcb_clear:
            thumb_section = self.g.difference(thumb_section, [self.cluster.thumb_pcb_plate_cutouts()])

        block = self.g.box(350, 350, 40)
        block = self.g.translate(block, (0, 0, -20))
        main_shape = self.g.difference(main_shape, [block])
        thumb_section = self.g.difference(thumb_section, [block])

        if debug_exports:
             self.g.export_file(shape=thumb_section, fname=path.join(r"..", "things", r"debug_thumb_test_5_shape".format(self.side)))

        if self.p.separable_thumb:
            thumb_section = self.g.difference(thumb_section, [main_shape])
            if self.p.show_caps:
                thumb_section = self.g.add([thumb_section, self.cluster.thumbcaps()])
                if has_trackball:
                    thumb_section = self.g.add([thumb_section, ball])
        else:
            main_shape = self.g.union([main_shape, thumb_section])
            if debug_exports:
                 self.g.export_file(shape=main_shape,
                            fname=path.join(r"..", "things", r"debug_thumb_test_6_shape".format(self.side)))
            if self.p.show_caps:
                main_shape = self.g.add([main_shape, self.cluster.thumbcaps()])
                if has_trackball:
                    main_shape = self.g.add([main_shape, ball])

            # if self.p.trackball_in_wall and (self.side == self.p.ball_side or self.p.ball_side == 'both') and not self.p.separable_thumb:
            #     tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_wall()
            #
            #     main_shape = self.g.difference(main_shape, [tbprecut])
            #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
            #     main_shape = self.g.union([main_shape, tb])
            #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
            #     main_shape = self.g.difference(main_shape, [tbcutout])
            #     #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
            #     #  self.g.export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
            #     main_shape = self.g.union([main_shape, sensor])
            #
            #     if self.p.show_caps:
            #         main_shape = self.g.add([main_shape, ball])

        if self.p.show_caps:
            main_shape = self.g.add([main_shape, self.caps()])

        if self.side == "left":
            main_shape = self.g.mirror(main_shape, 'YZ')
            thumb_section = self.g.mirror(thumb_section, 'YZ')

        return main_shape, thumb_section

    def baseplate(self, wedge_angle=None):

        if self.p.ENGINE == 'cadquery':
            cq = self.g.cq
            # shape = mod_r

            thumb_shape = self.cluster.thumb()
            thumb_wall_shape = self.cluster.walls(skeleton=self.p.skeletal)
            thumb_wall_shape = self.g.union([thumb_wall_shape, *self.screw_insert_outers(thumb=True)])
            thumb_connector_shape = self.cluster.thumb_connectors()
            thumb_connection_shape = self.cluster.connection(skeleton=self.p.skeletal)
            thumb_section = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])
            thumb_section = self.g.difference(thumb_section, self.screw_insert_holes(thumb=True))

            shape = self.g.union([
                self.case_walls(),
                *self.screw_insert_outers(),
                thumb_section
            ])
            tool = self.screw_insert_all_shapes(self.p.screw_hole_diameter / 2., self.p.screw_hole_diameter / 2., 350, )
            for item in tool:
                item = self.g.translate(item, [0, 0, -10])
                shape = self.g.difference(shape, [item])

            tool = self.screw_insert_thumb_shapes(self.p.screw_hole_diameter / 2., self.p.screw_hole_diameter / 2., 350, )
            for item in tool:
                item = self.g.translate(item, [0, 0, -10])
                shape = self.g.difference(shape, [item])

            # shape = self.g.union([main_shape, thumb_shape])

            shape = self.g.translate(shape, (0, 0, -0.0001))

            square = self.g.cq.Workplane('XY').rect(1000, 1000)
            for wire in square.wires().objects:
                plane = self.g.cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
            shape = self.g.intersect(shape, plane)

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
                if sizes[-1] > max_val:
                    inner_index = i_wire
                    max_val = sizes[-1]
            debugprint(sizes)
            inner_wire = base_wires[inner_index]

            # inner_plate = cq.Workplane('XY').add(cq.Face.makeFromWires(inner_wire))
            if wedge_angle is not None:
                0
                #NOT IMPLEMENTED
                # cq.Workplane('XY').add(cq.Solid.revolve(outerWire, innerWires, angleDegrees, axisStart, axisEnd))
            else:
                inner_shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outerWire=inner_wire, innerWires=[],
                                                                            vecNormal=cq.Vector(0, 0, self.p.base_thickness)))
                inner_shape = self.g.translate(inner_shape, (0, 0, -self.p.base_rim_thickness))

                holes = []
                for i in range(len(base_wires)):
                    if i not in [inner_index, outer_index]:
                        holes.append(base_wires[i])
                cutout = [*holes, inner_wire]

                shape = cq.Workplane('XY').add(
                    cq.Solid.extrudeLinear(outer_wire, cutout, cq.Vector(0, 0, self.p.base_rim_thickness)))
                hole_shapes = []
                for hole in holes:
                    loc = hole.Center()
                    hole_shapes.append(
                        self.g.translate(
                            self.g.cylinder(self.p.screw_cbore_diameter / 2.0, self.p.screw_cbore_depth),
                            (loc.x, loc.y, 0)
                            # (loc.x, loc.y, screw_cbore_depth/2)
                        )
                    )
                shape = self.g.difference(shape, hole_shapes)
                shape = self.g.translate(shape, (0, 0, -self.p.base_rim_thickness))
                shape = self.g.union([shape, inner_shape])
            return shape

        else:
            shape = self.g.union([
                self.case_walls(),
                self.cluster.walls(),
                self.cluster.connection(),
                *self.screw_insert_outers(),
                *self.screw_insert_outers(thumb=True),
            ])
            tool = self.g.translate(self.g.union([
                *self.screw_insert_screw_holes(),
                *self.screw_insert_screw_holes(thumb=True),
            ]), [0, 0, -10])
            base = self.g.box(1000, 1000, .01)
            shape = shape - tool
            shape = self.g.intersect(shape, base)

            shape = self.g.translate(shape, [0, 0, -0.001])

            return self.g.sl.projection(cut=True)(shape)

    def run(self):
        # Process parameters sets the parameter based on the right cluster and any assymmetric features.
        # Features can provide overwrites for parameters for their side.

        # Side-ality has been removed from arguments and moved to an instance variable to minimize passing
        # class level settings during generation.
        self.process_parameters('right')
        mod_r, tmb_r = self.model_side()
        self.g.export_file(shape=mod_r, fname=path.join(self.p.save_path, self.p.config_name + r"_right"))
        self.g.export_file(shape=tmb_r, fname=path.join(self.p.save_path, self.p.config_name + r"_thumb_right"))

        # base = baseplate(mod_r, tmb_r)
        base = self.baseplate()
        self.g.export_file(shape=base, fname=path.join(self.p.save_path, self.p.config_name + r"_right_plate"))
        self.g.export_dxf(shape=base, fname=path.join(self.p.save_path, self.p.config_name + r"_right_plate"))

        if not self.p.symmetric:
            print('ASYMMETRIC')
            self.process_parameters('left')

            mod_l, tmb_l = self.model_side()
            self.g.export_file(shape=mod_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left"))
            self.g.export_file(shape=tmb_l, fname=path.join(self.p.save_path, self.p.config_name + r"_thumb_left"))

            base_l = self.g.mirror(self.baseplate(), 'YZ')
            self.g.export_file(shape=base_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))
            self.g.export_dxf(shape=base_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))

        else:
            print('SYMMETRIC')
            self.g.export_file(shape=self.g.mirror(mod_r, 'YZ'), fname=path.join(self.p.save_path, self.p.config_name + r"_left"))

            lbase = self.g.mirror(base, 'YZ')
            self.g.export_file(shape=lbase, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))
            self.g.export_dxf(shape=lbase, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))

        if self.p.ENGINE == 'cadquery':
            freecad.generate_freecad_script(path.abspath(self.p.save_path), [
                self.p.config_name + r"_right",
                self.p.config_name + r"_left",
                self.p.config_name + r"_right_plate",
                self.p.config_name + r"_left_plate"
            ])






if __name__ == '__main__':
    pass

    # base = baseplate()
    #  self.g.export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))
