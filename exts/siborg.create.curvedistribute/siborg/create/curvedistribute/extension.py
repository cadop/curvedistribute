import omni.ext
import omni.ui as ui

from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd


def interpcurve(stage, curve_path, num_points):

    # Get the curve prim and points that define it
    curveprim = stage.GetPrimAtPath(curve_path)
    points = curveprim.GetAttribute('points').Get()
    points = np.array(points)
    # print(f'Points: {points}')

    # Create a BSpline object
    k = 3 # degree of the spline
    t = np.linspace(0, 1, len(points) - k + 1, endpoint=True)
    t = np.append(np.zeros(k), t)
    t = np.append(t, np.ones(k))
    spl = BSpline(t, points, k)

    # Interpolate points
    tnew = np.linspace(0, 1, num_points)
    interpolated_points = spl(tnew)

    return interpolated_points

def copy_to_points(stage, interpolated_points, ref_prim, path_to):

    for i in range(len(interpolated_points)):
        primpath_to = f"{path_to}_{i}"
        omni.usd.duplicate_prim(stage, ref_prim, primpath_to)
        new_prim = stage.GetPrimAtPath(primpath_to)
        target_pos = Gf.Vec3d(tuple(interpolated_points[i]))
        new_prim.GetAttribute('xformOp:translate').Set(target_pos)




# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class SiborgCreateCurvedistributeExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[siborg.create.curvedistribute] siborg create curvedistribute startup")

        self._count = 0

        self._window = ui.Window("Distribute along curve", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                def duplicate():
                    stage = omni.usd.get_context().get_stage()
                    curve_path = '/World/BasisCurves'
                    ref_prim = '/World/Cube'
                    path_to = f'{ref_prim}Copy'
                    num_points = self._count

                    interpolated_points = interpcurve(stage, curve_path, num_points)
                    copy_to_points(stage, interpolated_points, ref_prim, path_to)

                with ui.VStack():
                    x = ui.IntField(height=5) 
                    x.model.add_value_changed_fn(lambda m, self=self: setattr(self, '_count', m.get_value_as_int()))
                    ui.Button("Distribute", clicked_fn=duplicate)

    def on_shutdown(self):
        print("[siborg.create.curvedistribute] siborg create curvedistribute shutdown")
