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
        assistant_instructions = file.read()
except FileNotFoundError:
    system_instruction = ""
    print("File system_instruction_job_description.txt not found.")
    exit(1)

try:
    with open("system_instruction_speech_code.txt", "r") as file:
        assistant_instructions += file.read()
except FileNotFoundError:
    print("File system_instruction_speech_code.txt not found.")
    exit(1)

with open("double_agents_instructions.json", "r") as file:
    instructions = json.load(file)
#assistant_instructions = instructions["assistant"]
customer_instructions = instructions["customer"]
instructions_combined = assistant_instructions + customer_instructions

model_1 = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction = assistant_instructions
)

model_2 = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction = customer_instructions
)

chat_session_1 = model_1.start_chat(history=[])
chat_session_2 = model_2.start_chat(history=[])

with open("Conv_Log.txt", "a") as file:
    file.write("--------------------\n")
    file.write("MODN Test Conversation\n")
    file.write(f"Time: {time.strftime("%Y-%m-%d %H:%M:%S")} \n\n\n")

def conversation_loop(num_turns=10):
    assistant_line = "Hello! Welcome to MODN. How can I help you today?\n"
    customer_line = chat_session_2.send_message(assistant_line).text
    print("MODN:", assistant_line)
    print("Customer:", customer_line)

    with open("Conv_Log.txt", "a") as file:
        file.write(f"MODN: {assistant_line}\n\n\n")
        file.write(f"Customer: {customer_line}\n\n\n")

    for i in range(num_turns):
        assistant_response = chat_session_1.send_message(customer_line)
        assistant_line = assistant_response.text
        print("\nMODN:", assistant_line)

        customer_response = chat_session_2.send_message(assistant_line)
        customer_line = customer_response.text
        print("\nCustomer:", customer_line)

        with open("Conv_Log.txt", "a") as file:
            file.write(f"MODN: {assistant_line}\n\n\n")
            file.write(f"Customer: {customer_line}\n\n\n")
        
        time.sleep(10)

conversation_loop()