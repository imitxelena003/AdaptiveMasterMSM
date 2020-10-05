"""
This file is part of the AdaptiveMasterMSM package.

"""

import sys, os
import numpy as np
import random
from adaptivemastermsm.launcher import launcher_lib
#import mdtraj as md

def gen_input_weights(n_msm_runs, labels_all, trajs):
    """
        
    Parameters
    ----------
    n_msm_runs : int array
        Number of runs for each macrostate
    labels_all : list
        List of all discretized trajectories
    trajs : List
        List of instances of TimeSeries for all input trajectories

    """

    counter = np.zeros(len(n_msm_runs))
    # generar weights
    w = np.zeros((len(labels_all), len(n_msm_runs)))
    for j, x_j in enumerate(labels_all):
        for i in range(len(n_msm_runs)):
            # row: which traj, column: which label
            index = list_duplicates_of(list(x_j), i)
            w[j][i] = len(index)
        if np.sum(w[j]) > 0.0: w[j] /= np.sum(w[j])

    inputs = []
    for i in range(len(n_msm_runs)):
        while True:
            which_tr_index = random.choices(range(len(labels_all)), weights=w[:,i])
            which_tr = labels_all[which_tr_index[0]]
            # obtain positions in traj where label 'i' is found
            index = list_duplicates_of(list(which_tr), i)
            if len(index) is 0: continue # esto es redundante si weights funciona
            j = random.choice(index)
            map_inputs(trajs[which_tr_index[0]].mdt, i, j, inputs)
            counter[which_tr[j]] += 1
            if n_msm_runs[i] <= counter[which_tr[j]]: break
        
    print(np.sum(counter), counter)
    print(inputs)
    return inputs

def map_inputs(traj, label, frame, inputs):
    """
        
    Parameters
    ----------
    label : int
        Label identifying the initial state of the new input
    frame : int
        Frame corresponding to the initial state for the new input

    """

    fn = '%s_%s.gro'%(label,frame)
    inputs.append(fn)
    #traj[frame].save_gro(fn) #traj[frame].center_coordinates()
    tr = 'data/tr_%s.xtc'%(frame)
    traj[frame].save_xtc(tr)
    tpr = 'data/alaTB.tpr'
    print('ionix',traj[frame].time,traj.time[frame])
    cmd = "gmx trjconv -s %s -f %s -dump %s"%(tpr, tr, traj.time[frame])
    #cmd = "gmx trjconv -f %s -dump %f"%(tr, traj[frame].time)
    os.system(cmd)

    """# frame file
    frame = 'data/frame_%s_%s.ndx'%(label,frame)
    launcher_lib.checkfile(frame)
    inp = open(frame, "w")
    txt = """
    #`[frames]
    #%d
    """ % (frame)
    inp.write(txt)
    inp.close()
    # trajectory file
    tr = 'data/tr_%s.xtc'%(frame)
    traj[frame].save_xtc(tr)
    # create gro file corresponding to snapshot frame from tr trajectory
    cmd = "gmx trjconv -f %s -o %s -fr %s"%(tr, fn, frame)
    os.system(cmd)"""


def list_duplicates_of(seq,item):
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(item,start_at+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs

#def gen_input_dict(n_msm_runs, self.labels_all, self.trajs):
#    state_kv = {}
#    for n in n_msm_runs:
#        if n not in state_kv.keys():
#            print ("Building entry for microstate %g"%n)
#            gen_dict_state(n, an)
#        traj, frame = random.choice(state_kv[n])
#        #print (n, traj, frame)
#    return state_kv

def gen_dict_state(s, trajs, state_kv):
    """
    Generates dictionary entry for state s
    
    Parameters
    ----------
    s : str, int
        The key for the state
    trajs : instance
        Instance of TimeSeries containing all trajectories

    """
    #global state_kv
    state_kv[s] = []
    for t in trajs:
        try:
            ivals = np.where(t.distraj == s)[0]
            for i in ivals:
                state_kv[s].append([t.mdt, i])
        except KeyError:
            pass