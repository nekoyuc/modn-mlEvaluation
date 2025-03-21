import base64
import os
from google import genai
from google.genai import types
import random
import time
import re

config_written = False

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()

def generate(iter, temp, prompt):
    global config_written
    file1 = ""
    file2 = ""
    file3 = ""
    img_dir = "img_examples/complex_pattern/"
    img_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if os.path.isfile(os.path.join(img_dir, f))]
    '''
    selected_files = random.sample(img_files, 3)
    file1, file2, file3 = selected_files
    '''
    while not file1.endswith(".png"):
        selected_files = random.sample(img_files, 1)
        file1 = selected_files[0]

    new_folder = f'gemini_images/gemini_img/batch{iter}/'
    os.makedirs(new_folder, exist_ok=True)
    n = 1
    for file in selected_files:
        new_file_path = os.path.join(new_folder, f"{n}th_" + os.path.basename(file))
        with open(file, 'rb') as fsrc, open(new_file_path, 'wb') as fdst:
            fdst.write(fsrc.read())
        n += 1

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    print("File: ", file1)
    files = [
        # Make the file available in local system working directory
        client.files.upload(file=file1),
        # Make the file available in local system working directory
        #client.files.upload(file=file2),
        # Make the file available in local system working directory
        #client.files.upload(file=file3),
    ]
    model = "gemini-2.0-flash-exp-image-generation"
    user_text = prompt + ". Leave the object empty, show the full extent of the whole object, do not include any other objects. Keep the background, mono-colored, plain and simple. Reference and imitate style of the uploaded image. If the image style is inconsistent with the request, just try your best and go do it."
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text=user_text),
            ],
        ),
        '''
        types.Content(
            role="model",
            parts=[
                types.Part.from_uri(
                    file_uri=files[3].uri,
                    mime_type=files[3].mime_type,
                ),
            ],
        ),
        '''
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=temp,
        top_p=0.55,
        top_k=1000,
        max_output_tokens=8192,
        response_modalities=[
            "image",
            "text",
        ],
        response_mime_type="text/plain",
    )

    if config_written == False:
        config_written = True
        config_file_path = "gemini_images/gemini_img/config.txt"
        with open(config_file_path, "a") as config_file:
            config_file.write(f"Temperature: {generate_content_config.temperature}\n")
            config_file.write(f"Top P: {generate_content_config.top_p}\n")
            config_file.write(f"Top K: {generate_content_config.top_k}\n")
            config_file.write(f"Max Output Tokens: {generate_content_config.max_output_tokens}\n")
            config_file.write(f"Response Modalities: {', '.join(generate_content_config.response_modalities)}\n")
            config_file.write(f"Response Mime Type: {generate_content_config.response_mime_type}\n")
            config_file.write(f"Prompt: {user_text}\n")

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
        if chunk.candidates[0].content.parts[0].inline_data:
            file_name = new_folder + "gemini_image.png"
            save_binary_file(
                file_name, chunk.candidates[0].content.parts[0].inline_data.data
            )
            print(
                "File of mime type"
                f" {chunk.candidates[0].content.parts[0].inline_data.mime_type} saved"
                f"to: {file_name}"
            )
        else:
            print(chunk.text)
    time.sleep(5)

if __name__ == "__main__":
    prompt = input("Type your image description here:\n").strip()
    for t in range(3):
        repetition = 0
        while repetition < 2:
            config_written = False
            for i in range(10):
                generate(i, t, prompt)

            base_dir = "/Users/nekoyuc/src/modn-mlEvaluation/gemini_images/"
            def get_next_batch_number(base_dir):
                max_number = 0
                for dir_name in os.listdir(base_dir):
                    if dir_name.startswith("gemini_img"):
                        try:
                            number = int(dir_name.replace("gemini_img", ""))
                            if number > max_number:
                                max_number = number
                        except ValueError:
                            continue
                return max_number + 1

            next_batch_number = get_next_batch_number(base_dir)
            print(f"Next batch number: {next_batch_number}")
            os.rename(os.path.join(base_dir, "gemini_img"), os.path.join(base_dir, f"gemini_img{next_batch_number}"))

            repetition += 1
        t += 1
