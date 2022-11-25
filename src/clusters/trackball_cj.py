import json
import os
import numpy as np
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import clusters.trackball_cluster_abc as ca
from typing import Any, Sequence

def debugprint(data):
    pass
    # print



@dataclass_json
@dataclass
class TrackballCJClusterParameters(ca.TrackballClusterParametersBase):
    name: str = 'TRACKBALL_CJ'

    package: str = 'clusters.trackball_cj'
    class_name: str = 'TrackballCJCluster'

    thumb_offsets: Sequence[float] = (6.0, -3.0, 7.0)

    tl_rotation: Sequence[float] = (7.5, -18, 10)
    tl_position: Sequence[float] = (-32.5, -14.5, -2.5)

    tr_rotation: Sequence[float] = (10, -15, 10)
    tr_position: Sequence[float] = (-12.0, -16.0, 3.0)

    ml_rotation: Sequence[float] = (6, -34, 40)
    ml_position: Sequence[float] = (-51.0, -25.0, -12.0)

    bl_rotation: Sequence[float] = (-4.0, -35.0, 52.0)
    bl_position: Sequence[float] = (-56.3, -43.3, -23.5)

    track_rotation: Sequence[float] = (0, 0, 0)
    track_position: Sequence[float] = (-15, -60, -12)

    tb_inner_diameter: float = 42
    tb_thickness: float = 2
    tb_outer_diameter: float = 53

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-40, -75),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = (
        (-40, -75), (-63, 10), (15, -40)
    )


