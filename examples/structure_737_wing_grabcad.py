from afem.config import Settings
from afem.exchange import StepRead
from afem.geometry import *
from afem.graphics import Viewer
from afem.smesh import *
from afem.oml import *
from afem.structure import *
from afem.topology import *

Settings.log_to_console()

# Import wing solid from STEP file
step_read = StepRead(r'../models/boeing_737_wing_grabcad.step')
shape = step_read.shape
solids = ExploreShape.get_solids(shape)
# There should only be one solid that is the wing
solid = solids[0]

# Manually create a wing reference surface. Points came from examination in
# CAD program.
p1 = [0, 0, 0.41811]
p2 = [-299.374016, 0, -4.790998]
c1 = NurbsCurveByPoints([p1, p2]).curve

p1 = [-147.834646, 216.535433, 19.148031]
p2 = [-297.834646, 216.535433, 17.768032]
c2 = NurbsCurveByPoints([p1, p2]).curve

p1 = [-370.472441, 669.291339, 58.555188]
p2 = [-424.050551, 669.291339, 58.597981]
c3 = NurbsCurveByPoints([p1, p2]).curve

sref = NurbsSurfaceByInterp([c1, c2, c3], 1).surface
wing = Body(solid)
wing.set_sref(sref)
wing.set_transparency(0.5)

# Root rib and fuselage radius
r = 148. / 2.
pln = PlaneByAxes((0., r, 0.), 'xz').plane

root_rib = RibBySurface('root rib', pln, wing).rib

# Tip rib
p0 = [-370.472441, 669.291339, 58.555188]
pln = PlaneByAxes(p0, 'xz').plane
tip_rib = RibBySurface('tip rib', pln, wing).rib

# Rear spar
p1 = root_rib.point_from_parameter(0.7, is_rel=True)
p2 = tip_rib.point_from_parameter(0.7, is_rel=True)
rspar = SparByPoints('rear spar', p1, p2, wing).spar

# Front inboard spar
u = root_rib.local_to_global_u(0.15)
p1 = root_rib.point_on_cref(u)
v = wing.sref.vknots[1]
p2 = wing.eval(0.15, v)
inbd_fspar = SparByPoints('inbd front spar', p1, p2, wing).spar

# Front outboard spar
p1 = inbd_fspar.p2
u = tip_rib.local_to_global_u(0.15)
p2 = tip_rib.point_on_cref(u)
outbd_fspar = SparByPoints('outbd front spar', p1, p2, wing).spar

# Adjust root and tip rib reference curve
root_rib.set_p1(inbd_fspar.p1)
root_rib.set_p2(rspar.p1)
tip_rib.set_p1(outbd_fspar.p2)
tip_rib.set_p2(rspar.p2)

# Kink rib
p1 = inbd_fspar.p2
p2 = inbd_fspar.p2
rspar.points_to_cref([p2])
pln = PlaneByIntersectingShapes(inbd_fspar.shape, outbd_fspar.shape, p2).plane
kink_rib = RibByPoints('kink rib', p1, p2, wing, pln).rib

# Inboard ribs
u2 = rspar.invert_cref(kink_rib.p2)
inbd_ribs = RibsAlongCurveByDistance('inbd rib', rspar.cref, 24.,
                                     inbd_fspar.shape, rspar.shape, wing,
                                     d1=12., d2=-24., u2=u2).ribs

# Outboard ribs
outbd_ribs = RibsAlongCurveByDistance('outbd rib', rspar.cref, 24.,
                                      outbd_fspar.shape, rspar.shape, wing,
                                      d1=24, d2=-24., u1=u2).ribs

# Front center spar
xz_pln = PlaneByAxes(axes='xz').plane

p2 = inbd_fspar.p1
p1 = inbd_fspar.p1
ProjectPointToSurface(p1, xz_pln, update=True)

pln = PlaneByIntersectingShapes(inbd_fspar.shape, root_rib.shape, p1).plane
fcspar = SparByPoints('front center spar', p1, p2, wing, pln).spar

# Rear center spar
p2 = rspar.p1
p1 = rspar.p1
ProjectPointToSurface(p1, xz_pln, update=True)
pln = PlaneByIntersectingShapes(rspar.shape, root_rib.shape, p1).plane
rcspar = SparByPoints('rear center spar', p1, p2, wing, pln).spar

# Center ribs
tool = PointsAlongCurveByNumber(rcspar.cref, 4)
i = 1
center_ribs = []
for p in tool.interior_points:
    pln = PlaneByAxes(p, 'xz').plane
    name = ' '.join(['center rib', str(i)])
    rib = RibBetweenShapes(name, fcspar.shape, rcspar.shape, wing, pln).rib
    center_ribs.append(rib)
    i += 1

wing_parts = AssemblyAPI.get_parts(rtype=SurfacePart)

# Fuse wing parts and discard faces
FuseSurfacePartsByCref(wing_parts)
DiscardByCref(wing_parts)

# Skin
skin = SkinByBody('skin', wing).skin
skin.fuse(*wing_parts)

hs = HalfspaceBySurface(tip_rib.sref, [0, 1e6, 0]).solid
skin.discard_by_solid(hs)

# Mesh
print('Meshing the shape...')
the_shape = AssemblyAPI.prepare_shape_to_mesh()
the_gen = MeshGen()
the_mesh = the_gen.create_mesh(the_shape)
alg2d = NetgenAlgo2D(the_gen)
hyp2d = NetgenSimple2D(the_gen, 4.)
the_mesh.add_hypotheses([hyp2d, alg2d])
the_gen.compute(the_mesh, the_shape)

# View
skin.set_transparency(0.5)
v = Viewer()
v.add(AssemblyAPI.get_master())
v.start()
v.add(the_mesh)
v.start()