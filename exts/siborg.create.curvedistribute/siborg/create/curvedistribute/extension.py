import omni.ext
import omni.ui as ui
from omni.ui import color as cl
from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd
from . import utils

from .core import CurveManager, GeomCreator

AXIS = ["+X", "+Y", "+Z", "-X", "-Y", "-Z"]  # taken from motion path
CURVES = ["Bezier", "BSpline"]

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
            self._use_instance_model = ui.SimpleBoolModel()

            #Defaults
            self._count = 0
            self._source_prim_model.as_string = ""
            self._source_curve_model.as_string = ""
            self._sampling_resolution = 0
            self._use_instance_model = False
            self._use_orient_model = False
            self._forward_axis = [1,0,0]
            self._curve_type = utils.CURVE.Bezier
            #Grab Prim in Stage on Selection
            def _get_prim():
                self._source_prim_model.as_string = ", ".join(utils.get_selection())

            def _get_curve():
                self._source_curve_model.as_string = ", ".join(utils.get_selection())


            self._window = ui.Window("Distribute Along Curve", width=260, height=360)
            with self._window.frame:
                with ui.VStack(height=10, width=240, spacing=10):
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
                    ui.Label("Select Curve From Stage", tooltip="Select a BasisCurves type")
                    with ui.HStack():
                        ui.StringField(height=2, model=self._source_curve_model)
                        ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_curve)

                    ui.Spacer()

                    ui.Label("Get Prims From Stage", width=65, tooltip="Select multiple prims to distribute in sequence")
                    with ui.HStack():
                        ui.StringField(height=2, model=self._source_prim_model)
                        ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_prim)
                    
                    ui.Spacer()


                    with ui.HStack():
                        ui.Label("Copies", tooltip="Number of copies to distribute. Endpoints are included in the count.")
                        x = ui.IntField(height=5)
                        x.model.add_value_changed_fn(lambda m, self=self: setattr(self, '_count', m.get_value_as_int()))
                        x.model.set_value(3) 
                        
                        
                        ui.Label("     Subsamples", tooltip="A sampling parameter, don't touch if you don't understand")
                        x = ui.IntField(height=5) 
                        x.model.add_value_changed_fn(lambda m, self=self: setattr(self, '_sampling_resolution', m.get_value_as_int()))
                        x.model.set_value(1000) 

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
                        
                        ui.Button("Distribute", clicked_fn=lambda: GeomCreator.duplicate(self._count, 
                                                                                         self._sampling_resolution, 
                                                                                         self._source_curve_model, 
                                                                                         self._source_prim_model, 
                                                                                         self._use_instance_model,
                                                                                         self._use_orient_model,
                                                                                         self._forward_axis,
                                                                                         self._curve_type), 
                                        style=distribute_button_style) 

                    with ui.HStack():
                        # ui.StringField(height=2, model=self._source_prim_model)
                        # ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_prim)
                        ui.Label(" Use instances ", width=65, tooltip="Select to use instances when copying a prim")
                        instancer = ui.CheckBox(width=30)
                        instancer.model.add_value_changed_fn(lambda m : setattr(self, '_use_instance_model', m.get_value_as_bool()))
                        instancer.model.set_value(False)
                        
                        ui.Label(" Follow Orientation ", width=65)
                        instancer = ui.CheckBox(width=30)
                        instancer.model.add_value_changed_fn(lambda m : setattr(self, '_use_orient_model', m.get_value_as_bool()))
                        instancer.model.set_value(False)

                    with ui.HStack():
                        ui.Label("Spline Type", 
                                 name="label", 
                                 width=160, 
                                 tooltip="Type of curve to use for interpolating control points")
                        ui.Spacer(width=13)
                        widget = ui.ComboBox(0, *CURVES).model
                        widget.add_item_changed_fn(lambda m, i: setattr(self, '_curve_type',
                                                                        m.get_item_value_model().get_value_as_int()
                                                                        )
                                                   )

                    with ui.HStack():
                        ui.Label("Forward Axis", 
                                 name="label", 
                                 width=160, 
                                 tooltip="Forward axis of target Object")
                        ui.Spacer(width=13)
                        widget = ui.ComboBox(0, *AXIS).model
                        widget.add_item_changed_fn(lambda m, i: setattr(self, '_forward_axis',
                                                                        utils.index_to_axis(m.get_item_value_model().get_value_as_int())
                                                                        )
                                                   )
        
        def on_shutdown(self):
            print("[siborg.create.curvedistribute] siborg create curvedistribute shutdown")