class TrackballCJCluster(ca.TrackballClusterBase):
    parameter_type = TrackballCJClusterParameters
    num_keys = 4
    is_tb = True


    @staticmethod
    def name():
        return "TRACKBALL_CJ"

    def position_rotation(self):
        pos = np.array(self.tp.track_position) + np.array(self.thumborigin())
        rot = self.tp.track_rotation
        return pos, rot

    def oct_corner(self, i, diameter, shape):
        radius = diameter / 2
        i = (i + 1) % 8

        r = radius
        m = radius * np.tan(np.pi / 8)

        points_x = [m, r, r, m, -m, -r, -r, -m]
        points_y = [r, m, -m, -r, -r, -m, m, r]

        return self.g.translate(shape, (points_x[i], points_y[i], 0))

    def thumb_layout(self, shape):
        return self.g.union([
            self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])),
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation])),
            self.ml_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_ml_rotation])),
            self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
        ])

    def tbcj_edge_post(self, i):
        shape = self.g.box(self.p.post_size, self.p.post_size, self.tp.tb_thickness)
        shape = self.oct_corner(i, self.tp.tb_outer_diameter, shape)
        return shape

    def tbcj_web_post(self, i):
        shape = self.g.box(self.p.post_size, self.p.post_size, self.tp.tb_thickness)
        shape = self.oct_corner(i, self.tp.tb_outer_diameter, shape)
        return shape

    def tbcj_holder(self):
        center = self.g.box(self.p.post_size, self.p.post_size, self.tp.tb_thickness)

        shape = []
        for i in range(8):
            shape_ = self.g.hull_from_shapes([
                center,
                self.tbcj_edge_post(i),
                self.tbcj_edge_post(i + 1),
            ])
            shape.append(shape_)
        shape = self.g.union(shape)

        shape = self.g.difference(
            shape,
            [self.g.cylinder(self.tp.tb_inner_diameter / 2, self.tp.tb_thickness + 0.1)]
        )

        return shape

    def thumb(self):
        t = self.thumb_layout(self.pl.single_plate())
        tb = self.track_place(self.tbcj_holder())
        return self.g.union([t, tb])

    def thumbcaps(self):
        t = self.thumb_layout(self.pl.sa_cap(1))
        return t

    def thumb_connectors(self):
        hulls = []

        # Top two
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_br()),
                    self.tr_place(self.pl.web_post_tl()),
                    self.tr_place(self.pl.web_post_bl()),
                ]
            )
        )

        # centers of the bottom four
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.bl_place(self.pl.web_post_tr()),
                    self.bl_place(self.pl.web_post_br()),
                    self.ml_place(self.pl.web_post_tl()),
                    self.ml_place(self.pl.web_post_bl()),
                ]
            )
        )

        # top two to the middle two, starting on the left

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tl()),
                    self.ml_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_bl()),
                    self.ml_place(self.pl.web_post_br()),
                    self.tl_place(self.pl.web_post_br()),
                    self.tr_place(self.pl.web_post_bl()),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.tl_place(self.pl.web_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 0, self.p.cornerrow),
                    self.tr_place(self.pl.web_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 1, self.p.cornerrow),
                    self.tr_place(self.pl.web_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 1, self.p.cornerrow),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(self.pl.web_post_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(self.pl.web_post_br()),
                    self.parent.key_place(self.pl.web_post_br(), 2, self.p.lastrow),
                    self.parent.key_place(self.pl.web_post_bl(), 3, self.p.lastrow),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.track_place(self.tbcj_web_post(4)),
                    self.bl_place(self.pl.web_post_bl()),
                    self.track_place(self.tbcj_web_post(5)),
                    self.bl_place(self.pl.web_post_br()),
                    self.track_place(self.tbcj_web_post(6)),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.bl_place(self.pl.web_post_br()),
                    self.track_place(self.tbcj_web_post(6)),
                    self.ml_place(self.pl.web_post_bl()),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.ml_place(self.pl.web_post_bl()),
                    self.track_place(self.tbcj_web_post(6)),
                    self.ml_place(self.pl.web_post_br()),
                    self.tr_place(self.pl.web_post_bl()),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.track_place(self.tbcj_web_post(6)),
                    self.tr_place(self.pl.web_post_bl()),
                    self.track_place(self.tbcj_web_post(7)),
                    self.tr_place(self.pl.web_post_br()),
                    self.track_place(self.tbcj_web_post(0)),
                    self.tr_place(self.pl.web_post_br()),
                    self.parent.key_place(self.pl.web_post_bl(), 3, self.p.lastrow),
                ]
            )
        )

        return self.g.union(hulls)


    # todo update walls for wild track, still identical to orbyl
    def walls(self, skeleton=False):
        print('thumb_walls()')
        # thumb, walls
        shape = self.g.union([self.parent.wall_brace(self.ml_place, -0.3, 1, self.pl.web_post_tr(), self.ml_place, 0, 1, self.pl.web_post_tl())])
        shape = self.g.union(
            [shape, self.parent.wall_brace(self.bl_place, 0, 1, self.pl.web_post_tr(), self.bl_place, 0, 1, self.pl.web_post_tl())])
        shape = self.g.union(
            [shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_tl(), self.bl_place, -1, 0, self.pl.web_post_bl())])
        shape = self.g.union(
            [shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_tl(), self.bl_place, 0, 1, self.pl.web_post_tl())])
        shape = self.g.union(
            [shape, self.parent.wall_brace(self.ml_place, 0, 1, self.pl.web_post_tl(), self.bl_place, 0, 1, self.pl.web_post_tr())])

        corner = self.g.box(1, 1, self.tp.tb_thickness)

        points = [
            (self.bl_place, -1, 0, self.pl.web_post_bl()),
            (self.track_place, 0, -1, self.tbcj_web_post(4)),
            (self.track_place, 0, -1, self.tbcj_web_post(3)),
            (self.track_place, 0, -1, self.tbcj_web_post(2)),
            (self.track_place, 1, -1, self.tbcj_web_post(1)),
            (self.track_place, 1, 0, self.tbcj_web_post(0)),
            ((lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0, -1, self.pl.web_post_bl()),
        ]
        for i, _ in enumerate(points[:-1]):
            (pa, dxa, dya, sa) = points[i]
            (pb, dxb, dyb, sb) = points[i + 1]

            shape = self.g.union([shape, self.parent.wall_brace(pa, dxa, dya, sa, pb, dxb, dyb, sb)])

        return shape

    def connection(self, skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.g.union([self.g.bottom_hull(
            [
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.pl.web_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.tl_place(self.pl.web_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                self.tl_place(self.pl.web_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.ml_place(self.pl.web_post_tr()),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate1(-0.3, 1))),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                self.tl_place(self.pl.web_post_tl()),
            ]
        )])

        return shape

