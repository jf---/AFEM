from afem.geometry import *
from afem.graphics import Viewer
from afem.smesh import *
from afem.oml import *
from afem.structure import *
from afem.topology import *

# Inputs
diameter = 244
length = 360
main_floor_yloc = -12
cargo_floor_yloc = -108
frame_height = 3.5
frame_spacing = 24
floor_beam_height = 6

# Calculate
radius = diameter / 2.

# Create a solid cylinder to represent fuselage section.
cylinder = SolidByCylinder(radius, length).solid
fuselage = Body(cylinder)

# Skin
skin = SkinByBody('skin', fuselage).skin

# Trim off closed ends of skin since it came from a solid cylinder.
pln1 = PlaneByAxes(axes='xy').plane
box = SolidByPlane(pln1, 1e6, 1e6, -1e6).solid
skin.cut(box)

pln2 = PlaneByAxes((0., 0., length), 'xy').plane
box = SolidByPlane(pln2, 1e6, 1e6, 1e6).solid
skin.cut(box)

# Floor
pln = PlaneByAxes((0., main_floor_yloc, 0.), 'xz').plane
main_floor = FloorBySurface('main floor', pln, fuselage).floor

pln = PlaneByAxes((0., cargo_floor_yloc, 0.), 'xz').plane
cargo_floor = FloorBySurface('cargo floor', pln, fuselage).floor

# Frames
frames = FramesBetweenPlanesByDistance('frame', pln1, pln2, frame_spacing,
                                       fuselage, frame_height).frames

# Floor beams and posts
rev_cylinder = cylinder.Reversed()
above_floor = ShapeByDrag(main_floor.shape, (0., 2. * diameter, 0.)).shape
below_cargo_floor = ShapeByDrag(cargo_floor.shape, (0., -60., 0.)).shape

pln1 = PlaneByAxes((-.667 * radius, 0., 0.), 'yz').plane
face1 = FaceByPlane(pln1, -diameter, diameter, 0., length).face

pln2 = PlaneByAxes((.667 * radius, 0., 0.), 'yz').plane
face2 = FaceByPlane(pln2, -diameter, diameter, 0., length).face

i = 1
for frame in frames:
    # Beam
    shape = IntersectShapes(main_floor.shape, frame.sref).shape
    shape = ShapeByDrag(shape, (0., -floor_beam_height, 0.)).shape
    name = ' '.join(['floor beam', str(i)])
    beam = SurfacePart(name, shape)
    beam.cut(rev_cylinder)

    # Post
    name = ' '.join(['left floor post', str(i)])
    shape = IntersectShapes(face1, frame.sref).shape
    post = CurvePart(name, shape)
    post.cut(above_floor)
    post.cut(rev_cylinder)

    name = ' '.join(['right floor post', str(i)])
    shape = IntersectShapes(face2, frame.sref).shape
    post = CurvePart(name, shape)
    post.cut(above_floor)
    post.cut(rev_cylinder)

    # Create segment beneath cargo floor and merge with frame.
    frame_pln_face = FaceBySurface(frame.sref).face
    shape = CommonShapes(below_cargo_floor, frame_pln_face).shape
    shape = CutShapes(shape, rev_cylinder).shape
    frame.merge(shape, True)
    i += 1

main_floor.set_transparency(0.5)
cargo_floor.set_transparency(0.5)

all_parts = AssemblyAPI.get_parts(order=True)

# Split all parts together
join = SplitParts(all_parts)

# Mesh
the_shape = AssemblyAPI.prepare_shape_to_mesh()
the_gen = MeshGen()
the_mesh = the_gen.create_mesh(the_shape)

# Unstructured quad-dominant
ngh = NetgenSimple2D(the_gen, 4.)
nga = NetgenAlgo2D(the_gen)
the_mesh.add_hypotheses([ngh, nga])

# Max edge length
hy1d = MaxLength1D(the_gen, 4.)
alg1d = Regular1D(the_gen)
the_mesh.add_hypotheses([hy1d, alg1d])

# Mapped quads applied to applicable faces
mapped_hyp = QuadrangleHypo2D(the_gen)
mapped_algo = QuadrangleAlgo2D(the_gen)

for face in ExploreShape.get_faces(the_shape):
    if mapped_algo.is_applicable(face, True):
        the_mesh.add_hypotheses([mapped_hyp, mapped_algo], face)

the_gen.compute(the_mesh)

# View
v = Viewer()
v.add(AssemblyAPI.get_master())
v.add(the_mesh)
v.start()