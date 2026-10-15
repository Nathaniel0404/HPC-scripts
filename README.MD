# HPC HPCG Benchmarking Scripts

These were the scripts used to generate various experiment configurations based on the parameters we were testing. 

`build_hpcg.py` was used to generate a new directory to hold a new build based on differnt compiler optimisations.

`generate_experiments.py` was used to generate a separate directory for each experiment we wanted to run, which contained the config, slurm script and output files.

`run_experiments.py` was used to run the different slurm scripts in each experiment directory.

`parse_results.py` was used to look through each experiment directory, collect the relevant results and config, and consolidate the information in a csv file to allow for analysis.