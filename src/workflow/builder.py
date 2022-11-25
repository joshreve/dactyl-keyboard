# from dactyl_manuform import *
from clusters.default import DefaultCluster
import os.path as path
import getopt, sys
import json
import os
import shutil


debug_exports = False
debug_trace = False


def debugprint(info):
    if debug_trace:
        print(info)


class Builder:
    column_style = "asymetric"
    centerrow = 3
    lastrow = 4
    cornerrow = 3
    lastcol = 5


    def __init__(self, parent_locals):
        for item in parent_locals:
            globals()[item] = parent_locals[item]
        cluster = DefaultCluster(parent_locals)
        origin = cluster.thumborigin()
        print("Locals imported")
        print(thumb_style)


print("It built!")
