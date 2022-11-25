from dataclasses_json import dataclass_json
from dataclasses import dataclass
import clusters.trackball_orbyl as tbob
from typing import Any, Sequence

def debugprint(data):
    pass
    # print



@dataclass_json
@dataclass
class WilderClusterParameters(tbob.OrbylClusterParameters):
    name: str = 'TRACKBALL_WILDER'

    package: str = 'clusters.trackball_wilder'
    class_name: str = 'WilderCluster'

    thumb_offsets: Sequence[float] = (6.0, -3.0, 7.0)
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
    post_offsets: Sequence[Sequence[float]] = (
        (14, -8, 3),
        (3, -9, -7),
        (-4, 4, -6),
        (-5, 18, 19)
    )




class WilderCluster(tbob.OrbylCluster):
    parameter_type = WilderClusterParameters
    num_keys = 4
    is_tb = True


    @staticmethod
    def name():
        return "TRACKBALL_WILD"

    def position_rotation(self):
        rot = [10, -15, 5]
        pos = self.thumborigin()
        # Changes size based on key diameter around ball, shifting off of the top left cluster key.
        shift = [-.9*self.tp.key_diameter/2+27-42, -.1*self.tp.key_diameter/2+3-20, -5]
        for i in range(len(pos)):
            pos[i] = pos[i] + shift[i] + self.tp.translation_offset[i]

        for i in range(len(rot)):
            rot[i] = rot[i] + self.tp.rotation_offset[i]

        return pos, rot


    def tl_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 0])
        t_off = self.tp.key_translation_offsets[0]
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[0])
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0,0,-80])
        shape = self.track_place(shape)

        return shape

    def mr_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 0])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[1])
        t_off = self.tp.key_translation_offsets[1]
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0,0,-150])
        shape = self.track_place(shape)

        return shape

    def br_place(self, shape):
        shape = self.g.rotate(shape, [0, 0, 180])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[2])
        t_off = self.tp.key_translation_offsets[2]
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0,0,-195])
        shape = self.track_place(shape)

        return shape

    def bl_place(self, shape):
        debugprint('thumb_bl_place()')
        shape = self.g.rotate(shape, [0, 0, 180])
        shape = self.g.rotate(shape, self.tp.key_rotation_offsets[3])
        t_off = self.tp.key_translation_offsets[3]
        shape = self.g.translate(shape, (t_off[0], t_off[1]+self.tp.key_diameter/2, t_off[2]))
        shape = self.g.rotate(shape, [0,0,-240])
        shape = self.track_place(shape)

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


    def get_extras(self, shape, pos):
        posts = [shape]
        all_pos = []
        for i in range(len(pos)):
            all_pos.append(pos[i] + self.tp.translation_offset[i])
        z_pos = abs(pos[2])
        for post_offset in self.post_offsets.copy():
            support_z = z_pos + post_offset[2]
            new_offsets = post_offset
            new_offsets[2] = -z_pos
            support = self.g.cylinder(1.5, support_z, 10)
            support = self.g.translate(support, all_pos)
            support = self.g.translate(support, new_offsets)
            base = self.g.cylinder(4, 1, 10)
            new_offsets[2] = 0.5 - all_pos[2]
            base = self.g.translate(base, all_pos)
            base = self.g.translate(base, new_offsets)
            posts.append(base)
            support = self.g.union([support, base])
            posts.append(support)
        return self.g.union(posts)
