#!/bin/bash

# Set the value of ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS to 8
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8

# Initialize a counter for parallel jobs
parallel_jobs=0
max_jobs=12

# dummy placeholders
fixed_img="0"
moving_img="0"

#tac "../neurite-OASIS/subjects.txt" > "reverse_subjects_OASIS.txt"

while IFS= read -r line; do
	fixed_img=$line
	if [ $moving_img != "0" ]; then
		# create fixed and moving image paths
		fixed_path="../neurite-OASIS/$fixed_img/aligned_norm.nii.gz"
		moving_path="../neurite-OASIS/$moving_img/aligned_norm.nii.gz"
		output_prefix="ANTs/output_${fixed_img}_${moving_img}"
		echo antsRegistrationSyN.sh -n 8 -t so -d 3 -f "$fixed_path" -m "$moving_path" -o "$output_prefix"
		antsRegistrationSyN.sh -n 8 -t so -d 3 -f "$fixed_path" -m "$moving_path" -o "$output_prefix"  &
		# increment parallel jobs
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
	#fixed_img=$moving_img;
	moving_img=$fixed_img
done < "reverse_subjects_OASIS.txt"

# Wait for any remaining background jobs to complete
wait

