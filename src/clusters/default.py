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
class DefaultClusterParameters(ca.ClusterParametersBase):
    name: str = 'DEFAULT'

    package: str = 'clusters.default'
    class_name: str = 'DefaultCluster'

    thumb_offsets: Sequence[float] = (6.0, -3.0, 7.0)

    tl_rotation: Sequence[float] = (7.5, -18, 10)
    tl_position: Sequence[float] = (-32.5, -14.5, -2.5)

    tr_rotation: Sequence[float] = (10, -15, 10)
    tr_position: Sequence[float] = (-12.0, -16.0, 3.0)

    ml_rotation: Sequence[float] = (6, -34, 40)
    ml_position: Sequence[float] = (-51.0, -25.0, -12.0)

    mr_rotation: Sequence[float] = (-6, -34, 48)
    mr_position: Sequence[float] = (-29.0, -40.0, -13.0)

    bl_rotation: Sequence[float] = (-4.0, -35.0, 52.0)
    bl_position: Sequence[float] = (-56.3, -43.3, -23.5)

    br_rotation: Sequence[float] = (-16, -33, 54)
    br_position: Sequence[float] = (-37.8, -55.3, -25.3)

    cluster_1U: bool = False

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-21, -58),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = (
        (-28, -65), (8, -31), (-53, -3),
    )


# VARIABLES =[
# self.p.mount_width
# self.p.mount_height
# self.p.post_adj
# self.p.double_plate_height
# self.p.cornerrow
# self.p.lastrow
#
# default_1U_cluster
# ]

