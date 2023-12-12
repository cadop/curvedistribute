import omni.usd
from typing import List
from pxr import Sdf


def get_selection() -> List[str]:
    """Get the list of currently selected prims"""
    return omni.usd.get_context().get_selection().get_selected_prim_paths()