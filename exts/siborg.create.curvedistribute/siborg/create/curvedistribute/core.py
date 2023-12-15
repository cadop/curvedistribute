from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd


class CurveManager():
    def __init__(self):
        pass

    @classmethod
    def interpcurve(cls, stage, curve_path, num_points):

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

    @classmethod
    def copy_to_points(cls, stage, target_points, ref_prims, path_to, 
                        rand_order=False, use_orient=False, follow_curve=False):
        '''
        
        path_to: str, prefix to the prim path. automatically appends Copy
        TODO: rand_order =True, use randomness to determine which prim to place
        TODO: use_orient=True, rotate object to fact direction 
        TODO: follow_curve=True, set rotation axis to match curve (different than orientation when curve is 3d)
        '''

        # Get index of prims that are not None and keep track 
        prim_set = [p for p in ref_prims if p != None]
        print(prim_set) 
        num_prims = len(prim_set)
        cur_idx = 0

        for i in range(len(target_points)):
            ref_prim = prim_set[cur_idx]
            primpath_to = f"{ref_prim}Copy_{i}"
            
            omni.usd.duplicate_prim(stage, ref_prim, primpath_to)
            new_prim = stage.GetPrimAtPath(primpath_to)
            target_pos = Gf.Vec3d(tuple(target_points[i]))
            new_prim.GetAttribute('xformOp:translate').Set(target_pos)

            # Go to the next prim, or reset to 0
            if cur_idx < num_prims-1: cur_idx +=1
            else: cur_idx = 0

class GeomCreator():
    def __init__(self):
        pass
    
    @classmethod
    def duplicate(cls, _count, _source_curve_model, _source_prim_model):

        stage = omni.usd.get_context().get_stage()
        curve_path = _source_curve_model.as_string
        ref_prims = [_source_prim_model.as_string]

        ## All of these should work (assuming the named prim is there)
        # ref_prims = ['/World/Cube']
        # ref_prims = ['/World/Cube', None]
        # ref_prims = ['/World/Cube', '/World/Cone']

        path_to = f'/Copy'

        num_points = _count
        # Default to 3x the number of points to distribute? Actually might be handled already by interp
        num_samples = _count

        # TODO: make this setting for the resolution to sample the curve defined by user
        interpolated_points = CurveManager.interpcurve(stage, curve_path, num_samples)
        indices = np.linspace(0, len(interpolated_points) - 1, num_points, dtype=int)
        target_points = interpolated_points[indices]
        CurveManager.copy_to_points(stage, target_points, ref_prims, path_to)
        
                
        #     # TODO maybe?: make this setting for the resolution to sample the curve defined by user
        #     interpolated_points = CurveManager.interpcurve(stage, curve_path, num_samples)
        #     indices = np.linspace(0, len(interpolated_points) - 1, num_points, dtype=int)
        #     target_points = interpolated_points[indices]
        #     CurveManager.copy_to_points(stage, target_points, ref_prims, path_to)