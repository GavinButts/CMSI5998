#!/bin/bash
#SBATCH -N 1                   # Request 1 node
#SBATCH -n 10                  # Request 10 tasks (CPU cores) per node
#SBATCH --mem=20g              # Request 20 gigabytes of memory (adjust based on model requirements)
#SBATCH -J "news"              # Name of the job
#SBATCH -p long                # Run on the 'long' partition
#SBATCH -t 5:00:00             # Maximum duration of 5 hours (adjusted for potentially longer training times)
#SBATCH --gres=gpu:2           # Request 2 GPUs per node
#SBATCH -C A100                # Restrict to A100 NVIDIA GPUs

# Email configuration
#SBATCH --mail-user=gbutts@wpi.edu   # Email address to receive notifications
#SBATCH --mail-type=BEGIN,END,FAIL   # Events triggering email: job starts, ends, or fails

# Activate the virtual environment
source myenv/bin/activate

# Set environment variables (REDACTGED)
export NEWSAPI_KEY=0 
export MONGODB_URI=0

cd ~/turingfiles

# Run the Python scripts sequentially
python buildDatabase.py
python NewsLlama.py
python modelEval.py
