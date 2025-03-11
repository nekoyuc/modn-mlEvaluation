import os
import json
import google.generativeai as genai
import time
import re

# Create the model configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

try:
    with open("system_instruction_job_description.txt", "r") as file:
        instructions_assis = file.read()
except FileNotFoundError:
    system_instruction = ""
    print("File system_instruction_job_description.txt not found.")
    exit(1)

try:
    with open("system_instruction_speech_code.txt", "r") as file:
        instructions_assis += file.read()
except FileNotFoundError:
    print("File system_instruction_speech_code.txt not found.")
    exit(1)

with open("double_agents_instructions.json", "r") as file:
    instructions = json.load(file)
#instructions_assis = instructions["assistant"]
instructions_customer = instructions["customer"]
#instructions_combined = instructions_assis + instructions_customer

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model_assis = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction = instructions_assis
)
model_customer = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction = instructions_customer
)
#chat_session_1 = model_assis.start_chat(history=[])
#chat_session_2 = model_customer.start_chat(history=[])

def execute_loop(num_conv=5, num_turns=10):
    with open("prompts.txt", "w") as prompt_file:
        prompt_file.write("")
    with open("dalog.txt", "a") as file:
        file.write("\n\n\n--------------------\n")
        file.write("MODN Test Conversation\n")
        file.write(f"Time: {time.strftime("%Y-%m-%d %H:%M:%S")}")
    for i in range(num_conv):
        with open("dalog.txt", "a") as file:
            file.write(f"\n\nConversation {i+1} started.\n")
        conversation_loop(num_turns)
        i += 1
        

def conversation_loop(num_turns=10):
    with open("Conv_Log.txt", "a") as file:
        file.write("--------------------\n")
        file.write("MODN Test Conversation\n")
        file.write(f"Time: {time.strftime("%Y-%m-%d %H:%M:%S")} \n\n\n")
    
    chat_session_1 = model_assis.start_chat(history=[])
    chat_session_2 = model_customer.start_chat(history=[])

    line_assis = "Hello! Welcome to MODN. How can I help you today?\n"
    line_customer = chat_session_2.send_message(line_assis).text

    with open("Conv_Log.txt", "a") as file:
        file.write(f"MODN: {line_assis}\n\n\n")
        file.write(f"Customer: {line_customer}\n\n\n")

    extracted_prompt = ""

    for i in range(num_turns):
        if not line_customer.strip():
            line_customer = "Can you repeat it?"
            print(f"Empty response from customer. Let customer ask {line_customer}")
            with open("dalog.txt", "a") as file:
                file.write(f"Empty response from customer. Repeating last line. Let customer ask '{line_customer}'.\n")
        response_assis = chat_session_1.send_message(line_customer)
        line_assis = response_assis.text

        response_customer = chat_session_2.send_message(line_assis)
        line_customer = response_customer.text

        with open("Conv_Log.txt", "a") as file:
            file.write(f"MODN: {line_assis}\n\n\n")
            file.write(f"Customer: {line_customer}\n\n\n")

        try:
            # Use regular expression to find content between <prompt> and </prompt>
            match = re.search(r"<prompt>(.*?)</prompt>", line_assis, re.DOTALL) #re.DOTALL allows multiline matching.
            if match:
                extracted_prompt = match.group(1).strip() #group 1 is the part in the parenthesis in the regex. strip removes leading/trailing whitespace.
        except Exception as e:
            print(f"An error occurred: {e}")
            with open("dalog.txt", "a") as file:
                file.write(f"An error occurred: {e}\n")
        
        print("Turn", i+1)
        print("Extracted Prompt:", extracted_prompt)
        with open("dalog.txt", "a") as file:
            file.write(f"Turn {i+1}\n")
            file.write(f"Extracted Prompt: {extracted_prompt}\n")

        if i == num_turns - 1:
            if extracted_prompt != "":
                with open("prompts.txt", "a") as f:
                    f.write(f'"{extracted_prompt}"\n')
                    print(f"Prompt extracted and saved.")
                    with open("dalog.txt", "a") as file:
                        file.write("Prompt extracted and saved.\n")
            else:
                print("No prompt found in the text.")
                with open("dalog.txt", "a") as file:
                    file.write("No prompt found in the text.\n")
        time.sleep(10)

#execute_loop(5, 6)