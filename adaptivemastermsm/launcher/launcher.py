"""
This file is part of the AdaptiveMasterMSM package.

"""
#!/usr/bin/env python

import os
import subprocess
import shlex

# AdaptiveMasterMSM
from adaptivemastermsm.system import system

class Launcher(object):
    """
    Call GROMACS and process output to pass it to class analyzer
    """

    def __init__(self, md_step, forcefield, water, \
            filepdb, wet_xtc_file,  dry_xtc_file=None, last_wet_snapshot=None):
        """
        Read input from system, run MD, and process output
        for the class analyzer

        Args:
            ¿sysfile (str): File containing system information?
            md_step (str): 'Equilibration' or 'Production'
            filepdb (str): PDB file defining the system
            wet_xtc_file (str)
            dry_xtc_file (str)
            last_wet_snapshot (str)

        ¿Return?:
            trajfile (str): File containing processed trajectories
        """

        self.pdb = filepdb
        self.dry_xtc_file = dry_xtc_file
        self.last_wet_snapshot = last_wet_snapshot
        # create an instance of system class
        params = system.System(water, md_step, 1)

        if params.md_step == 'Production':
            cmd = 'gmx pdb2gmx -f %s -o %s_processed.gro -ff %s -water %s' % \
                    (filepdb, filepdb, forcefield, params.water)
            print(" running: ",cmd)
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            print(out, err)
            self.wet_xtc_file = wet_xtc_file
            
            # set multiprocessing options
            n_threads = mp.cpu_count()
            pool = mp.Pool(processes=n_threads)
            # run simulations
            gmxinput = [["data/%s" % i, "data/pull/%s" % i] \
                        for i in range(n_short_runs)]
            results = []
            for x in gmxinput:
                results.append(pool.apply_async(run_md, [x]))
            # close the pool and wait for each running task to complete
            pool.close()
            pool.join()
            for result in results:
                out, err = result.get()
                print("out: {} err: {}".format(out, err))

        elif params.md_step == 'Equilibration':
            # first equilibrate
            cmd = 'gmx pdb2gmx -f %s -o %s_processed.gro -ff %s -water %s -ignh' % \
                    (filepdb, filepdb, forcefield, params.water)
            print(" running: ",cmd)
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            print(out, err)
            out, err = params.build_box(1) # el numero es provisional
            print(out, err, "ionix")
            user_wet_xtc_file = wet_xtc_file
            self.wet_xtc_file = 'equilibration.xtc'
            self.run_md(4, params)
            os.system('cp end.gro %s_processed.gro' % filepdb)
           
            # then production
            # p.md_step = 'Production'  #ionix, ojo aqui, por eso i+1=2
            p_prod = system.System(water, 'Production', 2)
            self.wet_xtc_file = user_wet_xtc_file
            self.run_md(n_threads, p_prod)

        self.clean_working_directory()

        return

    def run_md(self, n_threads, params):
        """
    def run_md(self, x):
        
        md_step = x[0]
        tpr = x[1]
        mdp = x[2]
        n_threads = x[3]
        """

        # note for the moment wet_xtc_file, dry_xtc_file and last_wet_snapshot
        # overwrite each other, until I see their need

        cmd = 'gmx grompp -f %s -c %s_processed.gro -p topol.top -maxwarn 1'\
                % (params.md_step, self.filepdb); \
                'gmx mdrun -nt %d -s topol.tpr -x %s -c end.gro -g prod.log' % \
                (n_threads, self.wet_xtc_file)
        print(" running: ",cmd)
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        # if running in production mode, trjconv to create a dry XTC
        if params.md_step == 'Production':
            assert self.dry_xtc_file is not None and self.last_wet_snapshot is not None
            cmd = 'echo 0 | gmx trjconv -f end.gro -s topol.tpr -o %s -pbc whole' % self.last_wet_snapshot
            print(" running: ",cmd)
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = p.communicate()
            print(output, error)
            cmd = 'echo PROTEIN | gmx trjconv -f %s -s topol.tpr -o %s -pbc whole' % (self.wet_xtc_file, self.dry_xtc_file)
            print(" running: ",cmd)
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = p.communicate()
            print(output, error)

        return (out, err)

    def clean_working_directory(self):

        print ("Cleaning up...")
        os.system('rm \#*')
        os.system('mkdir logs')
        os.system('mv *.log logs')
        os.system('rm *.trr *.top *.itp *.edr *.cpt *.tpr out.gro conf.gro')
        os.system('mv equilibration.xtc *.mdp *.gro logs')
    
        return