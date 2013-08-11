openmm --coords ice-water.pdb --ffxml iamoeba.xml --n_steps 20000 --barostat MonteCarloAnisotropic --platform CUDA --polarization direct --rigid_water False --dt 0.5*femtosecond | tee openmm.out
