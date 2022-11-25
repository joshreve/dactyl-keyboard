from clusters.default import DefaultCluster
import json
import os
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import clusters.trackball_cluster_abc as ca
from typing import Any, Sequence

def debugprint(data):
    pass
    # print



@dataclass_json
@dataclass
class OrbylClusterParameters(ca.TrackballClusterParametersBase):
    name: str = 'TRACKBALL_ORBYL'

    package: str = 'clusters.trackball_orbyl'
    class_name: str = 'OrbylCluster'

    Uwidth: float = 1.2
    Uheight: float = 1.2
    key_diameter: float = 70
    translation_offset: Sequence[float] = (0, 0, 10)
    rotation_offset: Sequence[float] = (0, 0, 0)
    key_translation_offsets: Sequence[Sequence[float]] = (
        (0.0, 0.0, -8.0),
        (0.0, 0.0, -8.0),
        (0.0, 0.0, -8.0),
        (0.0, 0.0, -8.0),
    )
    key_rotation_offsets: Sequence[Sequence[float]] = (
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    )

    thumb_screw_xy_locations: Sequence[Sequence[float]] = ((-53, -68),)
    separable_thumb_screw_xy_locations: Sequence[Sequence[float]] = (
        (-53, -68), (-66, 8), (10, -40)
    )


