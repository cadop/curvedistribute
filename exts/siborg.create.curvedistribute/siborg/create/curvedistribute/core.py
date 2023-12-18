from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd


class CurveManager():
    def __init__(self):
        pass

    @classmethod
    def interpcurve(cls, stage, curve_path, num_points):
        '''Interpolates a bezier curve based on the input points on the usd'''

        # Get the curve prim and points that define it
        curveprim = stage.GetPrimAtPath(curve_path)
        points = curveprim.GetAttribute('points').Get()
        points = np.array(points)

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

    @classmethod
    def copy_to_points(cls, stage, target_points, ref_prims, path_to, make_instance=False,
                        rand_order=False, use_orient=False, follow_curve=False):
        '''
        
        path_to: str, prefix to the prim path. automatically appends Copy
        TODO: rand_order =True, use randomness to determine which prim to place
        TODO: use_orient=True, rotate object to face direction 
        TODO: follow_curve=True, set rotation axis to match curve (different than orientation when curve is 3d)
        '''
        
        # Define a path for the new scope prim
        scope_name = 'Copies'
        scope_path = f"/World/{scope_name}"
        # Create the scope prim at the specified path
        scope_prim = UsdGeom.Scope.Define(stage, scope_path)
        
        # Get index of prims that are not None and keep track 
        prim_set = [p for p in ref_prims if p != None]
        print(prim_set) 
        print(f'isntance? : {make_instance}')
        
        new_prims = []
        
        if make_instance:

            # Mark the original prims as instanceable if it has no children (like for a mesh)
            for prim_path in prim_set:

                original_prim = stage.GetPrimAtPath(prim_path)
                
                # If this prim is not wrapped in an xform
                if not original_prim.GetChildren():
                    ref_prim = original_prim
                    
                    ref_prim_suffix = str(ref_prim.GetPath()).split('/')[-1]
                    
                    # Create a new xform inside the scope
                    primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_Source"
                    new_prim_xform_wrapper = stage.DefinePrim(primpath_to, "Xform")
                    
                    # Make this new xform instanceable
                    new_prim_xform_wrapper.SetInstanceable(True)
                    
                    print(f'xform wrap path {new_prim_xform_wrapper}')
                    new_ref_prim = f"{new_prim_xform_wrapper.GetPath()}/{ref_prim_suffix}"
                    
                    # Duplicate the prim and put it under a new xform
                    omni.usd.duplicate_prim(stage, ref_prim.GetPath(), new_ref_prim)
                    xform = UsdGeom.Xformable(new_prim_xform_wrapper)
                    # Get the list of xformOps
                    xform_ops = xform.GetOrderedXformOps()
                    # Check if translate op exists
                    has_translate_op = any(op.GetOpType() == UsdGeom.XformOp.TypeTranslate for op in xform_ops)
                    if not has_translate_op:
                        xform.AddTranslateOp()
                    ref_prim= str(new_prim_xform_wrapper.GetPath())

                    original_prim = stage.GetPrimAtPath(ref_prim)
                    print("finished the xform wrapper")
                
                original_prim.SetInstanceable(True)
                
                new_prims.append(original_prim)

            prim_set = new_prims

        num_prims = len(prim_set)
        cur_idx = 0

        for i, target_point in enumerate(target_points):
            ref_prim = prim_set[cur_idx]

            if make_instance:
                prim_type =  ref_prim.GetTypeName()
                ref_prim_suffix = str(ref_prim.GetPath()).split('/')[-1]
                primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_{i}"       

                # Create a new prim and add a reference to the original prim
                instance_prim = stage.DefinePrim(primpath_to, prim_type)
                references = instance_prim.GetReferences()
                references.AddInternalReference(ref_prim.GetPath())

                target_pos = Gf.Vec3d(tuple(target_point))
                instance_prim.GetAttribute('xformOp:translate').Set(target_pos)
            else:
                ref_prim_suffix = str(ref_prim).split('/')[-1]
                primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_{i}"
                omni.usd.duplicate_prim(stage, ref_prim, primpath_to)        
                new_prim = stage.GetPrimAtPath(primpath_to)
                target_pos = Gf.Vec3d(tuple(target_point))
                new_prim.GetAttribute('xformOp:translate').Set(target_pos)

            if cur_idx < num_prims-1: cur_idx +=1
            else: cur_idx = 0


        # # Make a copy of the prims (won't matter if its a mesh or not)
        # else: 
        #     ###################################
        #     num_prims = len(prim_set)
        #     cur_idx = 0

        #     for i, target_point in enumerate(target_points):
        #         ref_prim = prim_set[cur_idx]
        #         ref_prim_suffix = str(ref_prim).split('/')[-1]
        #         primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_{i}"
        #         primpath_to = f"{ref_prim}Copy_{i}"
                
        #         omni.usd.duplicate_prim(stage, ref_prim, primpath_to)
        #         new_prim = stage.GetPrimAtPath(primpath_to)
        #         target_pos = Gf.Vec3d(tuple(target_point))
        #         new_prim.GetAttribute('xformOp:translate').Set(target_pos)

        #         # Go to the next prim, or reset to 0
        #         if cur_idx < num_prims-1: cur_idx +=1
        #         else: cur_idx = 0
        #     ###################################

class GeomCreator():
    def __init__(self):
        pass
    
    @classmethod
    def duplicate(cls, _count, _source_curve_model, _source_prim_model, _use_instance):
        '''
        ## All of these should work (assuming the named prim is there)
        # ref_prims = ['/World/Cube']
        # ref_prims = ['/World/Cube', None]
        # ref_prims = ['/World/Cube', '/World/Cone']
        '''

        stage = omni.usd.get_context().get_stage()
        curve_path = _source_curve_model.as_string
        ref_prims = [_source_prim_model.as_string]
        # _use_instance = _use_instance.as_bool


        path_to = f'/Copy'

        num_points = _count
        # Default to 3x the number of points to distribute? Actually might be handled already by interp
        num_samples = _count

        # TODO: make this setting for the resolution to sample the curve defined by user
        interpolated_points = CurveManager.interpcurve(stage, curve_path, num_samples)
        indices = np.linspace(0, len(interpolated_points) - 1, num_points, dtype=int)
        target_points = interpolated_points[indices]
        CurveManager.copy_to_points(stage, target_points, ref_prims, path_to, make_instance=_use_instance)
