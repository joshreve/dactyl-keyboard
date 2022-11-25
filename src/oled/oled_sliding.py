import json
import os
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Any, Sequence, Tuple, Optional
import oled.oled_abc as oa

def debugprint(data):
    pass
    # print


@dataclass_json
@dataclass
class OLEDSlidingParameters(oa.OLEDBaseParameters):
    package: str = 'oled.oled_sliding'
    class_name: str = 'OLEDSliding'
    name: str = 'SLIDING'

    vertical: bool = True
    mount_width: float = 12.5  # whole OLED width
    mount_height: float = 25.0  # whole OLED length
    mount_rim: float = 2.5
    mount_depth: float = 8.0
    mount_cut_depth: float = 20.0

    center_row: Optional[float] = 1.25  # if not None, this will override the oled_mount_location_xyz and oled_mount_rotation_xyz settings
    translation_offset: Sequence[float] = (0, 0, 4)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    rotation_offset: Sequence[float] = (0, 0, 0)

    # only used of center row not defined
    mount_location_xyz: Sequence[float] = (-78.0, 10.0, 41.0)  # will be overwritten if oled_center_row is not None
    mount_rotation_xyz: Sequence[float] = (6.0, 0.0, -3.0)  # will be overwritten if oled_center_row is not None

    # values override default configs
    left_wall_lower_y_offset: Optional[float] = 24.0
    left_wall_lower_z_offset: Optional[float] = 0.0
    left_wall_x_offset: Optional[float] = 12.0
    left_wall_z_offset: Optional[float] = 5.0


    # 'SLIDING' Parameters
    oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
    oled_edge_overlap_end: float = 6.5  # length from end of viewable screen to end of PCB
    oled_edge_overlap_connector: float = 5.5  # length from end of viewable screen to end of PCB on connection side.
    oled_edge_overlap_thickness: float = 2.5  # thickness of material over edge of PCB
    oled_edge_overlap_clearance: float = 2.5  # Clearance to insert PCB before laying down and sliding.
    oled_edge_chamfer: float = 2.0



class OLEDSliding(oa.OLEDBase):
    parameter_type = OLEDSlidingParameters



    @staticmethod
    def name():
        return "SLIDING"

    def oled_mount_frame(self):
        mount_ext_width = self.op.mount_width + 2 * self.op.mount_rim
        mount_ext_height = (
                self.op.mount_height + 2 * self.op.edge_overlap_end
                + self.op.edge_overlap_connector + self.op.edge_overlap_clearance
                + 2 *self.op.mount_rim
        )
        mount_ext_up_height = self.op.mount_height + 2 * self.op.mount_rim
        top_hole_start = -mount_ext_height / 2.0 + self.op.mount_rim + self.op.edge_overlap_end + self.op.edge_overlap_connector
        top_hole_length = self.op.mount_height

        hole = self.g.box(mount_ext_width, mount_ext_up_height, self.op.mount_cut_depth + .01)
        hole = self.g.translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

        hole_down = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_depth + self.op.mount_cut_depth / 2)
        hole_down = self.g.translate(hole_down, (0., 0., -self.op.mount_cut_depth / 4))
        hole = self.g.union([hole, hole_down])

        shape = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_depth)

        conn_hole_start = -mount_ext_height / 2.0 + self.op.mount_rim
        conn_hole_length = (
                self.op.edge_overlap_end + self.op.edge_overlap_connector
                + self.op.edge_overlap_clearance + self.op.thickness
        )
        conn_hole = self.g.box(self.op.mount_width, conn_hole_length + .01, self.op.mount_depth)
        conn_hole = self.g.translate(conn_hole, (
            0,
            conn_hole_start + conn_hole_length / 2,
            -self.op.edge_overlap_thickness
        ))

        end_hole_length = (
                self.op.edge_overlap_end + self.op.edge_overlap_clearance
        )
        end_hole_start = mount_ext_height / 2.0 - self.op.mount_rim - end_hole_length
        end_hole = self.g.box(self.op.mount_width, end_hole_length + .01, self.op.mount_depth)
        end_hole = self.g.translate(end_hole, (
            0,
            end_hole_start + end_hole_length / 2,
            -self.op.edge_overlap_thickness
        ))

        top_hole_start = -mount_ext_height / 2.0 + self.op.mount_rim + self.op.edge_overlap_end + self.op.edge_overlap_connector
        top_hole_length = self.op.mount_height
        top_hole = self.g.box(self.op.mount_width, top_hole_length,
                       self.op.edge_overlap_thickness + self.op.thickness - self.op.edge_chamfer)
        top_hole = self.g.translate(top_hole, (
            0,
            top_hole_start + top_hole_length / 2,
            (self.op.mount_depth - self.op.edge_overlap_thickness - self.op.thickness - self.op.edge_chamfer) / 2.0
        ))

        top_chamfer_1 = self.g.box(
            self.op.mount_width,
            top_hole_length,
            0.01
        )
        top_chamfer_2 = self.g.box(
            self.op.mount_width + 2 * self.op.edge_chamfer,
            top_hole_length + 2 * self.op.edge_chamfer,
            0.01
        )
        top_chamfer_1 = self.g.translate(top_chamfer_1, (0, 0, -self.op.edge_chamfer - .05))

        top_chamfer_1 = self.g.hull_from_shapes([top_chamfer_1, top_chamfer_2])

        top_chamfer_1 = self.g.translate(top_chamfer_1, (
            0,
            top_hole_start + top_hole_length / 2,
            self.op.mount_depth / 2.0 + .05
        ))

        top_hole = self.g.union([top_hole, top_chamfer_1])

        shape = self.g.difference(shape, [conn_hole, top_hole, end_hole])

        oled_mount_location_xyz, oled_mount_rotation_xyz = self.oled_position_rotation()

        shape = self.g.rotate(shape, oled_mount_rotation_xyz)
        shape = self.g.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = self.g.rotate(hole, oled_mount_rotation_xyz)
        hole = self.g.translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )

        return hole, shape

