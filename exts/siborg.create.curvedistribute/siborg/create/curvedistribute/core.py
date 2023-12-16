from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd
from scipy.interpolate import splprep, splev

def smooth_path(input_points, num_points=500):
    '''
    Interpolate the path and smooth the verts to be shown
    '''
    def interpolate_curve(points, num_points=100):
        """Interpolate the curve to produce a denser set of points."""
        tck, u = splprep([[p[0] for p in points], [p[1] for p in points], [p[2] for p in points]], s=0)
        u_new = np.linspace(0, 1, num_points)
        x_new, y_new, z_new = splev(u_new, tck)
        return list(zip(x_new, y_new, z_new))

    # Re-define the moving_average function as provided by you
    def moving_average(points, window_size=3):
        """Smoothen the curve using a moving average."""
        if window_size < 3:
            return points  # Too small window, just return original points

        extended_points = points[:window_size-1] + points + points[-(window_size-1):]
        smoothed_points = []

        for i in range(len(points)):
            window = extended_points[i:i+window_size]
            avg_x = sum(pt[0] for pt in window) / window_size
            avg_y = sum(pt[1] for pt in window) / window_size
            avg_z = sum(pt[2] for pt in window) / window_size
            smoothed_points.append((avg_x, avg_y, avg_z))

        return smoothed_points

    # Smooth the original input points
    smoothed_points = moving_average(input_points, window_size=4)

    # Interpolate the smoothed curve to produce a denser set of points
    interpolated_points = interpolate_curve(smoothed_points, num_points=num_points)

    # Smooth the denser set of points
    smoothed_interpolated_points = moving_average(interpolated_points, window_size=6)

    return smoothed_interpolated_points

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
        
        interpolated_points = smooth_path(interpolated_points, num_points)

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
        
        # Define a path for the new scope prim
        scope_name = 'Copies'
        scope_path = f"/World/{scope_name}"
        # Create the scope prim at the specified path
        scope_prim = UsdGeom.Scope.Define(stage, scope_path)
        
        # Get index of prims that are not None and keep track 
        prim_set = [p for p in ref_prims if p != None]
        print(prim_set) 
        
        new_prims = []
        
        # Mark the original prims as instanceable
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
            ref_prim_suffix = str(ref_prim.GetPath()).split('/')[-1]

            primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_{i}"
            prim_type =  ref_prim.GetTypeName()
            
            # Create a new prim and add a reference to the original prim
            instance_prim = stage.DefinePrim(primpath_to, prim_type)
            references = instance_prim.GetReferences()
            references.AddInternalReference(ref_prim.GetPath())

            target_pos = Gf.Vec3d(tuple(target_point))
            instance_prim.GetAttribute('xformOp:translate').Set(target_pos)
            
            if cur_idx < num_prims-1: cur_idx +=1
            else: cur_idx = 0


class GeomCreator():
    def __init__(self):
        pass
    
    @classmethod
    def duplicate(cls, _count, _source_curve_model, _source_prim_model):
        '''
        ## All of these should work (assuming the named prim is there)
        # ref_prims = ['/World/Cube']
        # ref_prims = ['/World/Cube', None]
        # ref_prims = ['/World/Cube', '/World/Cone']
        '''

        stage = omni.usd.get_context().get_stage()
        curve_path = _source_curve_model.as_string
        ref_prims = [_source_prim_model.as_string]


        path_to = f'/Copy'

        num_points = _count
        # Default to 3x the number of points to distribute? Actually might be handled already by interp
        num_samples = _count

        # TODO: make this setting for the resolution to sample the curve defined by user
        interpolated_points = CurveManager.interpcurve(stage, curve_path, num_samples)
        indices = np.linspace(0, len(interpolated_points) - 1, num_points, dtype=int)
        target_points = interpolated_points[indices]
        CurveManager.copy_to_points(stage, target_points, ref_prims, path_to)
