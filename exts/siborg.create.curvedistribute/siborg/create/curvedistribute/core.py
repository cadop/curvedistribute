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


stage = omni.usd.get_context().get_stage()
curve_path = '/World/BasisCurves'
ref_prim = '/World/Cube'
path_to = f'{ref_prim}Copy'
num_points = 15


interpolated_points = interpcurve(stage, curve_path, num_points)
copy_to_points(stage, interpolated_points, ref_prim, path_to)



# # Add an internal references 
# for i in range(num_points):
#     intern_target_path = Sdf.Path(f"/World/intern_target_{i}")
#     target_prim = UsdGeom.Xform.Define(stage, intern_target_path).GetPrim()
#     references  = ref_prim.GetReferences()
#     references.AddInternalReference(intern_target_path)



