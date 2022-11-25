import numpy as np
import sys
import getopt
import os
import json
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Any, Sequence

from oled.oled_clip import OLEDClipParameters as OLEDClip
from oled.oled_sliding import OLEDSlidingParameters as OLEDSliding
from oled.oled_undercut import OLEDUndercutParameters as OLEDUndercut


OLED_LOOKUP = {
    'CLIP': OLEDClip,
    'SLIDING': OLEDSliding,
    'UNDERCUT': OLEDUndercut,
}


@dataclass_json
@dataclass
class ShapeConfiguration:
    ENGINE = 'solid'  # 'solid' = solid python / OpenSCAD, 'cadquery' = cadquery / OpenCascade
    # ENGINE = 'cadquery'  # 'solid' = solid python / OpenSCAD, 'cadquery' = cadquery / OpenCascade

    ######################
    ## Shape parameters ##
    ######################

    save_dir: str = '.'
    config_name: str = "DM"

    show_caps: bool = False
    show_pcbs: bool = False  # only runs if caps are shown, easist place to initially inject geometry

    nrows = 5  # 5,  # key rows
    ncols = 6  # 6,  # key columns

    alpha: float = np.pi / 12.0  # curvature of the columns
    beta: float = np.pi / 36.0  # curvature of the rows
    centercol: int = 3  # controls left_right tilt / tenting (higher number is more tenting)
    centerrow_offset: int = 3  # rows from max, controls front_back tilt
    tenting_angle: float = np.pi / 12.0  # or, change this for more precise tenting control

    # symmetry states if it is a symmetric or asymmetric bui.  If asymmetric it doubles the generation time.
    symmetric: bool = True # "asymmetric" or "symmetric"

    column_style: str = "standard"  # options include :standard, :orthographic, and :fixed
    column_style_gt5: str = "orthographic"

    reduced_outer_keys: bool = True

    keyboard_z_offset: float = (11)  # controls overall height# original=9 with centercol=3# use 16 for centercol=2

    extra_width: float = 2.5  # extra space between the base of keys# original= 2
    extra_height: float = 1.0  # original= 0.5

    web_thickness: float = 4.0 + 1.1
    post_size: float = 0.1
    # post_adj =  post_size / 2
    post_adj: float = 0


    oled_config: Any = None   #OLED_LOOKUP[oled_mount_type]()
    controller_mount_config: Any = None
    plate_config: Any = None
    module_configs: Sequence[Any] = ()

    ###################################
    ## Bottom Plate Dimensions
    ###################################
    # COMMON DIMENSION
    screw_hole_diameter: float = 3
    # USED FOR CADQUERY ONLY
    base_thickness: float = 3.0  # thickness in the middle of the plate
    base_offset: float = 3.0  # Both start flat/flush on the bottom.  This offsets the base up (if positive)
    base_rim_thickness: float = 5.0  # thickness on the outer frame with screws
    screw_cbore_diameter: float = 6.0
    screw_cbore_depth: float = 2.5

    # Offset is from the top inner corner of the top inner key.

    ###################################
    ## COLUMN OFFSETS
    ####################################

    column_offsets: Sequence[Sequence[float]] = (
        (0, 0, 0),
        (0, 0, 0),
        (0, 2.82, -4.5),
        (0, 0, 0),
        (0, -6, 5),  # REDUCED STAGGER
        (0, -6, 5),  # REDUCED STAGGER
        (0, -6, 5),  # NOT USED IN MOST FORMATS (7th column)
    )

    ##############################
    # THUMB PARAMETERS
    ##############################

    # 'DEFAULT' 6-key, 'MINI' 5-key, 'CARBONFET' 6-key, 'MINIDOX' 3-key, 'TRACKBALL_ORBYL', 'TRACKBALL_CJ'
    # thumb_style = 'DEFAULT'
    left_cluster: Any = None
    right_cluster: Any = None
    separable_thumb: bool = False  # creates a separable thumb section with additional screws to hold it down.  Only attached at base.

    ##############################
    # WALL PARAMETERS
    ##############################

    wall_z_offset: float = 15  # length of the first downward_sloping part of the wall
    wall_x_offset: float = 5  # offset in the x and/or y direction for the first downward_sloping part of the wall (negative)
    wall_y_offset: float = 6  # offset in the x and/or y direction for the first downward_sloping part of the wall (negative)
    back_wall_y_offset: float = 6  # specific values for the left side due to the minimal wall.
    back_wall_z_offset: float = 15  # specific values for the left side due to the minimal wall.

    left_wall_ext_x_offset: float = 12  # specific values for the left side due to the minimal wall.
    left_wall_ext_z_offset: float = 3  # specific values for the left side due to the minimal wall.
    left_wall_ext_lower_x_offset: float = 0  # specific values for the lower left corner.
    left_wall_ext_lower_y_offset: float = 0  # specific values for the lower left corner.
    left_wall_ext_lower_z_offset: float = 0

    wall_thickness: float = 4.5  # wall thickness parameter used on upper/mid stage of the wall
    wall_base_y_thickness: float = 4.5  # wall thickness at the lower stage
    wall_base_x_thickness: float = 4.5  # wall thickness at the lower stage

    wall_base_back_thickness: float = 4.5  # wall thickness at the lower stage in the specifically in back for interface.

    ## Settings for column_style == :fixed
    ## The defaults roughly match Maltron settings
    ##   http://patentimages.storage.googleapis.com/EP0219944A2/imgf0002.png
    ## fixed_z overrides the z portion of the column ofsets above.
    ## NOTE: THIS DOESN'T WORK QUITE LIKE I'D HOPED.
    fixed_angles: Sequence[float] = tuple(np.deg2rad((10, 10, 0, 0, 0, -15, -15)))
    fixed_x: Sequence[float] = (-41.5, -22.5, 0, 20.3, 41.4, 65.5, 89.6)  # relative to the middle finger
    fixed_z: Sequence[float] = (12.1, 8.3, 0, 5, 10.7, 14.5, 17.5)
    fixed_tenting: float = np.deg2rad(0)

    ###################################
    ## SCREWS SETUP                  ##
    ###################################

    screws_offset: str = 'INSIDE'  # 'OUTSIDE', 'INSIDE', 'ORIGINAL'
    screw_insert_height: float = 3.8

    # 'screw_insert_bottom_radius = 5.31 / 2  #Designed for inserts
    # 'screw_insert_top_radius = 5.1 / 2  #Designed for inserts

    screw_insert_bottom_radius: float = 2.5 / 2  # Designed for self tapping
    screw_insert_top_radius: float = 2.5 / 2  # Designed for self tapping

    screw_insert_outer_radius: float = 4.25  # Common to keep interface to base

    # Does anyone even use these?  I think they just get in the way.
    wire_post_height: float = 7
    wire_post_overhang: float = 3.5
    wire_post_diameter: float = 2.6


    ##############################
    # EXPERIMENTAL PARAMETERS
    ##############################
    pinky_1_5U: bool = False  # LEAVE AS FALSE, CURRENTLY BROKEN
    first_1_5U_row = 0
    last_1_5U_row = 5

    skeletal: bool = False
    ##############################



    ####################################
    ## END CONFIGURATION SECTION
    ####################################
    def __post_init__(self):
        if self.left_cluster is None:
            import clusters.default as clust
            self.left_cluster = clust.DefaultClusterParameters()

        if self.right_cluster is None:
            import clusters.default as clust
            self.right_cluster = clust.DefaultClusterParameters()

        if self.oled_config is None:
            from oled import oled_clip
            self.oled_config = oled_clip.OLEDClipParameters()

        if self.controller_mount_config is None:
            from shapes import controllers
            self.controller_mount_config = controllers.ExternalControllerParameters()

        if self.plate_config is None:
            from shapes import plates
            self.plate_config = plates.NotchPlateParameters(plate_holes=True, plate_pcb_clear=True)


