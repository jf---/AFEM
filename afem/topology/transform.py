# This file is part of AFEM which provides an engineering toolkit for airframe
# finite element modeling during conceptual design.
#
# Copyright (C) 2016-2018  Laughlin Research, LLC (info@laughlinresearch.com)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gce import gce_MakeMirror

from afem.topology.entities import Shape


def mirror_shape(shape, pln):
    """
    Mirror a shape about a plane.

    :param afem.topology.entities.Shape shape: The shape.
    :param afem.geometry.entities.Plane pln: The plane.

    :return: The mirrored shape.
    :rtype: afem.topology.entities.Shape

    :raise RuntimeError: If the transformation fails or is not done.
    """
    trsf = gce_MakeMirror(pln.gp_pln).Value()
    builder = BRepBuilderAPI_Transform(shape.object, trsf, True)
    if not builder.IsDone():
        raise RuntimeError('Failed to mirror the shape.')
    return Shape.wrap(builder.Shape())
