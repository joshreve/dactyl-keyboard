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
class TBIWParameters:
    # class OLEDBaseParameters(ParametersBase):

    package: str = 'oled.oled_abc'
    class_name: str = 'OLEDBase'

    name: str = 'OLED_ABC'

    ###################################
    ## Trackball in Wall             ##
    ###################################
    trackball_in_wall: bool = False  # Separate trackball option, placing it in the OLED area
    tbiw_ball_center_row: float = 0.2  # up from cornerrow instead of down from top
    tbiw_translational_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_rotation_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_left_wall_x_offset_override: float = 50.0
    tbiw_left_wall_z_offset_override: float = 0.0
    tbiw_left_wall_lower_x_offset: float = 0.0
    tbiw_left_wall_lower_y_offset: float = 0.0
    tbiw_left_wall_lower_z_offset: float = 0.0

    tbiw_oled_center_row: float = .75  # not none, offsets are from this position
    tbiw_oled_translation_offset: Sequence[float] = (
    -3.5, 0, 1.5)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    tbiw_oled_rotation_offset: Sequence[float] = (0, 0, 0)

    ##########################################################################
    ## Finger Trackball in Wall EXPERIMENTAL WIP!!!!                        ##
    ##########################################################################
    finger_trackball_in_wall: bool = False  # Separate trackball option, placing it in the OLED area
    tbiw_ball_center_column: float = 0.2  # up from cornerrow instead of down from top
    tbiw_top_wall_translational_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_top_wall_rotation_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_top_wall_y_offset_override: float = 50.0
    tbiw_top_wall_z_offset_override: float = 0.0
    tbiw_top_wall_extension_cols: float = 4


class Trackball_in_wall:

    def process_parameters(self):
        if low_corner:
            x_offset = self.p.tbiw_left_wall_lower_x_offset
            y_offset = self.p.tbiw_left_wall_lower_y_offset
            z_offset = self.p.tbiw_left_wall_lower_z_offset
        else:
            x_offset = 0.0
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([
            self.p.tbiw_left_wall_x_offset_override - x_offset,
            -y_offset,
            self.p.tbiw_left_wall_z_offset_override + z_offset
        ]))

    def tbiw_position_rotation(self):
        base_pt1 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row - 1
        )
        base_pt2 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row + 1
        )
        base_pt0 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row
        )

        left_wall_x_offset = self.p.tbiw_left_wall_x_offset_override

        tbiw_mount_location_xyz = (
                (np.array(base_pt1) + np.array(base_pt2)) / 2.
                + np.array(((-left_wall_x_offset / 2), 0, 0))
                + np.array(self.p.tbiw_translational_offset)
        )

        angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
        angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
        tbiw_mount_rotation_xyz = np.rad2deg((angle_x, 0, angle_z)) + np.array(self.p.tbiw_rotation_offset)

        return tbiw_mount_location_xyz, tbiw_mount_rotation_xyz


    def generate_trackball_in_wall(self):
        pos, rot = self.tbiw_position_rotation()
        return self.generate_trackball_components(pos, rot)

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
