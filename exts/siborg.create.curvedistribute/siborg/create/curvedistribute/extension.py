import omni.ext
import omni.ui as ui
from omni.ui import color as cl
from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd
from .utils import get_selection


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
        def __init__(self,  delegate=None, **kwargs):
            super().__init__(**kwargs)

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
        def on_startup(self, ext_id):
            print("[siborg.create.curvedistribute] siborg create curvedistribute startup")


            #Models
            self._source_prim_model = ui.SimpleStringModel()
            self._source_curve_model = ui.SimpleStringModel()

            #Defaults
            self._source_prim_model.as_string = ""
            self._source_curve_model.as_string = ""

            #Grab Prim in Stage on Selection
            def _get_prim():
                self._source_prim_model.as_string = ", ".join(get_selection())

            def _get_curve():
                self._source_curve_model.as_string = ", ".join(get_selection())

            self._window = ui.Window("Distribute along curve", width=210, height=300)
            with self._window.frame:
                with ui.VStack(height=10, width=200, spacing=10):
                    select_button_style ={"Button":{"background_color": cl.cyan,
                                                "border_color": cl.white,
                                                "border_width": 2.0,
                                                "padding": 4,
                                                "margin_height": 1,
                                                "border_radius": 10,
                                                "margin_width":2},
                                                "Button.Label":{"color": cl.black},
                                                "Button:hovered":{"background_color": cl("#E5F1FB")}}
                    ui.Spacer()
                    ui.Label("Select Curve From Stage")
                    with ui.HStack():
                        ui.StringField(height=2, model=self._source_curve_model)
                        ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_curve)

                    ui.Spacer()

                    label = ui.Label("Get Prim From Stage", width=65)
                    with ui.HStack():
                        ui.StringField(height=2, model=self._source_prim_model)
                        ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_prim)
                    
                    ui.Spacer()

                    def duplicate():
                        stage = omni.usd.get_context().get_stage()
                        curve_path = self._source_curve_model.as_string
                        ref_prim = self._source_prim_model.as_string
                        path_to = f'{ref_prim}Copy'
                        num_points = self._count

                        interpolated_points = interpcurve(stage, curve_path, num_points)
                        copy_to_points(stage, interpolated_points, ref_prim, path_to)

                    ui.Label("Set Number of Points")
                    with ui.VStack():
                        distribute_button_style = {"Button":{"background_color": cl.cyan,
                            "border_color": cl.white,
                            "border_width": 2.0,
                            "padding": 10,
                            "margin_height": 10,
                            "border_radius": 10,
                            "margin_width":5},
                            "Button.Label":{"color": cl.black},
                            "Button:hovered":{"background_color": cl("#E5F1FB")}}
                        x = ui.IntField(height=5) 
                        x.model.add_value_changed_fn(lambda m, self=self: setattr(self, '_count', m.get_value_as_int()))
                        ui.Button("Distribute", clicked_fn=duplicate, style=distribute_button_style)

        def on_shutdown(self):
            print("[siborg.create.curvedistribute] siborg create curvedistribute shutdown")
