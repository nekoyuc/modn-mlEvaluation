import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    #system_instruction=system_instructions,
)

num_prompts = 50

print("Select an option:")
print("1. Start chat session")
print(f"2. Generate {num_prompts} prompts in prompts.txt")

user_choice = input("Enter 1 or 2: ").strip()

try:
    with open("system_instruction_job_description.txt", "r") as file:
        system_instruction = file.read()
except FileNotFoundError:
    system_instruction = ""
    print("File system_instruction_job_description.txt not found.")
    exit(1)

if user_choice == "1":
    try:
        with open("system_instruction_speech_code.txt", "r") as file:
            system_instruction += file.read()
    except FileNotFoundError:
        print("File system_instruction_speech_code.txt not found.")
        exit(1)
elif user_choice == "2":
    pass
else:
    print("Invalid choice. Exiting program.")

model = genai.GenerativeModel(system_instruction=system_instruction,)
chat_session = model.start_chat(history=[])

if user_choice == "1":
    print("\nChat session started. Type 'quit' to exit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Ending chat session.")
            break
        response = chat_session.send_message(user_input)
        print("\nAI: " + response.text)
        
elif user_choice == "2":
    request = f"Imagine a customer comes in with {num_prompts} random orders, make a list of summarization of these orders. In your response, put each order in double quotes and separate them with a comma, put each order on a new line. No need to say anything else besides the list of orders."
    response = chat_session.send_message(request)
    with open("prompts.txt", "w") as file:
        file.write(response.text)
    print(f"Prompts generated and saved in prompts.txt")

else:
    print("Invalid choice. Exiting program.")