import os

def copy_prompts_to_drive():
    source_path = '/Users/nekoyuc/src/modn-mlEvaluation/prompts.txt'
    destination_path = '/Users/nekoyuc/Google Drive/My Drive/MODN/Example Images/prompts.txt'   

    with open(source_path, 'r') as src_file:
        content = src_file.read()

    with open(destination_path, 'w') as dest_file:
        dest_file.write(content)

def copy(src_path, dest_path):
    os.system("scp {} {}".format(src_path, dest_path))

def copy_folder(src_path, dest_path):
    os.system("scp -r {} {}".format(src_path, dest_path))
