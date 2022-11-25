import json
from os import path
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Any, Sequence, Tuple
import oled.oled_abc as oa

def debugprint(data):
    pass
    # print


@dataclass_json
@dataclass
class OLEDUndercutParameters(oa.OLEDBaseParameters):
    package: str = 'oled.oled_undercut'
    class_name: str = 'OLEDUndercut'
    name: str = 'UNDERCUT'

    vertical: bool = True
    mount_width: float = 12.5  # whole OLED width
    mount_height: float = 25.0  # whole OLED length
    mount_rim: float = 2.5
    mount_depth: float = 8.0
    mount_cut_depth: float = 20.0

    center_row: float = 1.25  # if not None, this will override the oled_mount_location_xyz and oled_mount_rotation_xyz settings
    translation_offset: Sequence[float] = (0, 0, 4)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    rotation_offset: Sequence[float] = (0, 0, 0)

    # only used of center row not defined
    mount_location_xyz: Sequence[float] = (-78.0, 10.0, 41.0)  # will be overwritten if oled_center_row is not None
    mount_rotation_xyz: Sequence[float] = (6.0, 0.0, -3.0)  # will be overwritten if oled_center_row is not None

    # values override default configs
    left_wall_lower_y_offset: float = 28.0
    left_wall_lower_z_offset: float = 0.0
    left_wall_x_offset: float = 12.0
    left_wall_z_offset: float = 5.0


    # 'UNDERCUT' Parameters
    mount_undercut: float = 1.0
    mount_undercut_thickness: float = 2.0


class OLEDUndercut(oa.OLEDBase):
    parameter_type = OLEDUndercutParameters

    @staticmethod
    def name():
        return "SLIDING"

    def oled_mount_frame(self):
        mount_ext_width = self.op.mount_width + 2 * self.op.mount_rim
        mount_ext_height = self.op.mount_height + 2 * self.op.mount_rim
        hole = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_cut_depth + .01)

        shape = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_depth)
        shape = self.g.difference(shape, [self.g.box(self.op.mount_width, self.op.mount_height, self.op.mount_depth + .1)])
        undercut = self.g.box(
            self.op.mount_width + 2 * self.op.mount_undercut,
            self.op.mount_height + 2 * self.op.mount_undercut,
            self.op.mount_depth)
        undercut = self.g.translate(undercut, (0., 0., -self.op.mount_undercut_thickness))
        shape = self.g.difference(shape, [undercut])

        oled_mount_location_xyz, oled_mount_rotation_xyz = self.oled_position_rotation()

        shape = self.g.rotate(shape, oled_mount_rotation_xyz)
        shape = self.g.translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                          )

        hole = self.g.rotate(hole, oled_mount_rotation_xyz)
        hole = self.g.translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                         )

        return hole, shape

