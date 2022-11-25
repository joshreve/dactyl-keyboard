# import numpy as np
# import os.path as path
# import os
# import copy
# import importlib
from helpers import helpers_abc
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import os.path as path
import copy
from typing import Any, Sequence, Tuple, Optional
# from src.dactyl_manuform import ParametersBase

## LISTING VARIABLES IN SHAPE CLASS FOR PARAMETER SEPARATION CONSIDERATIONS.
# shape_vars=[
########################
# PLATE INTERFACE DIMENSIONS
########################
# mount_thickness
# mount_width
# mount_height
# sa_length
# plate_thickness
# adjustable_plate_height
# double_plate_height

########################
# PLATE INTERNAL DIMENSIONS
########################
# keyswitch_width
# keyswitch_height

# clip_undercut
# undercut_transition
# notch_width
#
# plate_file
# plate_offset
# adjustable_plate_height
# double_plate_height
#
########################
# WEB AND POST GEOMETRIES
########################
# post_size
# web_thickness
# post_adj
#
#
########################
# PLATE HOLES FOR PCB MOUNT
########################
# plate_holes_width
# plate_holes_height
# plate_holes_xy_offset
# plate_holes_diameter
# plate_holes_depth
#
########################
# PLATE REPRESENTATION
########################
# plate_pcb_size
# plate_pcb_offset
# pcb_hole_diameter
# pcb_hole_pattern_width
# pcb_hole_pattern_height
# pcb_width
# pcb_height
# pcb_thickness
#
########################
# TRACKBALL GEOMETRIES
########################
# trackball_modular
# ball_diameter
# ball_gap
# ball_wall_thickness
# trackball_modular_clearance
# trackball_modular_lip_width
# trackball_hole_diameter
# trackball_hole_height
# hole_diameter
#
########################
# PARTS LOAD PATH
########################
# parts_path
#
# ]

debug_trace=False


def usize_dimension(Usize=1.5):
    sa_length = 18.5
    return Usize * sa_length


def debugprint(info):
    if debug_trace:
        print(info)


    #################
    ## Switch Hole ##
    #################

    # plate options are
    # 'HOLE' = a square hole.  Also useful for applying custom plate files.
    # 'NUB' = original side nubs.
    # 'UNDERCUT' = snap fit undercut.  May require CLIP_THICKNESS and possibly CLIP_UNDERCUT tweaking
    #       and/or filing to get proper snap.
    # 'NOTCH' = snap fit undercut only near switch clip.  May require CLIP_THICKNESS and possibly CLIP_UNDERCUT
    #       tweaking and/or filing to get proper snap.
    # 'HS_NUB' = hot swap underside with nubs.
    # 'HS_UNDERCUT' = hot swap underside with undercut. Does not generate properly.  Hot swap step needs to be modified.
    # 'HS_NOTCH' = hot swap underside with notch.  Does not generate properly.  Hot swap step needs to be modified.
    # 'plate_style = NUB'
    plate_style: str = 'NOTCH'



    hole_keyswitch_height: float = 14.0
    hole_keyswitch_width: float = 14.0

    nub_keyswitch_height: float = 14.4
    nub_keyswitch_width: float = 14.4

    undercut_keyswitch_height: float = 14.0
    undercut_keyswitch_width: float = 14.0
    notch_width: float = 6.0  # If using notch, it is identical to undecut, but only locally by the switch clip

    sa_profile_key_height: float = 12.7
    sa_length: float = 18.5
    sa_double_length: float = 37.5
    plate_thickness: float = 4 + 1.1

    plate_rim: float = 1.5 + 0.5
    # Undercut style dimensions
    clip_thickness: float = 1.1
    clip_undercut: float = 1.0
    undercut_transition: float = .2  # NOT FUNCTIONAL WITH OPENSCAD, ONLY WORKS WITH CADQUERY

    # Custom plate step file




