from pxr import Usd, UsdGeom, Gf, Sdf, Vt

import numpy as np
from scipy.interpolate import BSpline, CubicSpline
import omni.usd
from scipy.interpolate import splprep, splev


from . import utils

class CurveManager():
    def __init__(self):
        pass

    @classmethod
    def cubic_bezier(cls, p0, p1, p2, p3, t):
        '''Calculate position on a cubic Bezier curve given four control points.'''
        return ((1 - t)**3) * p0 + 3 * ((1 - t)**2) * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3

    @classmethod
    def create_bezier(cls, control_points, sampling_resolution):
        '''Create a continuous cubic Bezier curve from a list of control points.'''
        curve_points = []
        t = np.linspace(0, 1, sampling_resolution) # defaulted to 100
        for i in range(0, len(control_points) - 3, 3):  # Step strides 3, bezier continous shared handles with neighbors
            p0, p1, p2, p3 = control_points[i], control_points[i + 1], control_points[i + 2], control_points[i + 3]
            bezier_segment = np.array([CurveManager.cubic_bezier(p0, p1, p2, p3, t_) for t_ in t])
            curve_points.extend(bezier_segment)
        return curve_points

    @classmethod
    def create_bspline(cls, control_points, sampling_resolution):
        '''Create a continuous cubic Bezier curve from a list of control points.'''
        # Create a BSpline object
        k = 3 # degree of the spline
        t = np.linspace(0, 1, len(control_points) - k + 1, endpoint=True)
        t = np.append(np.zeros(k), t)
        t = np.append(t, np.ones(k))
        spl = BSpline(t, control_points, k)

        #### If not using evenly distributed points, can just return this
        # tnew = np.linspace(0, 1, num_points)
        # interpolated_points = spl(tnew)
        # return interpolated_points
        
        # Calculate the total arc length of the spline
        fine_t = np.linspace(0, 1, sampling_resolution)
        curve_points = spl(fine_t)
        
        return curve_points

    @classmethod
    def interpcurve(cls, stage, curve_path, num_points, sampling_resolution, curve_type=utils.CURVE.Bspline):
        '''Interpolates a bezier curve based on the input points on the usd'''

        # Get the curve prim and points that define it
        curveprim = stage.GetPrimAtPath(curve_path)
        points = curveprim.GetAttribute('points').Get()
        control_points = np.array(points)
        
        if sampling_resolution == 0: sampling_resolution = num_points
            
        if curve_type == utils.CURVE.Bezier:
            fine_points = CurveManager.create_bezier(control_points, sampling_resolution)
        elif curve_type == utils.CURVE.Bspline:
            fine_points = CurveManager.create_bspline(control_points, sampling_resolution)
        else:
            print("CURVE TYPE NOT IMPLEMENTED")
            return

        distances = np.sqrt(np.sum(np.diff(fine_points, axis=0)**2, axis=1))
        total_length = np.sum(distances)

        # Calculate the length of each segment
        segment_length = total_length / (num_points - 1)

        # Create an array of target lengths
        target_lengths = np.array([i * segment_length for i in range(num_points)])

        # Find the points at the target lengths
        spaced_points = [control_points[0]]  # Start with the first control point
        point_dirs = [fine_points[1]- fine_points[0]] # Store the direction for each point 
        current_length = 0
        j = 1  # Start from the second target length

        for i in range(1, len(fine_points)):
            segment_length = distances[i-1]
            # Create strides to find when the next point should be accepted
            while j < num_points - 1 and current_length + segment_length >= target_lengths[j]:
                # Assign points
                point = fine_points[i]                
                spaced_points.append(point)
                # Get directions
                direction = fine_points[i + 1] - point
                # Normalize the direction vector
                direction /= np.linalg.norm(direction)
                point_dirs.append(direction)
                
                j += 1
            current_length += segment_length

        # End with the last control point
        spaced_points.append(control_points[-1])  
        last_dir = control_points[-1] - control_points[-2]
        last_dir /= np.linalg.norm(last_dir)
        point_dirs.append(last_dir)
        
        return np.array(spaced_points), np.array(point_dirs)
       

    @classmethod
    def copy_to_points(cls, stage, target_points, target_dirs, ref_prims, path_to, _forward_axis, make_instance=False,
                        rand_order=False, use_orient=False, follow_curve=False):
        '''        
        path_to: str, prefix to the prim path. automatically appends Copy
        TODO: rand_order =True, use randomness to determine which prim to place
        TODO: follow_curve=True, set rotation axis to match curve (different than orientation when curve is 3d)
        '''
        
        # Define a path for the new scope prim
        scope_name = 'Copies'
        scope_path = f"/World/{scope_name}"
        # Create the scope prim at the specified path
        scope_prim = UsdGeom.Scope.Define(stage, scope_path)
        
        # Get index of prims that are not None and keep track 
        prim_set = [p for p in ref_prims if p != None]
        # print(prim_set) 
        # print(f'isntance? : {make_instance}')
        
        new_prims = []
        
        if make_instance:

            # Mark the original prims as instanceable if it has no children (like for a mesh)
            for prim_path in prim_set:
                # print(f'{prim_path=}')

                original_prim = stage.GetPrimAtPath(prim_path)
                # print(f'{original_prim=}')
                # If this prim is not wrapped in an xform
                if not original_prim.GetChildren():
                    ref_prim = original_prim
                    
                    ref_prim_suffix = str(ref_prim.GetPath()).split('/')[-1]
                    
                    # Create a new xform inside the scope
                    primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_Source"
                    new_prim_xform_wrapper = stage.DefinePrim(primpath_to, "Xform")
                    
                    # Make this new xform instanceable
                    new_prim_xform_wrapper.SetInstanceable(True)
                    
                    # print(f'xform wrap path {new_prim_xform_wrapper}')
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
                        
                    has_Orient_op = any(op.GetOpType() == UsdGeom.XformOp.TypeOrient for op in xform_ops)
                    if not has_Orient_op:
                        xform.AddOrientOp()
                                                
                    ref_prim= str(new_prim_xform_wrapper.GetPath())

                    original_prim = stage.GetPrimAtPath(ref_prim)
                    # print("finished the xform wrapper")
                
                original_prim.SetInstanceable(True)
                
                new_prims.append(original_prim)

            prim_set = new_prims

        num_prims = len(prim_set)
        cur_idx = 0


        # Place the prims
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
                # Move prim to desired location
                cur_prim = instance_prim
                
            else:
                # Directly duplicate the prim
                ref_prim_suffix = str(ref_prim).split('/')[-1]
                primpath_to = f"{scope_prim.GetPath()}/{ref_prim_suffix}_{i}"
                omni.usd.duplicate_prim(stage, ref_prim, primpath_to)        
                new_prim = stage.GetPrimAtPath(primpath_to)
                cur_prim = new_prim
                
            # Move prim to desired location
            target_pos = Gf.Vec3d(tuple(target_point))
            cur_prim.GetAttribute('xformOp:translate').Set(target_pos)
                

            if use_orient:
                # Make the forward vector face desired direction 
                target_direction = tuple(target_dirs[i])
                # Ensure the target direction is a normalized Gf.Vec3f
                target_direction = Gf.Vec3f(target_direction).GetNormalized()
                target_direction = np.asarray(target_direction)

                # Forward vector, assuming -Z is forward; change as per your convention
                forward_vector = np.array(_forward_axis)
                
                # Compute the cross product (rotation axis)
                rotation_axis = np.cross(forward_vector, target_direction)
                # Compute the dot product and then the angle
                dot_product = np.dot(forward_vector, target_direction)
                rotation_angle = np.arccos(np.clip(dot_product, -1.0, 1.0))  # Clipping for numerical stability
                rot_ax = Vt.Vec3fArray.FromNumpy(rotation_axis)[0]

                # Create a rotation quaternion
                rotation_quat = Gf.Quatf(rotation_angle, rot_ax).GetNormalized()

                # @TODO fix stupid hack
                # Apply the rotation
                try:    cur_prim.GetAttribute('xformOp:orient').Set(Gf.Quatd(rotation_quat))
                except: cur_prim.GetAttribute('xformOp:orient').Set(Gf.Quatf(rotation_quat))

            if cur_idx < num_prims-1: cur_idx +=1
            else: cur_idx = 0


