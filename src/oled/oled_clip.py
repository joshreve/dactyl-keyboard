import json
from os import path
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Any, Sequence, Tuple, Optional
import oled.oled_abc as oa

def debugprint(data):
    pass
    # print

@dataclass_json
@dataclass
class OLEDClipParameters(oa.OLEDBaseParameters):
    package: str = 'oled.oled_clip'
    class_name: str = 'OLEDClip'
    name: str = 'CLIP'

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

    # 'CLIP' Parameters
    oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
    mount_bezel_thickness: float = 3.5  # z thickness of clip bezel
    mount_bezel_chamfer: float = 2.0  # depth of the 45 degree chamfer
    mount_connector_hole: float = 6.0
    screen_start_from_conn_end: float = 6.5
    screen_length: float = 24.5
    screen_width: float = 10.5
    clip_thickness: float = 1.5
    clip_width: float = 6.0
    clip_overhang: float = 1.0
    clip_extension: float = 5.0
    clip_width_clearance: float = 0.5
    clip_undercut: float = 0.5
    clip_undercut_thickness: float = 2.5
    clip_y_gap: float = .2
    clip_z_gap: float = .2


class OLEDClip(oa.OLEDBase):
    parameter_type = OLEDClipParameters

    @staticmethod
    def name():
        return "CLIP"

    def oled_mount_frame(self):
        mount_ext_width = self.op.mount_width + 2 * self.op.mount_rim
        mount_ext_height = (
                self.op.mount_height + 2 * self.op.clip_thickness
                + 2 * self.op.clip_undercut + 2 * self.op.clip_overhang + 2 * self.op.mount_rim
        )
        hole = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_cut_depth + .01)

        shape = self.g.box(mount_ext_width, mount_ext_height, self.op.mount_depth)
        shape = self.g.difference(shape, [
            self.g.box(self.op.mount_width, self.op.mount_height,
                       self.op.mount_depth + .1)])

        clip_slot = self.g.box(
            self.op.clip_width + 2 * self.op.clip_width_clearance,
            self.op.mount_height + 2 * self.op.clip_thickness + 2 * self.op.clip_overhang,
            self.op.mount_depth + .1
        )

        shape = self.g.difference(shape, [clip_slot])

        clip_undercut = self.g.box(
            self.op.clip_width + 2 * self.op.clip_width_clearance,
            self.op.mount_height + 2 * self.op.clip_thickness + 2 * self.op.clip_overhang + 2 * self.op.clip_undercut,
            self.op.mount_depth + .1
        )

        clip_undercut = self.g.translate(clip_undercut, (0., 0., self.op.clip_undercut_thickness))
        shape = self.g.difference(shape, [clip_undercut])

        plate = self.g.box(
            self.op.mount_width + .1,
            self.op.mount_height - 2 * self.op.mount_connector_hole,
            self.op.mount_depth - self.op.oled_thickness
        )
        plate = self.g.translate(plate, (0., 0., -self.op.oled_thickness / 2.0))
        shape = self.g.union([shape, plate])

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

    def extra_parts(self):
        self.parent.extra_parts['OLED_Clip'] = self.oled_clip()

    def oled_clip(self):
        mount_ext_width = self.op.mount_width + 2 * self.op.mount_rim
        mount_ext_height = (
                self.op.mount_height + 2 * self.op.clip_thickness + 2 * self.op.clip_overhang
                + 2 * self.op.clip_undercut + 2 * self.op.mount_rim
        )

        oled_leg_depth = self.op.mount_depth + self.op.clip_z_gap

        shape = self.g.box(mount_ext_width - .1, mount_ext_height - .1, self.op.mount_bezel_thickness)
        shape = self.g.translate(shape, (0., 0., self.op.mount_bezel_thickness / 2.))

        hole_1 = self.g.box(
            self.op.screen_width + 2 * self.op.mount_bezel_chamfer,
            self.op.screen_length + 2 * self.op.mount_bezel_chamfer,
            .01
        )
        hole_2 = self.g.box(self.op.screen_width, self.op.screen_length,
                            2.05 * self.op.mount_bezel_thickness)
        hole = self.g.hull_from_shapes([hole_1, hole_2])

        shape = self.g.difference(shape,
                                  [self.g.translate(hole, (0., 0., self.op.mount_bezel_thickness))])

        clip_leg = self.g.box(self.op.clip_width, self.op.clip_thickness,
                              oled_leg_depth)
        clip_leg = self.g.translate(clip_leg, (
            0.,
            0.,
            # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
            -oled_leg_depth / 2.
        ))

        latch_1 = self.g.box(
            self.op.clip_width,
            self.op.clip_overhang + self.op.clip_thickness,
            .01
        )
        latch_2 = self.g.box(
            self.op.clip_width,
            self.op.clip_thickness / 2,
            self.op.clip_extension
        )
        latch_2 = self.g.translate(latch_2, (
            0.,
            -(
                        -self.op.clip_thickness / 2 + self.op.clip_thickness + self.op.clip_overhang) / 2,
            -self.op.clip_extension / 2
        ))
        latch = self.g.hull_from_shapes([latch_1, latch_2])
        latch = self.g.translate(latch, (
            0.,
            self.op.clip_overhang / 2,
            -oled_leg_depth
        ))

        clip_leg = self.g.union([clip_leg, latch])

        clip_leg = self.g.translate(clip_leg, (
            0.,
            (
                        self.op.mount_height + 2 * self.op.clip_overhang + self.op.clip_thickness) / 2 - self.op.clip_y_gap,
            0.
        ))

        shape = self.g.union([shape, clip_leg, self.g.mirror(clip_leg, 'XZ')])

        return shape


    def extra_parts(self):
        save_mount_location_xyz = self.op.mount_location_xyz
        save_mount_rotation_xyz = self.op.mount_rotation_xyz
        self.op.mount_location_xyz = (0.0, 0.0, -self.p.oled_config.oled_mount_depth / 2)
        self.op.oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
        self.g.export_file(shape=self.oled_clip(), fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip"))
        self.g.export_file(shape=self.oled_mount_frame()[1],
                fname=path.join(self.p.save_path, self.p.config_name + r"_oled_test"))
        self.g.export_file(shape=self.g.union((self.oled_mount_frame()[1], self.oled_clip())),
                fname=path.join(self.p.save_path, self.p.config_name + r"_oled_assy_test"))
        self.op.mount_location_xyz = save_mount_location_xyz
        self.op.mount_rotation_xyz = save_mount_rotation_xyz
