from clusters.default import DefaultCluster
import os
import json
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import clusters.cluster_abc as ca
from typing import Any, Sequence

def debugprint(data):
    pass


@dataclass_json
@dataclass
class MinidoxClusterParameters(ca.ClusterParametersBase):
    name: str = 'MINIDOX'
    package: str = 'clusters.minidox'
    class_name: str = 'MinidoxCluster'

    thumb_offsets: Sequence[float] = (6.0, -3.0, 7.0)

    tl_rotation: Sequence[float] = (10, -23, 25)
    tl_position: Sequence[float] = (-35, -16, -2)

    tr_rotation: Sequence[float] = (14, -15, 10)
    tr_position: Sequence[float] = (-15, -10, 5)

    ml_rotation: Sequence[float] = (6, -34, 40)
    ml_position: Sequence[float] = (-53, -26, -12)

    thumb_plate_tr_rotation: float = 0
    thumb_plate_tl_rotation: float = 0
    thumb_plate_ml_rotation: float = 0

    minidox_Usize: float = 1.6

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-37, -34),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = (
        (-37, -37), (-65, 11), (10, -26),
    )

class MinidoxCluster(ca.ClusterBase):
    parameter_type = MinidoxClusterParameters
    num_keys = 3
    is_tb = False

    @staticmethod
    def name():
        return "MINIDOX"

    def set_overrides(self):
        pass

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        return self.g.union([
            self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])),
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation])),
            self.ml_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_ml_rotation])),
        ])

    def thumb_fx_layout(self, shape):
        return self.g.union([
            self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])),
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation])),
            self.ml_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_ml_rotation])),
        ])

    def thumbcaps(self):
        t1 = self.thumb_1x_layout(self.pl.sa_cap(1))
        return t1

    def thumb(self):
        print('thumb()')
        shape = self.thumb_fx_layout(self.g.rotate(self.pl.single_plate(), [0.0, 0.0, -90]))
        shape = self.g.union([shape, self.thumb_fx_layout(self.pl.adjustable_plate(self.tp.minidox_Usize))])

        return shape

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) - self.p.post_adj, ((self.p.mount_height/2) + self.pl.adjustable_plate_size(self.tp.minidox_Usize)) - self.p.post_adj, 0]
                                )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, ((self.p.mount_height/2) + self.pl.adjustable_plate_size(self.tp.minidox_Usize)) - self.p.post_adj, 0]
                                )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, -((self.p.mount_height/2) + self.pl.adjustable_plate_size(self.tp.minidox_Usize)) + self.p.post_adj, 0]
                                )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) - self.p.post_adj, -((self.p.mount_height/2) + self.pl.adjustable_plate_size(self.tp.minidox_Usize)) + self.p.post_adj, 0]
                                )

    def thumb_connectors(self):
        hulls = []

        # Top two
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tr()),
                    self.tl_place(self.thumb_post_br()),
                    self.tr_place(self.thumb_post_tl()),
                    self.tr_place(self.thumb_post_bl()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.tl_place(self.thumb_post_bl()),
                    self.ml_place(self.thumb_post_tr()),
                    self.ml_place(self.thumb_post_br()),
                ]
            )
        )

        # top two to the main keyboard, starting on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.tl_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 0, self.p.cornerrow),
                    self.tr_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 1, self.p.cornerrow),
                    self.tr_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 1, self.p.cornerrow),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(self.thumb_post_br()),
                    self.parent.key_place(self.pl.web_post_br(), 2, self.p.lastrow),
                    self.parent.key_place(self.pl.web_post_bl(), 3, self.p.lastrow),
                ]
            )
        )

        return self.g.union(hulls)

    def walls(self, skeleton=False):
        print('thumb_walls()')
        # thumb, walls
        shape = self.g.union([self.parent.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(), self.tr_place, 0, -1, self.thumb_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.tr_place, 0, -1, self.thumb_post_bl(), self.tl_place, 0, -1, self.thumb_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.tl_place, 0, -1, self.thumb_post_br(), self.tl_place, 0, -1, self.thumb_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.tl_place, 0, -1, self.thumb_post_bl(), self.ml_place, -1, -1, self.thumb_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, -1, -1, self.thumb_post_br(), self.ml_place, 0, -1, self.thumb_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, 0, -1, self.thumb_post_bl(), self.ml_place, -1, 0, self.thumb_post_bl())])
        # thumb, corners
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, -1, 0, self.thumb_post_bl(), self.ml_place, -1, 0, self.thumb_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, -1, 0, self.thumb_post_tl(), self.ml_place, 0, 1, self.thumb_post_tl())])
        # thumb, tweeners
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, 0, 1, self.thumb_post_tr(), self.ml_place, 0, 1, self.thumb_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(), (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0, -1, self.pl.web_post_bl())])

        return shape

    def connection(self, skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.g.union([self.g.bottom_hull(
            [
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                               # self.parent.key_place(self.g.translate(self.sh.web_post_bl(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.ml_place(self.thumb_post_tr()),
                               self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate1(0, 1))),
                               self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate2(0, 1))),
                               self.ml_place(self.g.translate(self.thumb_post_tr(), self.parent.wall_locate3(0, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        return shape


    def thumb_pcb_plate_cutouts(self):
        shape = self.thumb_fx_layout(self.pl.plate_pcb_cutout())
        shape = self.g.union([shape, self.thumb_fx_layout(self.pl.plate_pcb_cutout())])
        #shape = self.g.add([shape, minidox_thumb_fx_layout(self.sh.plate_pcb_cutout())])
        return shape