@dataclass_json
@dataclass
class HolePlateParameters:
    package: str = 'shapes.plates'
    class_name: str = 'HolePlate'

    keyswitch_height: float = 14.0
    keyswitch_width: float = 14.0
    plate_thickness: float = 4 + 1.1

    sa_profile_key_height: float = 12.7
    sa_length: float = 18.5
    sa_double_length: float = 37.5

    plate_rim: float = 2.0

    hotswap: bool = False

    ###################################
    ## CUSTOM GEOMETRY ON PLATE
    ###################################

    plate_file_name: Optional[str] = None
    plate_offset: float = 0.0

    ###################################
    ## HOLES ON PLATE FOR PCB MOUNT
    ###################################
    plate_holes: bool = False
    plate_holes_xy_offset: Sequence[float] = (0.0, 0.0)
    plate_holes_width: float = 15.0
    plate_holes_height: float = 15.0
    plate_holes_diameter: float = 1.6
    plate_holes_depth: float = 20.0

    ###################################
    ## EXPERIMENTAL
    plate_pcb_clear: bool = False
    plate_pcb_size: Sequence[float] = (18.5, 18.5, 5)
    plate_pcb_offset: Sequence[float] = (0, 0, 0)  # this is off of the back of the plate size.
    ###################################

    ###################################
    ## SHOW PCB FOR FIT CHECK
    ###################################
    pcb_width: float = 18.0
    pcb_height: float = 18.0
    pcb_thickness: float = 1.5
    pcb_hole_diameter: float = 2
    pcb_hole_pattern_width: float = 14.3
    pcb_hole_pattern_height: float = 14.3