class GeomCreator():
    def __init__(self):
        pass
    
    @classmethod
    def duplicate(cls, _count, _sampling_resolution, _source_curve_model, _source_prim_model, 
                  _use_instance, _use_orient, _forward_axis, _curve_type):
        '''
        ## All of these should work (assuming the named prim is there)
        # ref_prims = ['/World/Cube']
        # ref_prims = ['/World/Cube', None]
        # ref_prims = ['/World/Cube', '/World/Cone']
        '''

        stage = omni.usd.get_context().get_stage()
        curve_path = _source_curve_model.as_string
        ref_prims = [_source_prim_model.as_string]
        ref_prims = _source_prim_model.as_string.replace(' ','').split(',')
        # _use_instance = _use_instance.as_bool

        path_to = f'/Copy'

        sampling_resolution = _sampling_resolution 
        num_points = _count
        # Default to 3x the number of points to distribute? Actually might be handled already by interp
        num_samples = _count
        
        # TODO: make this setting for the resolution to sample the curve defined by user
        interpolated_points, target_dirs = CurveManager.interpcurve(stage, curve_path, num_samples, sampling_resolution, _curve_type)
        indices = np.linspace(0, len(interpolated_points) - 1, num_points, dtype=int)

        target_points = interpolated_points[indices]
        CurveManager.copy_to_points(stage, target_points, target_dirs, ref_prims, path_to, _forward_axis,
                                    make_instance=_use_instance, use_orient=_use_orient)
