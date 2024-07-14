import streamlit as st
import os
import re
from datetime import datetime
import json
import zipfile
from io import BytesIO
import google.generativeai as genai


googleToken = "AIzaSyA7SEbEwHRd05IL-rPPcIDv92N8UhhdaJM"


genai.configure(api_key=googleToken)


TASK_COMPLETE_PHRASE = "The task is complete:"



def call_chat_bot(name:str):
    avatars = {
        'junior':'./icons/junior.png',
        'senior':'./icons/senior.png',
        'refiner':'./icons/refiner.png'
    }
    try:
        avatar = avatars[name] 
    except:
        avatar = None

    chat_model = st.chat_message(name,avatar=avatar)
    
    chat_model.write(name)
    return chat_model

def opus_orchestrator(client:genai.GenerativeModel,objective: str, file_content: str = None, previous_results: list = None):

    """
    Calls the Orchestrator to break down the objective into sub-tasks.

    Args:
        objective (str): The main objective to be achieved.
        file_content (str, optional): Content of the file associated with the objective. Defaults to None.
        previous_results (list, optional): List of results from previous sub-tasks. Defaults to None.

    Returns:
        tuple: Response from the orchestrator and file content.
    """
    senoir=call_chat_bot("senoir")
    senoir.markdown("Calling Orchestrator for your objective")
    
    previous_results_text = "\n".join(previous_results) if previous_results else "None"
    if file_content:
        senoir.markdown(f"File content:\n{file_content}")
    messages = [
        {
            "role": "model",
            "parts": "You are an AI orchestrator that breaks down objectives into sub-tasks."
        },
        {
            "role": "user",
            "parts": (f"Based on the following objective{' and file content' if file_content else ''}, and the previous sub-task results (if any), "
                        f"please break down the objective into the next sub-task, and create a concise and detailed prompt for a subagent so it can execute that task. "
                        "IMPORTANT!!! when dealing with code tasks make sure you check the code for errors and provide fixes and support as part of the next sub-task. "
                        "If you find any bugs or have suggestions for better code, please include them in the next sub-task prompt. "
                        "do not talk to much, just provide correct answers and answer to the question only no extra data, keep it short and sweet."
                        "Please assess if the objective has been fully achieved. If the previous sub-task results comprehensively address all aspects of the objective, "
                        f"include the phrase '{TASK_COMPLETE_PHRASE}' at the beginning of your response. If the objective is not yet fully achieved, break it down into the next sub-task "
                        "and create a concise and detailed prompt for a subagent to execute that task.\n\n"
                        f"Objective: {objective}" + (f'\nFile content:\n{file_content}' if file_content else '') + f"\n\nPrevious sub-task results:\n{previous_results_text}")
        }
    ]

    try:
        opus_response = client.generate_content(messages)
        response_text = opus_response.candidates[0].content.parts[0].text
        senoir.markdown(response_text)
        return response_text, file_content
    except Exception as e:
        senoir.markdown(f"Error calling Orchestrator: {e}")
        return "", file_content

def haiku_sub_agent(client:genai.GenerativeModel,prompt: str, previous_haiku_tasks: list = None, continuation: bool = False):
    """
    Calls the sub-agent to handle a specific sub-task.

    Args:
        prompt (str): The prompt for the sub-agent.
        previous_haiku_tasks (list, optional): List of previous haiku tasks. Defaults to None.
        continuation (bool, optional): Indicates if the prompt is a continuation. Defaults to False.

    Returns:
        str: Response from the sub-agent.
    """
    junoir=call_chat_bot("junoir")
    
        
    if previous_haiku_tasks is None:
        previous_haiku_tasks = []

    continuation_prompt = "Continuing from the previous answer, please complete the response do not talk to much, do not explain anything just provide correct answers and answer to the question only no extra data, keep it short and sweet."
    system_message = "Previous Haiku tasks:\n" + "\n".join(f"Task: {task['task']}\nResult: {task['result']}" for task in previous_haiku_tasks)
    if continuation:
        prompt = continuation_prompt

    messages = [
        {
            "role": "model",
            "parts": system_message
        },
        {
            "role": "user",
            "parts": prompt
        }
    ]

    try:
        opus_response = client.generate_content(messages)
        response_text = opus_response.candidates[0].content.parts[0].text
        junoir.markdown(response_text)
        return response_text
    except Exception as e:
        junoir.markdown(f"Error calling Sub-agent: {e}")
        return ""
    
