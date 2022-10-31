# The Dactyl-ManuForm Keyboard - Python 3 - Cadquery
This is a fork of [Dactyl-Manuform](https://github.com/tshort/dactyl-keyboard) by Tom Short, which itself is a fork of [Dactyl](https://github.com/adereth/dactyl-keyboard) by Matthew Adereth, a parameterized, split-hand, concave, columnar, ergonomic keyboard.

While the code structure remains comparable to the original, Clojure and OpenSCAD have been replaced by Python and cadquery/OpenCASCADE.  The predecessors were exceptional contributions to the ergo keyboard community by the authors but used a rather esoteric programming language, Clojure, and a relatively inconsistent geometry engine, OpenSCAD.  My hope is that by converting the code the community will have an easier time modifying and evolving this design.


## Collaborations and Donations
I decided to start accepting donations to help offset some of the prototyping costs and development time.  There are 2 ways to contribute to this project:

### Purchase a kit or keyboard from https://www.ergohaven.xyz/
I am also supported by [ergohaven](https://www.ergohaven.xyz/).  The Dactyl-Manuforms are generated from this repository.  After working with the owner on additions to support new features we decided to collaborate to evolve the designs they can offer and to support my work.

### Donate directly
I opened Liberapay and Ko-fi accounts to accept donations.  It is obviously not necessary, but is appreciated.  If you do donate and have something specific you really want to see, please let me know. I want to be very open that I can't promise to complete all requests as there are many reasons like engine capabilities and generator construction that can make certain features unfeasible, but I will do my best to improve this repo for you and the ergo keyboard community.

[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/joshreve/donate)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/K3K25ZIHR)


## Helpful Feedback
At this point there has been tons of feedback form the community and I greatly appreciate it.  While I can only work on this in my free time, I do my best to respond to anyone who posts a comment or question.  Feedback on issues or just possible new features is always welcome.

## Updated Geometry Engine, generating STEP files
As part of the effort to create a new engine I converted the code to cadquery/OpenCASCADE.  While OpenSCAD has provided an open source 3D engine that is extremely popular, it frankly creates barely passable STLs when you have complex geometry.  After being extremely frustrated trying to fix the mesh I realized it is just not a stable engine to create high quality files.  OpenCASCADE is extremely powerful but requires extensive detail to operate.  cadquery provided an excellent platform to run a stable geometry engine with a simplified API.

![STEP File in FreeCAD](./resources/FreeCAD_STEP_screen.png)

## Added Features

### Python package
This project is now a python package, and installs as one.
See below for instructions

### Refactored

Running `dactyl-keyboard --generate-config <config-file.json>` generates a settings file with the default configuration, which can be modified and then used to control the build with `dactyl-keyboard --config <config-file.json>`.
This file can of course be shared with others

Additionally, the OpenSCAD/solid python and OpenCASCADE/cadquery versions are merged with separate helper functions
to decouple the generator from the target library.  This also lets me stay sane by only modifying one file for most updates.

### Everyone gets a thumb cluster!

Added support of for the thumb clusters in the [carbonfet Dactyl library](https://github.com/carbonfet/dactyl-manuform).
These are the "mini" and "carbonfet" thumb clusters. Additional trackball cluster added as well more info to be added after additional build and debug time.

Feel free to try them out with by setting `'thumb_style'` to
`'DEFAULT'`, `'MINI'`, `'CARBONFET'`, `'MINIDOX'`, `'TRACKBALL_ORBYL'`, and `'TRACKBALL_CJ'`.

Trackball features accommodate a [Perixx PERIPRO-303](https://smile.amazon.com/gp/product/B08DD6GQRV/).  Others may fit, but this was the target ball diameter for the design.  It is a little smaller than a Ploopy to try to fit better in the cluster.

Rendered and actual images to be added in future commits.

### Clippable switch mounting

Tired of hot glue and constraining the socket with "nubs"?  I've added an adjustable undercut for using the clips on
the sockets.  May require some tweaking and little filing, but I have my DM built without any glue and you can too.
Just use `plate_style = 'UNDERCUT'`.  I've also added an improved local undercut using `plate_style = 'NOTCH'`.

### Kailh Hotswap
Added a new switch for hot swap and a way to include any additional geometry in the key plate by use of an imported file.
For hot swap just use `plate_style = 'HS_NOTCH'`, `plate_style = 'HS_HOLE'`, or `plate_style = 'HS_NUB'`.
To import an arbitrary geometry set the `plate_file = None` and `plate_offset = 0.0`.
The file must be .step for OpenCascade / cadquery and .stl for openSCAD / solid python.
The zero reference should be the key center (XY), and the top of the plate (Z).
Plate offset is a Z-axis translation for minor adjustments without modifying the geometry file.

**DISCLAIMER:  I have not built the hot swap version and cannot speak to the geometry.  I found it running around in various places and don't know the origin.  At least one user has claimed it works.**

If you know the origin I would like to credit the originator.  If you test it I'd love to know how well it works or if you come up with a better geometry I'm happy to add it.

Message me on Reddit u/j_oshreve if you are really stuck.  I don't have much time to help, but can answer the occasional question.  Also feel free to put in a pull request if you come up with something crafty and want to give others access to it.

![Hot Swap in OpenSCAD](./resources/OpenSCAD_hotswap.png)

### Multiple Controller Mounts

Added an external mount for a separate controller tray.  Looks to work with lolligag's controller trays / holders:

- [Promicro V1](https://dactyl.siskam.link/loligagger-external-holder-promicro-v1.stl)
- [Promicro V2](https://dactyl.siskam.link/loligagger-external-holder-promicro-v2.stl)
- [Elite-C V1 ](https://dactyl.siskam.link/loligagger-external-holder-elite-c-v1.stl)

Just use `controller_mount_type = 'EXTERNAL'`.

![Controller tray opening](./resources/external_controller_tray_opening.png)
![Tray 1](./resources/promicro_tray_1.png)
![Tray 2](./resources/promicro_tray_2.png)

This is a new feature so any feedback is appreciated.  If you have issues, message me on Reddit and I will try to help correct them.

### OLED Display Mount

Added 3 OLED mounts.  Have printed them stand alone with success.  I suggest clip, but it may require some tweaks based on your printer (over vs under sized).

![OLED Clip Mounting](./resources/clip_OLED_mounting.png)
![OLED Clip Plate](./resources/OLED_clip_plate.png)

`oled_mount_type = 'CLIP'` creates an opening to set the OLED with a clip on face plate to hold it down.  This is the preferred mounting, but needs the OLED to have a removable connection.

`oled_mount_type = 'SLIDING'` creates an opening such that you can slide the screen up through the back and into place.  Needs a piece of foam or a bit of glue to lock in place.

`oled_mount_type = 'UNDERCUT'` creates an opening with an undercut to create whatever custom holder you want.  Will not work without additional part creation from the user.

This is a new feature so any feedback is appreciated.  If you have issues, message me on Reddit and I will try to help correct them.

### Screw Post Locations

You can now have slightly better control of screw mounts.  Set to `'screws_offset':'INSIDE'`, `'screws_offset':'OUTSIDE'` or `'screws_offset': 'ORIGINAL'` to control screw locations relative to the wall.
![Inside Screws](./resources/inside_screw_posts.png)

I am planning to deprecate outside and original at some point.  I don't see the need to carry all of them and the hidden look the best.  If you disagree feel free to let me know and I may keep a second form.

## Status / Future
This is now a bit of a monster of many minds and yet continues to bear fruit.
I plan to continue to use this code to try new geometries and features to share for the foreseeable future.

## Installation

This project is now a python package, and installs as one:
```
pip install "dactyl-keyboard @ git+https://github.com/joshreve/dactyl-keyboard"
```
(see the official [pip support for version control systems](https://pip.pypa.io/en/stable/topics/vcs-support/) for more options)

The engines required to create output files are optional dependencies:
 - cadquery: `"pip install "dactyl-keyboard[cadquery] @ git+https://github.com/joshreve/dactyl-keyboard"`
 - solid/openSCAD: `"pip install "dactyl-keyboard[solid] @ git+https://github.com/joshreve/dactyl-keyboard"`

 Specifying multiple options requires separating them with a comma: `pip install "dactyl-keyboard[cadquery, solid] @ ..."`

To install you will need either [python](https://www.python.org/downloads/)+[pip](https://pip.pypa.io/en/stable/installation/) or a [conda environment](https://docs.anaconda.com/anaconda/install/index.html)

For python+pip it is recommended you follow standard practice and use a [virtual environment](https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-and-using-virtual-environments).

For conda, besides installing with pip you can also add the required entries to an `environment.yml` file, as so:
```yaml
name: ...
channels:
dependencies:
  - python>=3.8
  - pip:
    - "dactyl-keyboard @ git+https://github.com/joshreve/dactyl-keyboard"
```

## Generating the design

**Generating the design - UPDATED**
* If desired, run `dactyl-keyboard --generate-config <config-file>` and directly edit the file to configure the design.
* Run `dactyl-keyboard` (or `dactyl-keyboard --config <config-file>`) to create the geometry (ENGINE variable in run determines method)
* This will regenerate a `things/` directory with files (or in subdirectory if defined in config)
    * `*left.*`
    * `*right.*`
    * `*plate.*`
    * `*oled_clip.*` (if applicable)
    * `*oled_clip_test.*` (if applicable)
* Use [OpenSCAD](https://openscad.org/) to open a `.scad` file
* Use [FreeCAD](https://www.freecad.org/) or other application to open a `.step` file
* Make changes to design, repeat run step
* When done, use OpenSCAD or FreeCAD to export STL files

**The majority of the the rest of the below content is as defined by previous authors, except where noted.**

## Origin
![Imgur](http://i.imgur.com/LdjEhrR.jpg)

The main change is that the thumb cluster was adapted from the [ManuForm keyboard](https://github.com/jeffgran/ManuForm) ([geekhack](https://geekhack.org/index.php?topic=46015.0)). The walls were changed to just drop to the floor. The keyboard is paramaterized to allow adjusting the following:

* Rows: 4 - 6
* Columns: 5 and up
* Row curvature
* Column curvature
* Row tilt (tenting)
* Column tilt
* Column offsets
* Height

## Assembly

### Printing
Pre-generated files can be opened in OpenSCAD or FreeCAD and exported to STL.  Bottom plate is available as a step file or dxf for cadquery or a .scad file to be exported from OpenSCAD.

### Wiring

Here are materials tshort used for wiring.

* Two Arduino Pro Micros
* [Heat-set inserts](https://www.mcmaster.com/#94180a331/=16yfrx1)
* [M3 wafer-head screws, 5mm](http://www.metricscrews.us/index.php?main_page=product_info&cPath=155_185&products_id=455)
* [Copper tape](https://www.amazon.com/gp/product/B009KB86BU)
* [#32 magnet wire](https://www.amazon.com/gp/product/B00LV909HI)
* [#30 wire](https://www.amazon.com/gp/product/B00GWFECWO)
* [3-mm cast acrylic](http://www.mcmaster.com/#acrylic/=144mfom)
* [Veroboard stripboard](https://www.amazon.com/gp/product/B008CPVMMU)
* [1N4148 diodes](https://www.amazon.com/gp/product/B00LQPY0Y0)
* [Female RJ-9 connectors](https://www.amazon.com/gp/product/B01HU7BVDU/)

I wired one half using the traditional approach of using the legs of a diode to form the row connections.
(I'm not great at soldering, so this was challenging for me.)
For this side, I used magnet wire to wire columns. That worked okay.
The magnet wire is small enough, it wants to move around, and it's hard to tell if you have a good connection.

![Imgur](http://i.imgur.com/7kPvSgg.jpg)

For another half, I used stripboard for the row connections.
This allowed me to presolder all of the diodes.
Then, I hot-glued this in place and finished the soldering of the other diode ends.
I like this approach quite a lot.
Connections for the diodes were much easier with one end fixed down.
On this half, I also used copper tape to connect columns.
This worked a bit better than the magnet wire for me.
For a future version, I may try just bare tinned copper wire for columns (something like #20).
With the stripboard, it's pretty easy keeping row and column connections separate.

![Imgur](http://i.imgur.com/JOm5ElP.jpg)

Note that a telephone handset cable has leads that are reversed, so take this into account when connecting these leads to the controller.

The 3D printed part is the main keyboard.
You can attach a bottom plate with screws.
The case has holes for heat-set inserts designed to hold 3- to 6-mm long M3 screws.
Then, I used wafer-head screws to connect a bottom plate.
If wires aren't dangling, a bottom plate may not be needed.
You need something on the bottom to keep the keyboard from sliding around.
Without a plate, you could use a rubber pad, or you could dip the bottom of the keyboard in PlastiDip.

For more photos of the first complete wiring of v0.4, see [Imgur](http://imgur.com/a/v9eIO).

This is how the rows/columns wire to the keys and the ProMicro
![Wire Diagram](https://docs.google.com/drawings/d/1s9aAg5bXBrhtb6Xw-sGOQQEndRNOqpBRyUyHkgpnSps/pub?w=1176&h=621)


#### Alternative row-driven wiring diagram for ProMicro:

NOTE: you also make sure the firmware is set up correctly (ex: change row pins with col pins)

![Left Wire Diagram](./resources/dactyl_manuform_left_wire_diagram.png)

![Right Wire Diagram](./resources/dactyl_manuform_right_wire_diagram.png)


### Firmware

Firmware goes hand in hand with how you wire the circuit.
I adapted the QMK firmware [here](https://github.com/tshort/qmk_firmware/tree/master/keyboards/dactyl-manuform).
This allows each side to work separately or together.
This site also shows connections for the Arduino Pro Micro controllers.

## License

General Code Copyright © 2015-2021 Matthew Adereth, Tom Short, and Joshua Shreve
Mini thumb cluster Copyright © 2015-2018 Matthew Adereth, Tom Short, and Leo Lou
Carbonfet thumb cluster © 2015-2018 Matthew Adereth, Tom Short, and carbonfet (github username)

The source code for generating the models (everything excluding the [things/](things/) and [resources/](resources/) directories is distributed under the [GNU AFFERO GENERAL PUBLIC LICENSE Version 3](LICENSE).  The generated models and PCB designs are distributed under the [Creative Commons Attribution-NonCommercial-ShareAlike License Version 3.0](LICENSE-models).
