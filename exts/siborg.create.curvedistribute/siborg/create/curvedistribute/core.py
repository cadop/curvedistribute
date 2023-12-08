from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np
from scipy.interpolate import BSpline
import omni.usd

stage = omni.usd.get_context().get_stage()
print(stage)

# Create an xform which should hold all references in this sample
ref_prim = '/World/Cube'
num_points = 15

prim = stage.GetPrimAtPath('/World/BasisCurves')
points = prim.GetAttribute('points').Get()
points = np.array(points)
print(f'Points: {points}')

# Extract x, y, and z coordinates
x, y, z = points[:, 0], points[:, 1], points[:, 2]

# Create a BSpline object
k = 3 # degree of the spline
t = np.linspace(0, 1, len(points) - k + 1, endpoint=True)
t = np.append(np.zeros(k), t)
t = np.append(t, np.ones(k))
spl = BSpline(t, points, k)

# Interpolate points
tnew = np.linspace(0, 1, num_points)
interpolated_points = spl(tnew)


for i in range(len(interpolated_points)):
    path_to = Sdf.Path(f"/World/intern_target_{i}")
    omni.usd.duplicate_prim(stage, ref_prim, path_to)
    new_prim = stage.GetPrimAtPath(path_to)
    target_pos = Gf.Vec3d(tuple(interpolated_points[i]))
    new_prim.GetAttribute('xformOp:translate').Set(target_pos)

# # Add an internal references 
# for i in range(num_points):
#     intern_target_path = Sdf.Path(f"/World/intern_target_{i}")
#     target_prim = UsdGeom.Xform.Define(stage, intern_target_path).GetPrim()
#     references  = ref_prim.GetReferences()
#     references.AddInternalReference(intern_target_path)



