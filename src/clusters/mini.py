import json
import os

from dataclasses_json import dataclass_json
from dataclasses import dataclass
import clusters.cluster_abc as ca
from typing import Any, Sequence

def debugprint(data):
    pass
    # print
@dataclass_json
@dataclass
class MiniClusterParameters(ca.ClusterParametersBase):
    name: str = 'MINI'

    package: str = 'clusters.mini'
    class_name: str = 'MiniCluster'

    thumb_offsets: Sequence[float] = (6.0, -3.0, 7.0)

    tr_rotation: Sequence[float] = (14, -15, 10)
    tr_position: Sequence[float] = (-15, -10, 5)

    tl_rotation: Sequence[float] = (10, -23, 25)
    tl_position: Sequence[float] = (-35, -16, -2)

    mr_rotation: Sequence[float] = (10, -23, 25)
    mr_position: Sequence[float] = (-23, -34, -6)

    br_rotation: Sequence[float] = (6, -34, 35)
    br_position: Sequence[float] = (-39, -43, -16)

    bl_rotation: Sequence[float] = (6, -32, 35)
    bl_position: Sequence[float] = (-51, -25, -11.5)

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-29, -52),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-29, -52), (-62, 10), (12, -25))


class MiniCluster(ca.ClusterBase):
    parameter_type = MiniClusterParameters
    num_keys = 6
    is_tb = False

    @staticmethod
    def name():
        return "MINI"

    def set_overrides(self):
        pass

    def tl_place(self, shape):
        shape = self.g.rotate(shape, self.tp.tl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tl_position)
        return shape

    def tr_place(self, shape):
        shape = self.g.rotate(shape, self.tp.tr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tr_position)
        return shape

    def mr_place(self, shape):
        shape = self.g.rotate(shape, self.tp.mr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.mr_position)
        return shape

    def br_place(self, shape):
        shape = self.g.rotate(shape, self.tp.br_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.br_position)
        return shape

    def bl_place(self, shape):
        shape = self.g.rotate(shape, self.tp.bl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.bl_position)
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        return self.g.union([
            self.mr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_mr_rotation])),
            self.br_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_br_rotation])),
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation])),
            self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
        ])


    def thumb_15x_layout(self, shape, cap=False, plate=True):
        debugprint('thumb_15x_layout()')
        return self.g.union([self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation]))])

    def thumbcaps(self):
        t1 = self.thumb_1x_layout(self.pl.sa_cap(1))
        t15 = self.thumb_15x_layout(self.g.rotate(self.pl.sa_cap(1), [0, 0, 90]))
        return t1.add(t15)

    def thumb(self):
        print('thumb()')
        shape = self.thumb_1x_layout(self.pl.single_plate())
        shape = self.g.union([shape, self.thumb_15x_layout(self.pl.single_plate())])

        return shape

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.pl.web_post(),
                                [self.p.mount_width / 2 - self.p.post_adj, (self.p.mount_height / 2) - self.p.post_adj, 0]
                                )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, (self.p.mount_height / 2) - self.p.post_adj, 0]
                                )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, -(self.p.mount_height / 2) + self.p.post_adj, 0]
                                )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) - self.p.post_adj, -(self.p.mount_height / 2) + self.p.post_adj, 0]
                                )




    def thumb_connectors(self):
        hulls = []

        # Top two
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_br()),
                    self.tr_place(self.thumb_post_tl()),
                    self.tr_place(self.thumb_post_bl()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.pl.web_post_tr()),
                    self.br_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tl()),
                    self.mr_place(self.pl.web_post_bl()),
                ]
            )
        )

        # bottom two on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.mr_place(self.pl.web_post_tr()),
                    self.mr_place(self.pl.web_post_br()),
                    self.tr_place(self.thumb_post_br()),
                ]
            )
        )

        # between top and bottom row
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.pl.web_post_tl()),
                    self.bl_place(self.pl.web_post_bl()),
                    self.br_place(self.pl.web_post_tr()),
                    self.bl_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tl()),
                    self.tl_place(self.pl.web_post_bl()),
                    self.mr_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_br()),
                    self.tr_place(self.pl.web_post_bl()),
                    self.mr_place(self.pl.web_post_tr()),
                    self.tr_place(self.pl.web_post_br()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tl()),
                    self.bl_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_bl()),
                    self.bl_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tr()),
                    self.tl_place(self.pl.web_post_bl()),
                    self.tl_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tr()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.pl.web_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.tl_place(self.pl.web_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 0, self.p.cornerrow),
                    self.tr_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 1, self.p.cornerrow),
                    self.tr_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 1, self.p.cornerrow),
                    # self.parent.key_place(self.sh.web_post_tl(), 2, self.p.lastrow),
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
        shape = self.g.union([self.parent.wall_brace(self.mr_place, 0, -1, self.pl.web_post_br(), self.tr_place, 0, -1, self.thumb_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.mr_place, 0, -1, self.pl.web_post_br(),
                                                            self.mr_place, 0, -1, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, 0, -1, self.pl.web_post_br(),
                                                            self.br_place, 0, -1, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, 0, 1, self.pl.web_post_tr(),
                                                            self.bl_place, 0, 1, self.pl.web_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, -1, 0, self.pl.web_post_tl(),
                                                            self.br_place, -1, 0, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_tl(),
                                                            self.bl_place, -1, 0, self.pl.web_post_bl())])
        # thumb, corners
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, -1, 0, self.pl.web_post_bl(),
                                                            self.br_place, 0, -1, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_tl(),
                                                            self.bl_place, 0, 1, self.pl.web_post_tl())])
        # thumb, tweeners
        shape = self.g.union([shape, self.parent.wall_brace(self.mr_place, 0, -1, self.pl.web_post_bl(),
                                                            self.br_place, 0, -1, self.pl.web_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_bl(),
                                                            self.br_place, -1, 0, self.pl.web_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(),
                                                            (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0, -1, self.pl.web_post_bl())])

        return shape


    def connection(self, skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.g.union([self.g.bottom_hull(
            [
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.pl.web_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.tl_place(self.pl.web_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                               self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                               self.tl_place(self.pl.web_post_tl()),
                           ]
                       )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.bl_place(self.pl.web_post_tr()),
                               self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate1(-0.3, 1))),
                               self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.bl_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.pl.web_post_tl()),
                           ]
                       )])

        return shape

    def thumb_pcb_plate_cutouts(self):
        shape = self.thumb_1x_layout(self.pl.plate_pcb_cutout())
        shape = self.g.union([shape, self.mini_thumb_15x_layout(self.pl.plate_pcb_cutout())])
        #shape = self.g.add([shape, mini_thumb_15x_layout(self.sh.plate_pcb_cutout())])
        return shape