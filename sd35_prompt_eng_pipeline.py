import os
import subprocess
import operations.operations as op

def sd35pipeline(it_num):
    # Step 1: Generate prompts
    command = ["python3", "prompt.py"]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input="2\n")

        if stderr:
            print("Error: ", stderr)

    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("Error: ", e)
    print("Step 1 - Prompts generated successfully.")

    # Step 2: Copy prompts to Remote
    op.copy('/Users/nekoyuc/src/modn-mlEvaluation/prompts.txt', 'yucblob@bigblob.local:SD_3_5_Evaluation/prompts.txt')
    print("Step 2 - Prompts copied successfully.")

    # Step 3: Copy additional and negative prompts to Remote
    op.copy('/Users/nekoyuc/src/modn-mlEvaluation/prompt_eng.json', 'yucblob@bigblob.local:SD_3_5_Evaluation/prompt_eng.json')
    print("Step 3 - Additional and negative prompts copied successfully.")

    # Step 4: Run Stable Diffusion 3.5 in Remote
    remote_user = 'yucblob'
    remote_host = 'bigblob.local'
    remote_path = 'SD_3_5_Evaluation'

    command = f"ssh {remote_user}@{remote_host} 'source .sdvenv/bin/activate; cd {remote_path}; python3 sd3-5_finetuned_from_remote.py'"
    os.system(command)
    print("Step 4 - Stable Diffusion 3.5 ran successfully.")

    # Step 5: Copy results from Remote
    op.copy('yucblob@bigblob.local:SD_3_5_Evaluation/prompts.txt', 'yucblob@bigblob.local:SD_3_5_Evaluation/results_3_5_finetuned/prompts.txt')
    op.copy_folder('yucblob@bigblob.local:SD_3_5_Evaluation/results_3_5_finetuned/', f'/Users/nekoyuc/src/modn-mlEvaluation/1v1_image_rater/results_3_5_finetuned_{it_num}/')
    print("Step 5 - Results copied successfully.")

    # Step 6: Clean up results from folder in Remote
    command = f"ssh {remote_user}@{remote_host} 'rm -rf {remote_path}/results_3_5_finetuned'"
    os.system(command)

    command = f"ssh {remote_user}@{remote_host} 'mkdir -p {remote_path}/results_3_5_finetuned'"
    os.system(command)
    print("Step 6 - Results cleaned up successfully.")

    # Step 7: Copy additional and negative prompts to result folder
    op.copy('/Users/nekoyuc/src/modn-mlEvaluation/prompt_eng.json', f'/Users/nekoyuc/src/modn-mlEvaluation/1v1_image_rater/results_3_5_finetuned_{it_num}/')
    print("Step 7 - Additional and negative prompts copied successfully.")


i = 66
while i < 71:
    print(f"\nRunning pipeline for iteration {i}")
    sd35pipeline(i)
    i += 1