class HolePlate:
    g: helpers_abc
    # parent: dm.DactylBase

    parameter_type = HolePlateParameters
    symmetric = True
    
    def __init__(self, parent, p_parameters=None):
        self._parent = parent
        self.p = parent.p
        self.g = parent.g

        if p_parameters is None:
            self.pp = self.parameter_type()
        else:
            self.pp = p_parameters

        self.process_parameters()

        self._plate = None

    def process_parameters(self):
        # Process parameters and feed the mount dimensions back
        print('SETTING PLATE PARAMETERS')
        self.pp.plate_file = None

        if self.pp.hotswap:
            self.pp.plate_file_name = r"hot_swap_plate"
            self.p.symmetric = False
            
        if self.pp.plate_file_name is not None:
            self.symmetric = False
            self.pp.plate_file = path.join(self.p.parts_path, self.pp.plate_file_name)

        self.p.mount_width = self.pp.keyswitch_width + 2 * self.pp.plate_rim
        self.p.mount_height = self.pp.keyswitch_height + 2 * self.pp.plate_rim
        self.p.mount_thickness = self.pp.plate_thickness

        self.pp.double_plate_height = (self.pp.sa_double_length - self.p.mount_height) / 3

        self.p.cap_top_height = self.pp.plate_thickness + self.pp.sa_profile_key_height

    def plate_shape(self):
        return self.plate_square_hole()

    def plate_square_hole(self):
        plate = self.g.box(self.p.mount_width, self.p.mount_height, self.p.mount_thickness)
        plate = self.g.translate(plate, (0.0, 0.0, self.p.mount_thickness / 2.0))

        shape_cut = self.g.box(self.pp.keyswitch_width, self.pp.keyswitch_height, self.p.mount_thickness * 2 + .02)
        shape_cut = self.g.translate(shape_cut, (0.0, 0.0, self.p.mount_thickness - .01))

        plate = self.g.difference(plate, [shape_cut])

        return plate

    def single_plate(self):
        if self._plate is None:
            plate = self.plate_shape()

            if self.pp.plate_holes:
                plate = self.plate_screw_holes(
                    plate,
                    plate_holes_width=self.pp.plate_holes_width, plate_holes_height=self.pp.plate_holes_height,
                    plate_holes_xy_offset=self.pp.plate_holes_xy_offset,
                    plate_holes_diameter=self.pp.plate_holes_diameter, plate_holes_depth=self.pp.plate_holes_depth
                )

            if self.pp.plate_file is not None:
                plate = self.add_plate_file(plate)

            self._plate = plate

        else:
            plate = self._plate
            
        if self._parent.side == "left" and not self.symmetric:
            plate = self.g.mirror(self._plate, 'YZ')

        return plate

    def add_plate_file(self, plate):
        socket = self.g.import_file(self.pp.plate_file)
        socket = self.g.translate(socket, [0, 0, self.pp.plate_thickness + self.pp.plate_offset])
        plate = self.g.union([plate, socket])
        return plate
        

    def plate_screw_holes(
            self, plate,
            plate_holes_width=None, plate_holes_height=None, plate_holes_xy_offset=None,
            plate_holes_diameter=None, plate_holes_depth=None
    ):
        half_width = plate_holes_width / 2.
        half_height = plate_holes_height / 2.

        if self._parent.side == 'right':
            x_off = plate_holes_xy_offset[0]
        else:
            x_off = -plate_holes_xy_offset[0]

        y_off = plate_holes_xy_offset[1]
        holes = [
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off + half_width, y_off + half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off - half_width, y_off + half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off - half_width, y_off - half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off + half_width, y_off - half_height, plate_holes_depth / 2 - .01)
            ),
        ]

        plate = self.g.difference(plate, holes)

        return plate

    def plate_pcb_cutout(self):
        shape = self.g.box(*self.pp.plate_pcb_size)
        shape = self.g.translate(shape, (0, 0, -self.pp.plate_pcb_size[2] / 2))
        shape = self.g.translate(shape, self.pp.plate_pcb_offset)

        if self._parent.side == "left":
            shape = self.g.mirror(shape, 'YZ')

        return shape


    ################
    ## SA Keycaps ##
    ################

    def sa_cap(self, Usize=1):
        # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
        # sa_length = 18.25

        if Usize == 1:
            bl2 = 18.5 / 2
            bw2 = 18.5 / 2
            m = 17 / 2
            pl2 = 6
            pw2 = 6

        elif Usize == 2:
            bl2 = self.pp.sa_length
            bw2 = self.pp.sa_length / 2
            m = 0
            pl2 = 16
            pw2 = 6

        elif Usize == 1.5:
            bl2 = self.pp.sa_length / 2
            bw2 = 27.94 / 2
            m = 0
            pl2 = 6
            pw2 = 11

        k1 = self.g.polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = self.g.extrude_poly(outer_poly=k1, height=0.1)
        k1 = self.g.translate(k1, (0, 0, 0.05))
        k2 = self.g.polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = self.g.extrude_poly(outer_poly=k2, height=0.1)
        k2 = self.g.translate(k2, (0, 0, 12.0))
        if m > 0:
            m1 = self.g.polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = self.g.extrude_poly(outer_poly=m1, height=0.1)
            m1 = self.g.translate(m1, (0, 0, 6.0))
            key_cap = self.g.hull_from_shapes((k1, k2, m1))
        else:
            key_cap = self.g.hull_from_shapes((k1, k2))

        key_cap = self.g.translate(key_cap, (0, 0, 5 + self.pp.plate_thickness))

        if self.p.show_pcbs:
            key_cap = self.g.add([key_cap, self.key_pcb()])

        return key_cap

    def key_pcb(self):
        shape = self.g.box(self.pp.pcb_width, self.pp.pcb_height, self.pp.pcb_thickness)
        shape = self.g.translate(shape, (0, 0, -self.pp.pcb_thickness / 2))
        hole = self.g.cylinder(self.pp.pcb_hole_diameter / 2, self.pp.pcb_thickness + .2)
        hole = self.g.translate(hole, (0, 0, -(self.pp.pcb_thickness + .1) / 2))
        holes = [
            self.g.translate(hole, (self.pp.pcb_hole_pattern_width / 2, self.pp.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (-self.pp.pcb_hole_pattern_width / 2, self.pp.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (-self.pp.pcb_hole_pattern_width / 2, -self.pp.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (self.pp.pcb_hole_pattern_width / 2, -self.pp.pcb_hole_pattern_height / 2, 0)),
        ]
        shape = self.g.difference(shape, holes)

        return shape

    ####################
    ## Web Connectors ##
    ####################

    def web_post(self):
        debugprint('web_post()')
        post = self.g.box(self.p.post_size, self.p.post_size, self.p.web_thickness)
        post = self.g.translate(post, (0, 0, self.pp.plate_thickness - (self.p.web_thickness / 2)))
        return post

    def web_post_tr(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj

        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0

        return self.g.translate(self.web_post(),
                                ((mount_width / w_divide) - post_adj, (mount_height / 2) - post_adj, 0))

    def web_post_br(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), ((mount_width / w_divide) - post_adj, -(mount_height / 2) + post_adj, 0))

    def web_post_tl(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), (-(mount_width / w_divide) + post_adj, (mount_height / 2) - post_adj, 0))

    def web_post_bl(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), (-(mount_width / w_divide) + post_adj, -(mount_height / 2) + post_adj, 0))

    def adjustable_square_plate(self, Uwidth=1.5, Uheight=1.5):
        width = usize_dimension(Usize=Uwidth)
        height = usize_dimension(Usize=Uheight)
        print("width: {}, height: {}, thickness:{}".format(width, height, self.p.web_thickness))
        shape = self.g.box(width, height, self.p.web_thickness)
        shape = self.g.difference(shape, [self.g.box(self.p.mount_width - .01, self.p.mount_height - .01, 2 * self.p.web_thickness)])
        # shape = self.g.translate(shape, (0, 0, web_thickness / 2))
        shape = self.g.translate(shape, (0, 0, self.pp.plate_thickness - (self.p.web_thickness / 2)))

        return shape

    def adjustable_plate_size(self, Usize=1.5):
        return (Usize * self.pp.sa_length - self.p.mount_height) / 2

    def adjustable_plate_half(self, Usize=1.5):
        debugprint('double_plate()')
        adjustable_plate_height = self.adjustable_plate_size(Usize)
        top_plate = self.g.box(self.p.mount_width, adjustable_plate_height, self.p.web_thickness)
        top_plate = self.g.translate(top_plate,
                                     [0, (adjustable_plate_height + self.p.mount_height) / 2,
                                      self.pp.plate_thickness - (self.p.web_thickness / 2)]
                                     )
        return top_plate

    def adjustable_plate(self, Usize=1.5):
        debugprint('double_plate()')
        top_plate = self.adjustable_plate_half(Usize)
        return self.g.union((top_plate, self.g.mirror(top_plate, 'XZ')))

    def double_plate_half(self):
        debugprint('double_plate()')

        top_plate = self.g.box(self.p.mount_width, self.pp.double_plate_height, self.p.web_thickness)
        top_plate = self.g.translate(top_plate,
                                     [0, (self.pp.double_plate_height + self.p.mount_height) / 2,
                                      self.pp.plate_thickness - (self.p.web_thickness / 2)]
                                     )
        return top_plate

    def double_plate(self):
        debugprint('double_plate()')
        top_plate = self.double_plate_half()
        return self.g.union((top_plate, self.g.mirror(top_plate, 'XZ')))


@dataclass_json
@dataclass
class UndercutPlateParameters(HolePlateParameters):
    package: str = 'shapes.plates'
    class_name: str = 'UndercutPlate'

    keyswitch_height: float = 14.0
    keyswitch_width: float = 14.0

    plate_rim: float = 1.5 + 0.5
    # Undercut style dimensions
    clip_thickness: float = 1.1
    clip_undercut: float = 1.0
    undercut_transition: float = .2  # NOT FUNCTIONAL WITH OPENSCAD, ONLY WORKS WITH CADQUERY


class UndercutPlate(HolePlate):
    parameter_type = UndercutPlateParameters
    g: helpers_abc

    # parent: dm.DactylBase
  
    def plate_shape(self):
        plate = self.plate_square_hole()
        undercut = self.plate_undercut()

        plate = self.g.difference(plate, [undercut])
        return plate
    
    def plate_undercut(self):
        undercut = self.g.box(
            self.pp.keyswitch_width + 2 * self.pp.clip_undercut,
            self.pp.keyswitch_height + 2 * self.pp.clip_undercut,
            self.p.mount_thickness
        )
        if self.p.ENGINE == 'cadquery' and self.pp.undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(self.pp.undercut_transition, self.pp.clip_undercut)

        return undercut




@dataclass_json
@dataclass
class NotchPlateParameters(HolePlateParameters):
    package: str = 'shapes.plates'
    class_name: str = 'NotchPlate'

    keyswitch_height: float = 14.0
    keyswitch_width: float = 14.0

    plate_rim: float = 1.5 + 0.5

    notch_width: float = 6.0  # If using notch, it is identical to undecut, but only locally by the switch clip
    clip_thickness: float = 1.1
    clip_undercut: float = 1.0
    undercut_transition: float = .2  # NOT FUNCTIONAL WITH OPENSCAD, ONLY WORKS WITH CADQUERY

 
class NotchPlate(HolePlate):
    parameter_type = NotchPlateParameters
    g: helpers_abc

    # parent: dm.DactylBase

    def plate_shape(self):
        plate = self.plate_square_hole()
        undercut = self.plate_notch()

        plate = self.g.difference(plate, [undercut])
        return plate
        
    def plate_notch(
            self, keyswitch_width=None, keyswitch_height=None, mount_thickness=None,
            notch_width=None, clip_undercut=None, undercut_transition=None
    ):
        undercut = self.g.box(
            self.pp.notch_width,
            self.pp.keyswitch_height + 2 * self.pp.clip_undercut,
            self.p.mount_thickness
        )
        undercut = self.g.union([
            undercut,
            self.g.box(
                self.pp.keyswitch_width + 2 * self.pp.clip_undercut,
                self.pp.notch_width,
                self.p.mount_thickness
            )
        ])

        undercut = self.g.translate(undercut, (0.0, 0.0, -self.pp.clip_thickness + self.p.mount_thickness / 2.0))

        if self.p.ENGINE == 'cadquery' and self.pp.undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(self.pp.undercut_transition, self.pp.clip_undercut)

        return undercut


@dataclass_json
@dataclass
class NubPlateParameters(HolePlateParameters):
    package: str = 'shapes.plates'
    class_name: str = 'NubPlate'

    keyswitch_height: float = 14.4
    keyswitch_width: float = 14.4
    plate_thickness: float = 4 + 1.1

    plate_rim: float = 1.5 + 0.5

    nub_radius: float = 1.0
    nub_width: float = 2.75
    nub_protrusion: float = 1.0

    # nub_base: float = 1.0

class NubPlate(HolePlate):
    parameter_type = NubPlateParameters
    g: helpers_abc

    # parent: dm.DactylBase

    def plate_shape(self):
        plate = self.nub_plate()
        return plate

    def nub_plate(self):
        tb_border = (self.p.mount_height - self.pp.keyswitch_height) / 2
        top_wall = self.g.box(self.p.mount_width, tb_border, self.pp.plate_thickness)
        top_wall = self.g.translate(top_wall, (0, (tb_border / 2) + (self.pp.keyswitch_height / 2), self.pp.plate_thickness / 2))

        lr_border = (self.p.mount_width - self.pp.keyswitch_width) / 2
        left_wall = self.g.box(lr_border, self.p.mount_height, self.pp.plate_thickness)
        left_wall = self.g.translate(left_wall, ((lr_border / 2) + (self.pp.keyswitch_width / 2), 0, self.pp.plate_thickness / 2))

        # only used to create part of a hull
        self.pp.nub_base = 1.0

        side_nub = self.g.cylinder(radius=self.pp.nub_radius, height=self.pp.nub_width)
        side_nub = self.g.rotate(side_nub, (90, 0, 0))
        side_nub = self.g.translate(
            side_nub, (self.pp.keyswitch_width / 2 - (self.pp.nub_protrusion - self.pp.nub_radius), 0, 1)
        )

        nub_cube = self.g.box(self.pp.nub_base, self.pp.nub_width, self.pp.plate_thickness)
        nub_cube = self.g.translate(nub_cube, ((self.pp.nub_base / 2) + (self.pp.keyswitch_width / 2), 0, self.pp.plate_thickness / 2))

        side_nub2 = self.g.tess_hull(shapes=(side_nub, nub_cube))
        side_nub2 = self.g.union([side_nub2, side_nub, nub_cube])

        plate_half1 = self.g.union([top_wall, left_wall, side_nub2])
        plate_half2 = plate_half1
        plate_half2 = self.g.mirror(plate_half2, 'XZ')
        plate_half2 = self.g.mirror(plate_half2, 'YZ')

        plate = self.g.union([plate_half1, plate_half2])

        return plate




