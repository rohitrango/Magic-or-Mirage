from glob import glob
import time
import numpy as np
import torch
import SimpleITK as sitk
sitk.ProcessObject_SetGlobalWarningDisplay(False)
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

# global lock for thread safe writing
lock = threading.Lock()

DATA_DIR = "../neurite-OASIS"

#def command_iteration(filter):
    #print(f"{filter.GetElapsedIterations():3} = {filter.GetMetric():10.5f}")

def worker(queue):
    while True:
        arg = queue.get()
        if arg is None:
            queue.task_done()
            break
        fix, mov, out = arg
        if os.path.exists(out):
            print("Exists already", out)
            continue
        register(fix, mov, out)
        queue.task_done()

def register(fixed_image_path, moving_image_path, output_file, gaussian=1, iterations=200):
    print(f"Registering {moving_image_path} to {fixed_image_path} and saving at {output_file}")
    fixed = sitk.ReadImage(fixed_image_path)
    moving = sitk.ReadImage(moving_image_path)
    moving.SetSpacing(fixed.GetSpacing())
    moving.SetDirection(fixed.GetDirection())
    moving.SetOrigin(fixed.GetOrigin())

    # match hisotgrams first
    matcher = sitk.HistogramMatchingImageFilter()
    if fixed.GetPixelID() in (sitk.sitkUInt8, sitk.sitkInt8):
        matcher.SetNumberOfHistogramLevels(128)
    else:
        matcher.SetNumberOfHistogramLevels(1024)
    matcher.SetNumberOfMatchPoints(7)
    matcher.ThresholdAtMeanIntensityOn()
    moving = matcher.Execute(moving, fixed)

    # symmetric forces demons
    demons = sitk.FastSymmetricForcesDemonsRegistrationFilter()
    demons.SetNumberOfIterations(iterations)
    # Standard deviation for Gaussian smoothing of displacement field
    demons.SetStandardDeviations(gaussian)
    #demons.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(demons))
    displacementField = demons.Execute(fixed, moving)
    outTx = sitk.DisplacementFieldTransform(displacementField)

    lock.acquire()
    try:
        sitk.WriteTransform(outTx, output_file)
    except:
        print("Could not save", output_file)
        pass
    lock.release()


if __name__ == '__main__':
    # Get images
    files = sorted(glob(osp.join(DATA_DIR, "OASIS*/aligned_norm.nii.gz")))
    fixed, moving = files[:-1], files[1:]
    args = Queue()
    for f, m in zip(fixed, moving):
        fid = f.split("/")[2]
        mid = m.split("/")[2]
        print(fid, mid)
        output = f"Demons/output_{fid}_{mid}.h5"
        args.put((f, m, output))

    # run threads
    num_threads = 8
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(args,))
        t.start()
        threads.append(t)

    q = args
    q.join()
    for _ in range(num_threads):
        q.put(None)
    for t in threads:
        t.join()
    print("All tasks complete.")

