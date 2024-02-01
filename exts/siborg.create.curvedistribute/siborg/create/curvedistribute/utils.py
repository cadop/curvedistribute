import omni.usd
from typing import List
from pxr import Sdf
from enum import IntEnum

class CURVE(IntEnum):
    Bezier = 0
    Bspline = 1
    Linear = 2

def get_selection() -> List[str]:
    """Get the list of currently selected prims"""
    return omni.usd.get_context().get_selection().get_selected_prim_paths()

def index_to_axis(idx):
    # AXIS = ["+X", "+Y", "+Z", "-X", "-Y", "-Z"]  # taken from motion path
    xp = [1,0,0]
    yp = [0,1,0]
    zp = [0,0,1]
    
    xn = [-1,0,0]
    yn = [0,-1,0]
    zn = [0,0,-1]
    
    axis_vecs = [xp,yp,zp,xn,yn,zn]
    
    return axis_vecs[idx]