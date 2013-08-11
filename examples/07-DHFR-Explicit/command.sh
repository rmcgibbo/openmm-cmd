openmm --coords dhfr.pdb --protein amber99sb --water tip3p --cutoff 0.9*nanometer --platform CUDA --n_steps 100000 | tee openmm.out
