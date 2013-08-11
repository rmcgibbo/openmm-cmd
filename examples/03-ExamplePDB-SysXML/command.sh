openmm --coords input.pdb --protein amber99sb --water tip3p --serialize system.xml
openmm --coords input.pdb --sysxml system.xml | tee openmm.out
