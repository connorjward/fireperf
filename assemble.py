"""
Script that assembles a matrix.
"""

import argparse

from firedrake import *

from fireperf.form import make_form
from fireperf.mesh import make_mesh


parser = argparse.ArgumentParser()
parser.add_argument("-o", dest="log_file", default="log.txt", type=str)
parser.add_argument("--meta", dest="meta_file", default="metadata.csv", 
                    type=str, help="Location of the metadata file.")
parser.add_argument("--form", default="helmholtz", type=str)
parser.add_argument("--mesh", default="tri", type=str,
                    choices=["tri", "quad", "tet", "hex"])
parser.add_argument("--mesh-refinement-level", default=1, type=int,
                    help="The factor by which to refine the mesh.")
parser.add_argument("--degree", default=1, type=int)
parser.add_argument("--repeats", default=1, type=int)
parser.add_argument("--use-action", action="store_true")
args = parser.parse_args()

mesh = make_mesh(args.mesh, args.mesh_refinement_level)
V = FunctionSpace(mesh, "CG", degree=args.degree)

if args.use_action:
    two_form = make_form(args.form, V)
    form = action(two_form, Function(V))
else:
    form = make_form(args.form, V)

# Do a warm start and save the resulting tensor to prevent reallocation
# in future.
out = assemble(form)

# Enable PETSc logging.
PETSc.Log.begin()

# Do main run.
for _ in range(args.repeats):
    with PETSc.Log.Stage("Assemble"):
        assemble(form, tensor=out)

# Save the log output to a file.
PETSc.Log.view(PETSc.Viewer.ASCII(args.log_file))

# Save the metadata file, appending to the file if it already exists.
with open(args.meta_file, "a") as f:
    # Add a header if the file is empty.
    if f.tell() == 0:
        f.write("filename,form,mesh,mesh_refinement_level,degree,dof\n")

    f.write(f"{args.log_file},{args.form},{args.mesh},{args.mesh_refinement_level},"
            f"{args.degree},{V.dof_count}\n")
