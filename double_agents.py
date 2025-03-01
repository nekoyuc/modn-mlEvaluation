import os
import json
import google.generativeai as genai
import time

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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

chat_session_1 = model_assis.start_chat(history=[])
chat_session_2 = model_customer.start_chat(history=[])

with open("Conv_Log.txt", "a") as file:
    file.write("--------------------\n")
    file.write("MODN Test Conversation\n")
    file.write(f"Time: {time.strftime("%Y-%m-%d %H:%M:%S")} \n\n\n")

def conversation_loop(num_turns=10):
    line_assis = "Hello! Welcome to MODN. How can I help you today?\n"
    line_customer = chat_session_2.send_message(line_assis).text
    print("MODN:", line_assis)
    print("Customer:", line_customer)

    with open("Conv_Log.txt", "a") as file:
        file.write(f"MODN: {line_assis}\n\n\n")
        file.write(f"Customer: {line_customer}\n\n\n")

    for i in range(num_turns):
        response_assis = chat_session_1.send_message(line_customer)
        line_assis = response_assis.text
        print("\nMODN:", line_assis)

        response_customer = chat_session_2.send_message(line_assis)
        line_customer = response_customer.text
        print("\nCustomer:", line_customer)

        with open("Conv_Log.txt", "a") as file:
            file.write(f"MODN: {line_assis}\n\n\n")
            file.write(f"Customer: {line_customer}\n\n\n")
        
        time.sleep(10)

conversation_loop()