if __name__ == '__main__':
    from dactyl_manuform import *

    import clusters.default as clust_def
    left_cluster = clust_def.DefaultClusterParameters()
    right_cluster = clust_def.DefaultClusterParameters()

    # import clusters.mini as clust_min
    # right_cluster = clust_min.MiniClusterParameters()

    # import clusters.carbonfet as clust_cf
    # right_cluster = clust_cf.CarbonfetClusterParameters()
    #
    # import clusters.minidox as clust_md
    # right_cluster = clust_md.MinidoxClusterParameters()

    # import clusters.trackball_cj as clust_tbcj
    # right_cluster = clust_tbcj.TrackballCJClusterParameters()

    # import clusters.trackball_orbyl as clust_orb
    # right_cluster = clust_orb.OrbylClusterParameters()

    # import clusters.trackball_wilder as clust_wd
    # right_cluster = clust_wd.WilderClusterParameters()

    # left_cluster = copy.deepcopy(right_cluster)


    from oled import oled_clip
    oled = oled_clip.OLEDClipParameters()

    from shapes import controllers
    ctrl = controllers.ExternalControllerParameters()
    # ctrl = controllers.OriginalControllerParameters()
    # ctrl = controllers.PCBMountControllerParameters()

    config = ShapeConfiguration(
        back_wall_y_offset=10,  # specific values for the left side due to the minimal wall.
        back_wall_z_offset=3,  # specific values for the left side due to the minimal wall.
        right_cluster=right_cluster,
        left_cluster=left_cluster,
        oled_config=oled,
        controller_mount_config=ctrl,
    )

    db = DactylBase(config)
    db.run()

    with open('test.json', mode='w') as fid:
        fid.write(config.to_json(indent=4))

    ## HERE FOR QUICK TESTING, SHOULD BE COMMENTED ON COMMIT
    # from dactyl_manuform import *
    # run()
