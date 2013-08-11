openmm --coords acp2.pdb --sysxml system.xml --dt 0.5*femtosecond --minimize False --n_steps 5000 --traj_freq 100 --restart_freq 100 --progress_freq 10 --platform CUDA | tee openmm.out
