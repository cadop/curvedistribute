import omni.ext
import omni.ui as ui
from omni.ui import color as cl
from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd
from . import utils

from .core import CurveManager, GeomCreator

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
            self._source_prim_model.as_string = ""
            self._source_curve_model.as_string = ""
            self._use_instance_model = False

            #Grab Prim in Stage on Selection
            def _get_prim():
                self._source_prim_model.as_string = ", ".join(utils.get_selection())

            def _get_curve():
                self._source_curve_model.as_string = ", ".join(utils.get_selection())

            self._window = ui.Window("Distribute along curve", width=210, height=320)
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
                        ui.Button("Distribute", clicked_fn=lambda: GeomCreator.duplicate(self._count,  
                                                                             self._source_curve_model, 
                                                                             self._source_prim_model, 
                                                                             self._use_instance_model), 
                                  style=distribute_button_style) 

                    with ui.HStack():
                        # ui.StringField(height=2, model=self._source_prim_model)
                        # ui.Button("S", width=20, height=20, style=select_button_style, clicked_fn=_get_prim)
                        ui.Label(" Use instances", width=65)
                                 
                        instancer = ui.CheckBox(width=30)
                        instancer.model.add_value_changed_fn(lambda m : setattr(self, '_use_instance_model', m.get_value_as_bool()))
                        instancer.model.set_value(False)

        def on_shutdown(self):
            print("[siborg.create.curvedistribute] siborg create curvedistribute shutdown")
