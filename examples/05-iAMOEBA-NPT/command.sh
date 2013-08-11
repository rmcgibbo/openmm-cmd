openmm --coords waterbox.pdb --ffxml iamoeba.xml --n_steps 20000 --barostat MonteCarlo --platform CUDA --polarization direct --rigid_water False --dt 0.5*femtosecond | tee openmm.out
