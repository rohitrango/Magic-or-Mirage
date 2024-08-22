#!/bin/bash

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8

# Initialize a counter for parallel jobs
parallel_jobs=0
max_jobs=12

fixed_img="0"
moving_img="0"

while IFS= read -r line; do
	fixed_img=$line
	if [ $moving_img != "0" ]; then
		# create paths
		fixed_path="../neurite-OASIS/$fixed_img/aligned_norm.nii.gz"
		moving_path="../neurite-OASIS/$moving_img/aligned_norm.nii.gz"
		output_prefix="Greedy/output_${fixed_img}_${moving_img}"
		# increment parallel jobs
		greedy -d 3 -m WNCC 2x2x2 -i "$fixed_path" "$moving_path" -o "${output_prefix}_warp.nii.gz" -n 100x100x40 -s 1.5mm 0.5mm &
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

