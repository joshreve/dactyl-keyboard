import json
import os
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from abc import ABC
from typing import Any, Sequence, Tuple
# from src.dactyl_manuform import ParametersBase

def debugprint(data):
    pass
    # print

@dataclass_json
@dataclass
class ClusterParametersBase:
# class ClusterParametersBase(ParametersBase):
    name: str = 'NONE'
    package: str = 'cluster_abc'
    class_name: str = 'ClusterBase'

    thumb_offsets: Sequence[float] = (6, -3, 7)

    tr_rotation: Sequence[float] = (7.5, -18, 10)
    tr_position: Sequence[float] = (-32.5, -14.5, -2.5)

    tl_rotation: Sequence[float] = (10, -15, 10)
    tl_position: Sequence[float] = (-12, -16, 3)

    mr_rotation: Sequence[float] = (-6, -34, 48)
    mr_position: Sequence[float] = (-29, -40, -13)

    ml_rotation: Sequence[float] = (6, -34, 40)
    ml_position: Sequence[float] = (-51, -25, -12)

    br_rotation: Sequence[float] = (-16, -33, 54)
    br_position: Sequence[float] = (-37.8, -55.3, -25.3)

    bl_rotation: Sequence[float] = (-4, -35, 52)
    bl_position: Sequence[float] = (-56.3, -43.3, -23.5)

    thumb_plate_tr_rotation: float = 0
    thumb_plate_tl_rotation: float = 0
    thumb_plate_mr_rotation: float = 0
    thumb_plate_ml_rotation: float = 0
    thumb_plate_br_rotation: float = 0
    thumb_plate_bl_rotation: float = 0

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-21, -58),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-21, -58),)


class ClusterBase(ABC):
    parameter_type = ClusterParametersBase
    num_keys = 6
    is_tb = False
    debug_exports = False

    def __init__(self, parent, t_parameters=None):
        self.g = parent.g
        self.p = parent.p
        self.parent = parent
        self.pl = parent.pl

        if t_parameters is None:
            t_parameters = self.parameter_type()

        self.tp = t_parameters

        self.set_overrides()


    def set_overrides(self):
        pass

    @staticmethod
    def name():
        return "ABC"

    def thumborigin(self):
        origin = self.parent.key_position([self.p.mount_width / 2, -(self.p.mount_height / 2), 0], 1, self.p.cornerrow)

        for i in range(len(origin)):
            origin[i] = origin[i] + self.tp.thumb_offsets[i]

        return origin


    def tl_place(self, shape):
        debugprint('tl_place()')
        shape = self.g.rotate(shape, self.tp.tl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tl_position)
        return shape

    def tr_place(self, shape):
        debugprint('tr_place()')
        shape = self.g.rotate(shape, self.tp.tr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tr_position)
        return shape

    def mr_place(self, shape):
        debugprint('mr_place()')
        shape = self.g.rotate(shape, self.tp.mr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.mr_position)
        return shape

    def ml_place(self, shape):
        debugprint('ml_place()')
        shape = self.g.rotate(shape, self.tp.ml_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.ml_position)
        return shape

    def br_place(self, shape):
        debugprint('br_place()')
        shape = self.g.rotate(shape,  self.tp.br_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.br_position)
        return shape

    def bl_place(self, shape):
        debugprint('bl_place()')
        shape = self.g.rotate(shape, self.tp.bl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.bl_position)
        return shape

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) - self.p.post_adj, ((self.p.mount_height / 2) + self.pl.pp.double_plate_height) - self.p.post_adj, 0]
                                )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, ((self.p.mount_height / 2) + self.pl.pp.double_plate_height) - self.p.post_adj, 0]
                                )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) + self.p.post_adj, -((self.p.mount_height / 2) + self.pl.pp.double_plate_height) + self.p.post_adj, 0]
                                )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) - self.p.post_adj, -((self.p.mount_height / 2) + self.pl.pp.double_plate_height) + self.p.post_adj, 0]
                                )


    def thumb_1x_layout(self, shape, cap=False):
        return shape

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        return shape

    def thumbcaps(self):
        return self.pl.sa_cap(1)

    def thumb(self):
        return self.pl.single_plate()

    def thumb_connectors(self):
        return self.pl.web_post_tl()


    def walls(self, skeleton=False):
        return self.pl.web_post_tl()

    def connection(self, skeleton=False):
        return self.pl.web_post_tl()


    def screw_positions(self, separate_thumb=True):
        if separate_thumb:
            locations = self.tp.separable_thumb_screw_xy_locations
        else:
            locations = self.tp.thumb_screw_xy_locations

        origin = self.thumborigin()
        positions = []
        for i, loc in enumerate(locations):
            positions.append([])
            for j in range(2):
                positions[i].append(locations[i][j] + origin[j])
        return positions

    def get_extras(self, shape, pos):
        return shape

    def thumb_pcb_plate_cutouts(self):
        return self.pl.plate_pcb_cutout()

    def screw_insert_holes(self):
        return self.parent.screw_insert_thumb_shapes(
            self.p.screw_insert_bottom_radius, self.p.screw_insert_top_radius, self.p.screw_insert_height + .02,
            offset=-.01
        )

    def generate_thumb(self):
        # thumb_shape = thumb()
        thumb_shape = self.thumb()

        if self.debug_exports:
             self.g.export_file(shape=thumb_shape, fname=path.join(r"..", "things", r"debug_thumb_shape"))
        thumb_connector_shape = self.thumb_connectors()
        if self.debug_exports:
             self.g.export_file(shape=thumb_connector_shape, fname=path.join(r"..", "things", r"debug_thumb_connector_shape"))

        thumb_wall_shape = self.walls(skeleton=self.p.skeletal)
        thumb_wall_shape = self.g.union([thumb_wall_shape, *self.parent.screw_insert_outers(thumb=True)])
        thumb_connection_shape = self.connection(skeleton=self.p.skeletal)

        if self.debug_exports:
            thumb_test = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])
            self.g.export_file(shape=thumb_test, fname=path.join(r"..", "things", r"debug_thumb_test_{}_shape".format(self.side)))

        thumb_section = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])
        thumb_section = self.g.difference(thumb_section, self.screw_insert_holes())

        return thumb_section