def opus_refine(client:genai.GenerativeModel,objective: str, sub_task_results: list, filename: str, projectname: str, continuation: bool = False):
    """
    Calls Opus to refine the sub-task results into a cohesive final output.

    Args:
        objective (str): The main objective to be achieved.
        sub_task_results (list): List of results from sub-tasks.
        filename (str): The filename for the final output.
        projectname (str): The name of the project.
        continuation (bool, optional): Indicates if the refinement is a continuation. Defaults to False.

    Returns:
        str: The refined final output.
    """
    refiner = call_chat_bot("refiner")
    refiner.markdown("Calling Opus to provide the refined final output for your objective")
    messages = [
        {
            "role": "model",
            "parts": "You are an AI assistant that refines sub-task results into a cohesive final output."
        },
        {
            "role": "user",
            "parts": (f"Objective: {objective}\n\nSub-task results:\n" + "\n".join(sub_task_results) + 
                        "\n\nPlease review and refine the sub-task results into a cohesive final output. Add any missing information or details as needed. "
                        "Make sure the code files are completed. When working on code projects, ONLY AND ONLY IF THE PROJECT IS CLEARLY A CODING ONE please provide the following:\n"
                        "1. Project Name: Create a concise and appropriate project name that fits the project based on what it's creating. The project name should be no more than 20 characters long.\n"
                        "2. Folder Structure: Provide the folder structure as a valid JSON object, where each key represents a folder or file, and nested keys represent subfolders. Use null values for files. "
                        "Ensure the JSON is properly formatted without any syntax errors. Please make sure all keys are enclosed in double quotes, and ensure objects are correctly encapsulated with braces, "
                        "separating items with commas as necessary.\nWrap the JSON object in <folder_structure> tags.\n"
                        "3. Code Files: For each code file, include ONLY the file name in this format like this: 'Filename: <filename>' NEVER EVER USE THE FILE PATH OR ANY OTHER FORMATTING YOU ONLY USE THE FOLLOWING format "
                        "'Filename: <filename>' followed by the code block enclosed in triple backticks, with the language identifier after the opening backticks, like this:\n\n​python\n<code>\n​")
        }
    ]

    try:
        opus_response = client.generate_content(messages)
        response_text = opus_response.candidates[0].content.parts[0].text
        refiner.markdown(response_text)
        return response_text
    except Exception as e:
        refiner.markdown(f"Error calling Refiner: {e}")
        return ""
        


def create_folder_structure(project_name: str, folder_structure: dict, code_blocks: list):
    """
    Creates the folder structure and files based on the provided structure and code blocks.

    Args:
        project_name (str): The name of the project.
        folder_structure (dict): The folder structure as a dictionary.
        code_blocks (list): List of code blocks with filenames.
    """
    try:
        os.makedirs(project_name, exist_ok=True)
        create_folders_and_files(project_name, folder_structure, code_blocks)
    except OSError as e:
        print(e)
        return



def create_folders_and_files(current_path: str, structure: dict, code_blocks: list):
    """
    Recursively creates folders and files based on the provided structure.

    Args:
        current_path (str): The current path to create folders and files in.
        structure (dict): The folder structure as a dictionary.
        code_blocks (list): List of code blocks with filenames.
    """
    for key, value in structure.items():
        path = os.path.join(current_path, key)
        if isinstance(value, dict):
            try:
                os.makedirs(path, exist_ok=True)
                create_folders_and_files(path, value, code_blocks)
            except OSError as e:
                print(e)
        else:
            code_content = next((code for file, code in code_blocks if file == key), None)
            if code_content:
                try:
                    with open(path, 'w') as file:
                        file.write(code_content)
                except IOError as e:
                    print(e)



