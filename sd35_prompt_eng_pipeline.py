import os
import subprocess
import operations.operations as op

# Step 1: Generate prompts
command = ["python3", "prompt.py"]
try:
    process = subprocess.Popen(
        command,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = True
    )

    stdout, stderr = process.communicate(input="2\n")

    if stderr:
        print("Error: ", stderr)

except FileNotFoundError:
    print("File not found.")
except Except as e:
    print("Error: ", e)

# Step 2: Copy prompts to Remote
op.copy('/Users/nekoyuc/src/modn-mlEvaluation/prompts.txt', 'yucblob@bigblob.local:SD_3_5_Evaluation/prompts.txt')

# Step 3: Copy additional and negative prompts to Remote
op.copy('/Users/nekoyuc/src/modn-mlEvaluation/prompt_eng.json', 'yucblob@bigblob.local:SD_3_5_Evaluation/prompt_eng.json')

# Step 4: Run Stable Diffusion 3.5 in Remote
remote_user = 'yucblob'
remote_host = 'bigblob.local'
remote_path = 'SD_3_5_Evaluation'

command = f"ssh {remote_user}@{remote_host} 'source .sdvenv/bin/activate; cd {remote_path}; python3 sd3-5_finetuned_from_remote.py'"
os.system(command)

# Step 5: Copy results from Remote
op.copy_folder('yucblob@bigblob.local:SD_3_5_Evaluation/results_3_5_finetuned/', '/Users/nekoyuc/src/modn-mlEvaluation/1v1_image_rater/results_3_5_finetuned/')
print("Results copied successfully.")

# Step 6: Clean up results from folder in Remote
command = f"ssh {remote_user}@{remote_host} 'rm -rf {remote_path}/results_3_5_finetuned'"
os.system(command)

command = f"ssh {remote_user}@{remote_host} 'mkdir -p {remote_path}/results_3_5_finetuned'"
os.system(command)
print("Results cleaned up successfully.")