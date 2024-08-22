''' Use pyelastix to test CUMC12 '''
from glob import glob
import time
import numpy as np
import torch
import SimpleITK as sitk
sitk.ProcessObject_SetGlobalWarningDisplay(False)
sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(8)
import argparse
from tqdm import tqdm
import pickle
import nibabel as nib
from subprocess import call
import os
import pprint
from multiprocessing import Pool
from os import path as osp
import threading
from queue import Queue
from itertools import product

cmd="/niftyreg/build/reg-apps/reg_f3d"
cmd_resamp="/niftyreg/build/reg-apps/reg_resample"

def register(fixed_image_path, moving_image_path, fixed_seg_path, moving_seg_path, output_warp, output_deformed, gaussian=1, iterations=200):
    print(f"Registering {fixed_image_path} to {moving_image_path} with seg: {moving_seg_path}")
    print(f"Output warp: {output_warp}")
    print(f"Output deformed: {output_deformed}")
    print()

    # write command to do registration
    command = f"{cmd} -ref {fixed_image_path} -flo {moving_image_path} -cpp {output_warp} -omp 8"
    print(command)
    # input()
    call(command.split())
    # resample the warp now
    resample_command = f"""{cmd_resamp} -ref {fixed_seg_path} -flo {moving_seg_path} -trans {output_warp} -res {output_deformed} -inter 0 -omp 8"""
    print(resample_command)
    call(resample_command.split())


if __name__ == '__main__':
    # Get images
    parser = argparse.ArgumentParser(description='Run niftyreg registration on all datasets')
    parser.add_argument('--dataset', type=str, default='IBSR18', choices=['IBSR18', 'CUMC12', 'LPBA40', 'MGH10'], required=True)
    parser.add_argument('--num_threads', type=int, default=8)
    args = parser.parse_args()

    # create dirs
    output_dirs = f"{args.dataset}/niftyreg/outputs"
    os.makedirs(output_dirs, exist_ok=True)

    # populate queue
    # q = Queue()
    q = []
    dataset = args.dataset
    if dataset == 'IBSR18':
        for i, j in product(range(1, 19), range(1, 19)):
            if i == j:
                continue
            i = str(i).zfill(2)
            j = str(j).zfill(2)
            fixed = f"{dataset}/IBSR_{i}/IBSR_{i}_ana_strip.nii.gz"
            moving = f"{dataset}/IBSR_{j}/IBSR_{j}_ana_strip.nii.gz"
            fixed_seg = f"{dataset}/IBSR_{i}/IBSR_{i}_seg_ana.nii.gz"
            moving_seg = f"{dataset}/IBSR_{j}/IBSR_{j}_seg_ana.nii.gz"
            warp_path = f"{dataset}/niftyreg/outputs/output_{i}_to_{j}_warp.nii.gz"
            deformed_seg_path = f"{dataset}/niftyreg/outputs/deformed_{i}_{j}_seg_ana.nii.gz"
            q.append((fixed, moving, fixed_seg, moving_seg, warp_path, deformed_seg_path))
    elif dataset == 'CUMC12':
        for i, j in product(range(1, 13), range(1, 13)):
            if i == j:
                continue
            fixed = f"{dataset}/Brains/m{i}.nii.gz"
            moving = f"{dataset}/Brains/m{j}.nii.gz"
            moving_seg = f"{dataset}/Atlases/m{j}.nii.gz"
            fixed_seg = f"{dataset}/Atlases/m{i}.nii.gz"
            warp_path = f"{dataset}/niftyreg/outputs/output_{i}_to_{j}_warp.nii.gz"
            deformed_seg_path = f"{dataset}/niftyreg/outputs/deformed_{i}_{j}_seg.nii.gz"
            q.append((fixed, moving, fixed_seg, moving_seg, warp_path, deformed_seg_path))
    elif dataset == 'MGH10':
        for i, j in product(range(1, 11), range(1, 11)):
            if i == j: continue
            fixed = f"{dataset}/Brains/g{i}.nii.gz"
            moving = f"{dataset}/Brains/g{j}.nii.gz"
            moving_seg = f"{dataset}/Atlases/g{j}.nii.gz"
            fixed_seg = f"{dataset}/Atlases/g{i}.nii.gz"
            warp_path = f"{dataset}/niftyreg/outputs/output_{i}_to_{j}_warp.nii.gz"
            deformed_seg_path = f"{dataset}/niftyreg/outputs/deformed_{i}_{j}_seg.nii.gz"
            q.append((fixed, moving, fixed_seg, moving_seg, warp_path, deformed_seg_path))
    elif dataset == 'LPBA40':
        for i, j in product(range(1, 41), range(1, 41)):
            if i == j: continue
            fixed = f"{dataset}/registered_pairs/l{i}_to_l{i}.nii.gz"
            moving = f"{dataset}/registered_pairs/l{j}_to_l{i}.nii.gz"
            fixed_seg = f"{dataset}/registered_label_pairs/l{i}_to_l{i}.nii.gz"
            moving_seg = f"{dataset}/registered_label_pairs/l{j}_to_l{i}.nii.gz"
            warp_path = f"{dataset}/niftyreg/outputs/output_{i}_to_{j}_warp.nii.gz"
            deformed_seg_path = f"{dataset}/niftyreg/outputs/deformed_{i}_{j}_seg.nii.gz"
            q.append((fixed, moving, fixed_seg, moving_seg, warp_path, deformed_seg_path))
    
    # q = q[:1]
    with Pool(args.num_threads) as p:
        p.starmap(register, q)