def load(objective:str):
    senoirClient = genai.GenerativeModel(st.session_state['senoir'])
    junoirClient = genai.GenerativeModel(st.session_state['junoir'])
    refinerClient = genai.GenerativeModel(st.session_state['refiner'])
    # Check if the input contains a file path
    if "./" in objective or "/" in objective:
        file_path = re.findall(r'[./\w]+\.[\w]+', objective)[0]
        with open(file_path, 'r') as file:
            file_content = file.read()
        objective = objective.split(file_path)[0].strip()
    else:
        file_content = None

    task_exchanges = []
    haiku_tasks = []

    while True:
        previous_results = [result for _, result in task_exchanges]
        if not task_exchanges:
            opus_result, file_content_for_haiku = opus_orchestrator(senoirClient,objective, file_content, previous_results)
        else:
            opus_result, _ = opus_orchestrator(senoirClient,objective, previous_results=previous_results)

        if TASK_COMPLETE_PHRASE in opus_result:
            final_output = opus_result.replace(TASK_COMPLETE_PHRASE, "").strip()
            break
        else:
            sub_task_prompt = opus_result
            if file_content_for_haiku and not haiku_tasks:
                sub_task_prompt = f"{sub_task_prompt}\n\nFile content:\n{file_content_for_haiku}"
            sub_task_result = haiku_sub_agent(junoirClient,sub_task_prompt, haiku_tasks)
            haiku_tasks.append({"task": sub_task_prompt, "result": sub_task_result})
            task_exchanges.append((sub_task_prompt, sub_task_result))
            file_content_for_haiku = None

    sanitized_objective = re.sub(r'\W+', '_', objective)
    timestamp = datetime.now().strftime("%H-%M-%S")
    refined_output = opus_refine(junoirClient,objective, [result for _, result in task_exchanges], timestamp, sanitized_objective)

    project_name_match = re.search(r'Project Name: (.*)', refined_output)
    project_name = project_name_match.group(1).strip() if project_name_match else sanitized_objective

    folder_structure_match = re.search(r'<folder_structure>(.*?)</folder_structure>', refined_output, re.DOTALL)
    folder_structure = {}
    if folder_structure_match:
        json_string = folder_structure_match.group(1).strip()
        try:
            folder_structure = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError

    code_blocks = re.findall(r'Filename: (\S+)\s*```[\w]*\n(.*?)\n```', refined_output, re.DOTALL)
    create_folder_structure(project_name, folder_structure, code_blocks)
    create_download_link(project_name)

    max_length = 25
    truncated_objective = sanitized_objective[:max_length] if len(sanitized_objective) > max_length else sanitized_objective
    filename = f"{timestamp}_{truncated_objective}.md"

    exchange_log = f"Objective: {objective}\n\n" + "=" * 40 + " Task Breakdown " + "=" * 40 + "\n\n"
    for i, (prompt, result) in enumerate(task_exchanges, start=1):
        exchange_log += f"Task {i}:\nPrompt: {prompt}\nResult: {result}\n\n"
    exchange_log += "=" * 40 + " Refined Final Output " + "=" * 40 + "\n\n" + refined_output


    with open(filename, 'w') as file:
        file.write(exchange_log)
    print(f"\nFull exchange log saved to {filename}")

def zip_folder(folder_path):
    # Create a bytes buffer to hold the zip file data
    zip_buffer = BytesIO()
    
    # Create a zip file object
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk the folder and add files to the zip file
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zip_file.write(file_path, arcname)
    
    # Move the buffer's position to the start
    zip_buffer.seek(0)
    
    return zip_buffer

def create_download_link(name:str):
    zip_buffer = zip_folder(name)
            
    st.download_button(
        label="Download Zip",
        data=zip_buffer,
        file_name=f"{name}.zip",
        mime="application/zip"
    )


st.set_page_config(
    page_title="XYZ",
    page_icon=":speach_ballon:"
)

models = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


with st.sidebar:
    st.subheader("Settings")
    
    st.write("Hello To AI World")


    st.selectbox("select a senoir",models,key="senoir")
    st.selectbox("select a junoir",models,key="junoir")
    st.selectbox("select a refiner",models,key="refiner")


user_query = st.chat_input("Type your prompt ....")

if user_query is not None and user_query.strip() != "":
    user = call_chat_bot("Human")
    user.markdown(user_query)
    load(user_query)
   