class DefaultCluster(ca.ClusterBase):
    parameter_type = DefaultClusterParameters
    num_keys = 6
    is_tb = False

    def set_overrides(self):
        if self.tp.cluster_1U:
                self.parent.pl.pp.double_plate_height = (.7 * self.pl.pp.sa_double_length - self.p.mount_height) / 3
        elif self.tp.name == 'DEFAULT':
            self.parent.pl.pp.double_plate_height = (.95 * self.pl.pp.sa_double_length - self.p.mount_height) / 3


    @staticmethod
    def name():
        return "DEFAULT"


    def thumborigin(self):
        # debugprint('thumborigin()')
        origin = self.parent.key_position([self.p.mount_width / 2, -(self.p.mount_height / 2), 0], 1, self.p.cornerrow)

        for i in range(len(origin)):
            origin[i] = origin[i] + self.tp.thumb_offsets[i]

        return origin

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        if cap:
            shape_list = [
                self.mr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_mr_rotation])),
                self.ml_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_ml_rotation])),
                self.br_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_br_rotation])),
                self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
            ]

            if self.tp.cluster_1U:
                shape_list.append(self.tr_place(
                    self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.tp.thumb_plate_tr_rotation]))
                )
                shape_list.append(self.tr_place(
                    self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.tp.thumb_plate_tr_rotation]))
                )
                shape_list.append(self.tl_place(
                    self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation]))
                )
            shapes = self.g.add(shape_list)

        else:
            shape_list = [
                self.mr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_mr_rotation])),
                self.ml_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_ml_rotation])),
                self.br_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_br_rotation])),
                self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
            ]
            if self.tp.cluster_1U:
                shape_list.append(self.tr_place(self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.tp.thumb_plate_tr_rotation])))
            shapes = self.g.union(shape_list)
        return shapes

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        debugprint('thumb_15x_layout()')
        if plate:
            if cap:
                shape = self.g.rotate(shape, (0, 0, 90))
                cap_list = [self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation]))]
                cap_list.append(self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])))
                return self.g.add(cap_list)
            else:
                shape_list = [self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tl_rotation]))]
                if not self.tp.cluster_1U:
                    shape_list.append(self.tr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])))
                return self.g.union(shape_list)
        else:
            if cap:
                shape = self.g.rotate(shape, (0, 0, 90))
                shape_list = [self.tl_place(shape)]
                shape_list.append(self.tr_place(shape))

                return self.g.add(shape_list)
            else:
                shape_list = [
                    self.tl_place(shape),
                ]
                if not self.tp.cluster_1U:
                    shape_list.append(self.tr_place(shape))

                return self.g.union(shape_list)

    def thumbcaps(self):
        t1 = self.thumb_1x_layout(self.pl.sa_cap(1), cap=True)
        if not self.tp.cluster_1U:
            t1.add(self.thumb_15x_layout(self.pl.sa_cap(1.5), cap=True))
        return t1

    def thumb(self):
        print('thumb()')
        shape = self.thumb_1x_layout(self.g.rotate(self.pl.single_plate(), (0, 0, -90)))
        shape = self.g.union([shape, self.thumb_15x_layout(self.g.rotate(self.pl.single_plate(), (0, 0, -90)))])
        shape = self.g.union([shape, self.thumb_15x_layout(self.pl.double_plate(), plate=False)])

        return shape


    def thumb_connectors(self):
        print('thumb_connectors()')
        hulls = []
        if self.tp.cluster_1U:
            thumbpost_tl = self.pl.web_post_tl
            thumbpost_tr = self.pl.web_post_tr
            thumbpost_bl = self.pl.web_post_bl
            thumbpost_br = self.pl.web_post_br
        else:
            thumbpost_tl = self.thumb_post_tl
            thumbpost_tr = self.thumb_post_tr
            thumbpost_bl = self.thumb_post_bl
            thumbpost_br = self.thumb_post_br
        # Top two
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tr()),
                    self.tl_place(self.thumb_post_br()),
                    self.tr_place(thumbpost_tl()),
                    self.tr_place(thumbpost_bl()),
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
                    self.br_place(self.pl.web_post_tr()),
                    self.br_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tl()),
                    self.mr_place(self.pl.web_post_bl()),
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
                    self.br_place(self.pl.web_post_tl()),
                    self.bl_place(self.pl.web_post_bl()),
                    self.br_place(self.pl.web_post_tr()),
                    self.bl_place(self.pl.web_post_br()),
                    self.mr_place(self.pl.web_post_tl()),
                    self.ml_place(self.pl.web_post_bl()),
                    self.mr_place(self.pl.web_post_tr()),
                    self.ml_place(self.pl.web_post_br()),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.ml_place(self.pl.web_post_tr()),
                    self.tl_place(self.thumb_post_bl()),
                    self.ml_place(self.pl.web_post_br()),
                    self.tl_place(self.thumb_post_br()),
                    self.mr_place(self.pl.web_post_tr()),
                    self.tr_place(thumbpost_bl()),
                    self.mr_place(self.pl.web_post_br()),
                    self.tr_place(thumbpost_br()),
                ]
            )
        )


        hulls.append(
            self.g.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.tl_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 0, self.p.cornerrow),
                    self.tr_place(thumbpost_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 1, self.p.cornerrow),
                    self.tr_place(thumbpost_tr()),
                    self.parent.key_place(self.pl.web_post_br(), 1, self.p.cornerrow),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(thumbpost_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tr_place(thumbpost_br()),
                    self.parent.key_place(self.pl.web_post_br(), 2, self.p.lastrow),
                    self.parent.key_place(self.pl.web_post_bl(), 3, self.p.lastrow),
                ]
            )
        )

        # return self.g.add(hulls)
        return self.g.union(hulls)


    def walls(self, skeleton=False):
        print('thumb_walls()')
        # thumb, walls
        if self.tp.cluster_1U:
            thumbpost_tl = self.pl.web_post_tl
            thumbpost_tr = self.pl.web_post_tr
            thumbpost_bl = self.pl.web_post_bl
            thumbpost_br = self.pl.web_post_br
        else:
            thumbpost_tl = self.thumb_post_tl
            thumbpost_tr = self.thumb_post_tr
            thumbpost_bl = self.thumb_post_bl
            thumbpost_br = self.thumb_post_br

        shape = self.g.union([self.parent.wall_brace(self.mr_place, 0, -1, self.pl.web_post_br(),
                                                     self.tr_place, 0, -1, thumbpost_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.mr_place, 0, -1, self.pl.web_post_br(),
                                                            self.mr_place, 0, -1, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, 0, -1, self.pl.web_post_br(),
                                                            self.br_place, 0, -1, self.pl.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, -0.3, 1, self.pl.web_post_tr(),
                                                            self.ml_place, 0, 1, self.pl.web_post_tl())])
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
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, 0, 1, self.pl.web_post_tl(),
                                                            self.bl_place, 0, 1, self.pl.web_post_tr())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.pl.web_post_bl(),
                                                            self.br_place, -1, 0, self.pl.web_post_tl())])
        shape = self.g.union([shape,
                              self.parent.wall_brace(self.tr_place, 0, -1, thumbpost_br(),
                                                     (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0,
                                                     -1, self.pl.web_post_bl())])

        return shape

    def connection(self, skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = None
        shape = self.g.union([shape, self.g.bottom_hull(
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
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1,
                                                          low_corner=True),
                               self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1,
                                                          low_corner=True),
                               self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.pl.web_post(), self.p.cornerrow, -1, low_corner=True),
                self.parent.left_key_place(self.g.translate(self.pl.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.ml_place(self.pl.web_post_tr()),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate1(-0.3, 1))),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.pl.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        return shape

    def get_extras(self, shape, pos):
        return shape

    def thumb_pcb_plate_cutouts(self):
        shape = self.thumb_1x_layout(self.pl.plate_pcb_cutout())
        shape = self.g.union([shape, self.thumb_15x_layout(self.pl.plate_pcb_cutout())])
        return shape