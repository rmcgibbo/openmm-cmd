openmm --coords input.pdb --protein amber99sb --water tip3p --serialize system.xml --n_steps 1 --minimize False
openmm --coords input.pdb --sysxml system.xml | tee openmm.out
