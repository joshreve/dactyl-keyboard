import json
from os import path
import numpy as np
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from abc import ABC
from typing import Any, Sequence, Tuple, Optional
# from src.dactyl_manuform import ParametersBase

def debugprint(data):
    pass
    # print


@dataclass_json
@dataclass
class OLEDBaseParameters:
# class OLEDBaseParameters(ParametersBase):

    package: str = 'oled.oled_abc'
    class_name: str = 'OLEDBase'

    name: str = 'OLED_ABC'

    vertical: bool = True
    mount_width: float = 12.5  # whole OLED width
    mount_height: float = 39.0  # whole OLED length
    mount_rim: float = 2.0
    mount_depth: float = 7.0
    mount_cut_depth: float = 20.0

    center_row: Optional[float] = 1.25  # if not None, this will override the oled_mount_location_xyz and oled_mount_rotation_xyz settings
    translation_offset: Sequence[float] = (0, 0, 4)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    rotation_offset: Sequence[float] = (0, 0, 0)

    # only used of center row not defined
    mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if center_row is not None
    mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if center_row is not None

    # values override default configs
    left_wall_lower_y_offset: Optional[float] = 12.0
    left_wall_lower_z_offset: Optional[float] = 5.0
    left_wall_x_offset: Optional[float] = 24.0
    left_wall_z_offset: Optional[float] = 0.0




class OLEDBase(ABC):
    parameter_type = OLEDBaseParameters

    def __init__(self, parent, o_parameters=None):
        self.g = parent.g
        self.p = parent.p
        self.parent = parent
        self.sh = parent.pl

        if o_parameters is None:
            o_parameters = self.parameter_type()

        self.op = o_parameters
        self.process_parameters()
        self.set_overrides()


    def set_overrides(self):
        if self.op.left_wall_lower_y_offset is not None:
            self.p.left_wall_ext_lower_y_offset = self.op.left_wall_lower_y_offset

        if self.op.left_wall_lower_z_offset is not None:
            self.p.left_wall_ext_lower_z_offset = self.op.left_wall_lower_z_offset

        if self.op.left_wall_x_offset is not None:
            self.p.left_wall_ext_x_offset = self.op.left_wall_x_offset

        if self.op.left_wall_z_offset is not None:
            self.p.left_wall_ext_z_offset = self.op.left_wall_z_offset


    def process_parameters(self):
        if self.op.center_row is not None:
            base_pt1 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row - 1
            )
            base_pt2 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row + 1
            )
            base_pt0 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row
            )

            mount_location_xyz = np.array(self.op.mount_location_xyz)
            mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-self.p.left_wall_ext_x_offset / 2), 0, 0)) + np.array(self.op.translation_offset)

            mount_location_xyz[2] = (mount_location_xyz[2] + base_pt0[2]) / 2
            self.op.mount_location_xyz = mount_location_xyz

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

            self.op.mount_rotation_xyz = np.rad2deg((angle_x, 0, -angle_z)) + np.array(
                self.op.rotation_offset)


    @staticmethod
    def name():
        return "ABC"

    def oled_position_rotation(self):
        if self.op.center_row is not None:

            base_pt1 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row - 1
            )
            base_pt2 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row + 1
            )
            base_pt0 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row
            )

            oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-self.p.left_wall_ext_x_offset / 2), 0, 0)) + np.array(self.op.translation_offset)
            oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

            if self.op.vertical:
                oled_mount_rotation_xyz = np.rad2deg((angle_x, 0, -angle_z)) + np.array(self.op.rotation_offset)
            else:
                oled_mount_rotation_xyz = (0, np.rad2deg(angle_x), -90) + np.array(self.op.rotation_offset)

            return oled_mount_location_xyz, oled_mount_rotation_xyz

        else:
            
            return self.op.mount_location_xyz, self.op.mount_rotation_xyz



    def oled_mount_frame(self):
        hole = self.g.box(1, 1, 1)
        shape = self.g.box(1, 1, 1)
        return hole, shape

    def extra_parts(self):
        self.g.export_file(shape=self.oled_mount_frame()[1],
                fname=path.join(self.p.save_path, self.p.config_name + r"_oled_test"))




        # if self.p.oled_mount_type == 'CLIP':
        #     oled_mount_location_xyz = (0.0, 0.0, -self.p.oled_config.oled_mount_depth / 2)
        #     oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
        #     self.g.export_file(shape=self.oled_clip(), fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip"))
        #     self.g.export_file(shape=self.oled_clip_mount_frame()[1],
        #             fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip_test"))
        #     self.g.export_file(shape=self.g.union((self.oled_clip_mount_frame()[1], self.oled_clip())),
        #             fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip_assy_test"))