class OrbylCluster(ca.TrackballClusterBase):
    parameter_type = OrbylClusterParameters
    num_keys = 4
    is_tb = True

    @staticmethod
    def name():
        return "TRACKBALL_ORBYL"

    def position_rotation(self):
        rot = [10, -15, 5]
        pos = self.thumborigin()
        # Changes size based on key diameter around ball, shifting off of the top left cluster key.
        shift = [-.9 * self.tp.key_diameter/2 + 27 - 42, -.1 * self.tp.key_diameter / 2 + 3 - 20, -5]
        for i in range(len(pos)):
            pos[i] = pos[i] + shift[i] + self.tp.translation_offset[i]

        for i in range(len(rot)):
            rot[i] = rot[i] + self.tp.rotation_offset[i]

        return pos, rot

    def track_place(self, shape):
        pos, rot = self.position_rotation()
        shape = self.g.rotate(shape, rot)
        shape = self.g.translate(shape, pos)
        return shape

    def tl_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 0])
        t_off = self.tp.key_translation_offsets[0]
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[0])
        shape = self.g.translate(shape, (t_off[0], t_off[1] + self.tp.key_diameter / 2, t_off[2]))
        shape = self.g.rotate(shape, [0, 0, -80])
        shape = self.track_place(shape)

        return shape

    def mr_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 0])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[1])
        t_off = self.tp.key_translation_offsets[1]
        shape = self.g.translate(shape, (t_off[0], t_off[1] + self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0, 0, -130])
        shape = self.track_place(shape)

        return shape

    def br_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 180])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[2])
        t_off = self.tp.key_translation_offsets[2]
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0, 0, -180])
        shape = self.track_place(shape)

        return shape

    def bl_place(self, shape):
        debugprint('thumb_bl_place()')
        shape = self.g.rotate(shape, [0, 0, 180])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[3])
        t_off = self.tp.key_translation_offsets[3]
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0, 0, -230])
        shape = self.track_place(shape)

        return shape

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        return self.g.union([
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])),
            self.mr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_mr_rotation])),
            self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
            self.br_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_br_rotation])),
        ])

    def thumb_fx_layout(self, shape):
        return self.g.union([
            self.tl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_tr_rotation])),
            self.mr_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_mr_rotation])),
            self.bl_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_bl_rotation])),
            self.br_place(self.g.rotate(shape, [0, 0, self.tp.thumb_plate_br_rotation])),
        ])

    def thumbcaps(self):
        t1 = self.thumb_1x_layout(self.pl.sa_cap(1))
        return t1

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) + self.pl.adjustable_plate_size(self.tp.Uwidth) - self.p.post_adj,
                                 ((self.p.mount_height / 2) + self.pl.adjustable_plate_size(self.tp.Uheight)) - self.p.post_adj, 0]
                                )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) - self.pl.adjustable_plate_size(self.tp.Uwidth) + self.p.post_adj,
                                 ((self.p.mount_height / 2) + self.pl.adjustable_plate_size(self.tp.Uheight)) - self.p.post_adj, 0]
                                )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.pl.web_post(),
                                [-(self.p.mount_width / 2) - self.pl.adjustable_plate_size(self.tp.Uwidth) + self.p.post_adj,
                                 -((self.p.mount_height / 2) + self.pl.adjustable_plate_size(self.tp.Uheight)) + self.p.post_adj, 0]
                                )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.pl.web_post(),
                                [(self.p.mount_width / 2) + self.pl.adjustable_plate_size(self.tp.Uwidth) - self.p.post_adj,
                                 - ((self.p.mount_height / 2) + self.pl.adjustable_plate_size(self.tp.Uheight)) + self.p.post_adj, 0]
                                )

    def tb_post_r(self):
        debugprint('post_r()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [1.0*(radius - self.p.post_adj), 0.0*(radius - self.p.post_adj), 0]
                                )

    def tb_post_tr(self):
        debugprint('post_tr()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [0.5*(radius - self.p.post_adj), 0.866*(radius - self.p.post_adj), 0]
                                )


    def tb_post_tl(self):
        debugprint('post_tl()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [-0.5*(radius - self.p.post_adj), 0.866*(radius - self.p.post_adj), 0]
                                )


    def tb_post_l(self):
        debugprint('post_l()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [-1.0*(radius - self.p.post_adj), 0.0*(radius - self.p.post_adj), 0]
                                )

    def tb_post_bl(self):
        debugprint('post_bl()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [-0.5*(radius - self.p.post_adj), -0.866*(radius - self.p.post_adj), 0]
                                )


    def tb_post_br(self):
        debugprint('post_br()')
        radius = self.p.ball_diameter/2+self.p.ball_wall_thickness + self.p.ball_gap
        return self.g.translate(self.pl.web_post(),
                                [0.5*(radius - self.p.post_adj), -0.866*(radius - self.p.post_adj), 0]
                                )

    def thumb(self):
        shape = self.thumb_1x_layout(self.pl.single_plate())
        shape = self.g.union([shape, self.thumb_fx_layout(self.pl.adjustable_square_plate(Uwidth=self.tp.Uwidth, Uheight=self.tp.Uheight))])

        # shape = tbjs_thumb_fx_layout(self.g.rotate(self.sh.single_plate(), [0.0, 0.0, -90]))
        # shape = tbjs_thumb_fx_layout(adjustable_square_plate(Uwidth=self.tp.Uwidth, Uheight=self.tp.Uheight))
        # shape = self.g.add([shape, *tbjs_thumb_fx_layout(adjustable_square_plate(Uwidth=self.tp.Uwidth, Uheight=self.tp.Uheight))])

        # shape = self.g.union([shape, trackball_layout(trackball_socket())])
        # shape = tbjs_thumb_1x_layout(self.sh.single_plate())
        return shape


    def thumb_connectors(self):
        print('thumb_connectors()')
        hulls = []

        # bottom 2 to tb
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.track_place(self.tb_post_l()),
                    self.bl_place(self.thumb_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.bl_place(self.thumb_post_tr()),
                    self.br_place(self.thumb_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.br_place(self.thumb_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.br_place(self.thumb_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.mr_place(self.thumb_post_br()),
                    self.track_place(self.tb_post_r()),
                    self.mr_place(self.thumb_post_bl()),
                    self.tl_place(self.thumb_post_br()),
                    self.track_place(self.tb_post_r()),
                    self.tl_place(self.thumb_post_bl()),
                    self.track_place(self.tb_post_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        # bottom left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.bl_place(self.thumb_post_tr()),
                    self.br_place(self.thumb_post_tl()),
                    self.bl_place(self.thumb_post_br()),
                    self.br_place(self.thumb_post_bl()),
                ]
            )
        )

        # bottom right
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.thumb_post_tr()),
                    self.mr_place(self.thumb_post_br()),
                    self.br_place(self.thumb_post_br()),
                    self.mr_place(self.thumb_post_tr()),
                ]
            )
        )
        # top right
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.mr_place(self.thumb_post_bl()),
                    self.tl_place(self.thumb_post_br()),
                    self.mr_place(self.thumb_post_tl()),
                    self.tl_place(self.thumb_post_tr()),
                ]
            )
        )

        return self.g.union(hulls)


    def walls(self, skeleton=False):
    # def tbjs_thumb_walls(skeleton=False):
        print('thumb_walls()')
        # thumb, walls
        shape = self.parent.wall_brace(
            self.mr_place, .5, 1, self.thumb_post_tr(),
            (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0, -1, self.pl.web_post_bl(),
        )
        shape = self.g.union([shape, self.parent.wall_brace(
            self.mr_place, .5, 1, self.thumb_post_tr(),
            self.br_place, 0, -1, self.thumb_post_br(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.br_place, 0, -1, self.thumb_post_br(),
            self.br_place, 0, -1, self.thumb_post_bl(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.br_place, 0, -1, self.thumb_post_bl(),
            self.bl_place, 0, -1, self.thumb_post_br(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.bl_place, 0, -1, self.thumb_post_br(),
            self.bl_place, -1, -1, self.thumb_post_bl(),
        )])

        shape = self.g.union([shape, self.parent.wall_brace(
            self.track_place, -1.5, 0, self.tb_post_tl(),
            (lambda sh: self.parent.left_key_place(sh, self.p.cornerrow, -1, low_corner=True)), -1, 0,
            self.pl.web_post(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.track_place, -1.5, 0, self.tb_post_tl(),
            self.track_place, -1, 0, self.tb_post_l(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.track_place, -1, 0, self.tb_post_l(),
            self.bl_place, -1, 0, self.thumb_post_tl(),
        )])
        shape = self.g.union([shape, self.parent.wall_brace(
            self.bl_place, -1, 0, self.thumb_post_tl(),
            self.bl_place, -1, -1, self.thumb_post_bl(),
        )])

        return shape

    def connection(self, skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        hulls = []
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.parent.left_key_place(self.pl.web_post(), self.p.lastrow - 1, -1, low_corner=True),                # self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        hulls.append(
            self.g.triangle_hulls(
                [
                    self.parent.key_place(self.pl.web_post_bl(), 0, self.p.cornerrow),
                    self.tl_place(self.thumb_post_bl()),
                    self.parent.key_place(self.pl.web_post_br(), 0, self.p.cornerrow),
                    self.tl_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_bl(), 1, self.p.cornerrow),
                    self.tl_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_br(), 1, self.p.cornerrow),
                    self.tl_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.tl_place(self.thumb_post_tr()),
                    self.parent.key_place(self.pl.web_post_bl(), 2, self.p.lastrow),
                    self.mr_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_br(), 2, self.p.lastrow),
                    self.parent.key_place(self.pl.web_post_bl(), 3, self.p.lastrow),
                    self.mr_place(self.thumb_post_tr()),
                    self.mr_place(self.thumb_post_tl()),
                    self.parent.key_place(self.pl.web_post_br(), 2, self.p.lastrow),

                ]
            )
        )
        shape = self.g.union(hulls)
        return shape


    def thumb_pcb_plate_cutouts(self):
        return self.thumb_1x_layout(self.pl.plate_pcb_cutout())
