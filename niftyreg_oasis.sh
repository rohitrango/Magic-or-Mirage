#!/bin/bash

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8

# Initialize a counter for parallel jobs
parallel_jobs=0
max_jobs=8

fixed_img="0"
moving_img="0"

cmd="/niftyreg/build/reg-apps/reg_f3d"

while IFS= read -r line; do
	fixed_img=$line
	if [ $moving_img != "0" ]; then
		# create paths
		fixed_path="../neurite-OASIS/$fixed_img/aligned_norm.nii.gz"
		moving_path="../neurite-OASIS/$moving_img/aligned_norm.nii.gz"
		output_prefix="niftyreg/output_${fixed_img}_${moving_img}.nii.gz"
		# increment parallel jobs
		$cmd -ref $fixed_path -flo $moving_path -cpp $output_prefix -omp 8 & 
		((parallel_jobs++))
	        # Check if the maximum parallel jobs limit is reached
	        if [ $parallel_jobs -eq $max_jobs ]; then
		  # Wait for all background jobs to complete
		  wait
		  # Reset the parallel jobs counter
		  parallel_jobs=0
	        fi
	fi
	# registration is done
	moving_img=$fixed_img
done < "reverse_subjects_OASIS.txt"

# Wait for any remaining background jobs to complete
wait

