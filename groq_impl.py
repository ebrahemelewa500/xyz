import streamlit as st          #package to make an interface webpage.
from groq import Groq           
import os                       #internal package to act with files to copy-read paths.
import re                       #Regular Expression Engine to make search in text more easier.
from datetime import datetime   #to deal with dates
import json   
import zipfile   
from io import BytesIO               

token1="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"       #to use API Key
token2="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"       #to use aditional API Key if limit Expired

client = Groq(api_key=token1)           #setup initial configuration for groq



TASK_COMPLETE_PHRASE = "The task is complete:"          #when therefiner watcg this sentence it creates project files to Download


def call_chat_bot(name:str):                            # to put icon avatar photo to Ai models  & to show name of every Ai Model
    avatars = {                                         
        'junior':'./icons/junior.png',
        'senior':'./icons/senior.png',
        'refiner':'./icons/refiner.png'
    }
    try:
        avatar = avatars[name] 
    except:
        avatar = None

    agent_chat_messenger = st.chat_message(name,avatar=avatar)
    
    agent_chat_messenger.write(name)
    return agent_chat_messenger
    


def senior_orchestrator(objective: str, file_content: str = None, previous_results: list = None):         #  Calls the Orchestrator to break down the objective into sub-tasks

    """
    Calls the Orchestrator to break down the objective into sub-tasks.

    Args:
        objective (str): The main objective to be achieved.
        file_content (str, optional): Content of the file associated with the objective. Defaults to None.
        previous_results (list, optional): List of results from previous sub-tasks. Defaults to None.

    Returns:
        tuple: Response from the orchestrator and file content.
    """
    senior=call_chat_bot("senior")
    senior.markdown("Calling Orchestrator for your objective")
    
    previous_results_text = "\n".join(previous_results) if previous_results else "None"
    messages = [
        {
            "role": "system",
            "content": "You are an AI orchestrator that breaks down objectives into sub-tasks."
        },
        {
            "role": "user",
            "content": (f"Based on the following objective{' and file content' if file_content else ''}, and the previous sub-task results (if any), "
                        f"break down the objective into the next sub-task, and create a concise and detailed prompt for a subagent so it can execute that task. "
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
        senior_response = client.chat.completions.create(
            model=st.session_state['senior'],
            messages=messages,
            max_tokens=8000
        )
        response_text = senior_response.choices[0].message.content
        senior.markdown(response_text)
        return response_text, file_content
    except Exception as e:
        senior.markdown(f"Error calling Orchestrator: {e}")
        return "", file_content

def junior_sub_agent(prompt: str, previous_junior_tasks: list = None, continuation: bool = False):         # Calls the sub-agent to handle a specific sub-task.
    """
    Calls the sub-agent to handle a specific sub-task.

    Args:
        prompt (str): The prompt for the sub-agent.
        previous_haiku_tasks (list, optional): List of previous haiku tasks. Defaults to None.
        continuation (bool, optional): Indicates if the prompt is a continuation. Defaults to False.

    Returns:
        str: Response from the sub-agent.
    """
    junior=call_chat_bot("junior")
    
        
    if previous_junior_tasks is None:
        previous_junior_tasks = []

    continuation_prompt = "Continuing from the previous answer, please complete the response do not talk to much, do not explain anything just provide correct answers and answer to the question only no extra data, keep it short and sweet."
    system_message = "Previous Haiku tasks:\n" + "\n".join(f"Task: {task['task']}\nResult: {task['result']}" for task in previous_junior_tasks)
    if continuation:
        prompt = continuation_prompt

    messages = [
        {
            "role": "system",
            "content": system_message
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        haiku_response = client.chat.completions.create(
            model=st.session_state['junior'],
            messages=messages,
            max_tokens=8000
        )
        response_text = haiku_response.choices[0].message.content
        junior.markdown(response_text)
        return response_text
    except Exception as e:                                      # e --> refers to the Error
        junior.markdown(f"Error calling Sub-agent: {e}")
        return ""
    
def refiner(objective: str, sub_task_results: list, filename: str, projectname: str, continuation: bool = False):           # Calls refiner to refine the sub-task results into a cohesive final output.
    """
    Calls refiner to refine the sub-task results into a cohesive final output.

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
    refiner.markdown("Calling refiner to provide the refined final output for your objective")
    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant that refines sub-task results into a cohesive final output."
        },
        {
            "role": "user",
            "content": (f"Objective: {objective}\n\nSub-task results:\n" + "\n".join(sub_task_results) + 
                        "\n\n review and refine the sub-task results into a cohesive final output. Add any missing information or details as needed. "
                        "Make sure the code files are completed. When working on code projects, ONLY AND ONLY IF THE PROJECT IS CLEARLY A CODING ONE please provide the following:\n"
                        "1. Project Name: Create a concise and appropriate project name that fits the project based on what it's creating. The project name should be no more than 20 characters long.\n"
                        "2. Folder Structure: Provide the folder structure as a valid JSON object, where each key represents a folder or file, and nested keys represent subfolders. Use null values for files. "
                        "Ensure the JSON is properly formatted without any syntax errors. make sure all keys are enclosed in double quotes, and ensure objects are correctly encapsulated with braces, "
                        "separating items with commas as necessary.\nWrap the JSON object in <folder_structure> tags.\n"
                        "3. Code Files: For each code file, include ONLY the file name in this format like this: 'Filename: <filename>' NEVER EVER USE THE FILE PATH OR ANY OTHER FORMATTING YOU ONLY USE THE FOLLOWING format "
                        "'Filename: <filename>' followed by the code block enclosed in triple backticks, with the language identifier after the opening backticks, like this:\n\n​python\n<code>\n​")
        }
    ]

    try:
        senior_response = client.chat.completions.create(
            model=st.session_state['refiner'],
            messages=messages,
            max_tokens=8000
        )
        response_text = senior_response.choices[0].message.content
        refiner.markdown(response_text)
        return response_text
    except Exception as e:
        refiner.markdown(f"Error calling Refiner: {e}")                # e --> refers to the Error
        return ""
        


def create_folder_structure(project_name: str, folder_structure: dict, code_blocks: list):         # Creates the folder structure and files based on the provided structure and code blocks.
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
        print(e)                    # e --> refers to the Error
        return



def create_folders_and_files(current_path: str, structure: dict, code_blocks: list):            # create folders and files based on the provided structure.
    """
    Recursively create folders and files based on the provided structure.           

    Args:
        current_path (str): The current path to create folders and files in.
        structure (dict): The folder structure as a dictionary.
        code_blocks (list): List of code blocks with filenames.
    """
    for key, value in structure.items():
        st.write(key)
        path = os.path.join(current_path, key)
        st.write(path)
        if isinstance(value, dict):
            try:
                os.makedirs(path, exist_ok=True)
                create_folders_and_files(path, value, code_blocks)
            except OSError as e:
                print(e)
        else:
            st.write("code_blocks")
            st.write(code_blocks)
            code_content = next((code for file, code in code_blocks if file == key), None)
            if code_content:
                try:
                    with open(path, 'w') as file:
                        file.write(code_content)
                    # console.print(Panel(f"Created file: [bold]{path}[/bold]", title="[bold green]File Creation[/bold green]", title_align="left", border_style="green"))
                except IOError as e:
                    print(e)
                    # console.print(Panel(f"Error creating file: [bold]{path}[/bold]\nError: {e}", title="[bold red]File Creation Error[/bold red]", title_align="left", border_style="red"))
            # else:
                # console.print(Panel(f"Code content not found for file: [bold]{key}[/bold]", title="[bold yellow]Missing Code Content[/bold yellow]", title_align="left", border_style="yellow"))


# "haiku" ---> refers to junior_sub_agent.
# "opus" ---> refers to senior_orchestrator.

def load(objective:str):                         # Get the objective from user input

    # Check if the input contains a file path               
    if "./" in objective or "/" in objective:
        file_path = re.findall(r'[./\w]+\.[\w]+', objective)[0]         # we use this if we used this project in cmd 
                                                                        # cause u can give the ai model the path of existing file in your pc has the description for the project u want to create
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
            opus_result, file_content_for_haiku = senior_orchestrator(objective, file_content, previous_results)
        else:
            opus_result, _ = senior_orchestrator(objective, previous_results=previous_results)

        if TASK_COMPLETE_PHRASE in opus_result:
            final_output = opus_result.replace(TASK_COMPLETE_PHRASE, "").strip()
            break
        else:
            sub_task_prompt = opus_result
            if file_content_for_haiku and not haiku_tasks:
                sub_task_prompt = f"{sub_task_prompt}\n\nFile content:\n{file_content_for_haiku}"
            sub_task_result = junior_sub_agent(sub_task_prompt, haiku_tasks)
            haiku_tasks.append({"task": sub_task_prompt, "result": sub_task_result})
            task_exchanges.append((sub_task_prompt, sub_task_result))
            file_content_for_haiku = None

    sanitized_objective = re.sub(r'\W+', '_', objective)                    # replace spaces with "_" in output file name
    timestamp = datetime.now().strftime("%H-%M-%S")                         # add the time in output file name
    refined_output = refiner(objective, [result for _, result in task_exchanges], timestamp, sanitized_objective)   #refine the final output

    project_name_match = re.search(r'Project Name: (.*)', refined_output)       # it matches the project name from the refined output.
    project_name = project_name_match.group(1).strip() if project_name_match else sanitized_objective

    folder_structure_match = re.search(r'<folder_structure>(.*?)</folder_structure>', refined_output, re.DOTALL)
    folder_structure = {}           #start with empty json object
    if folder_structure_match:
        json_string = folder_structure_match.group(1).strip()
        try:
            folder_structure = json.loads(json_string)          # convert string to json object
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError
            
    code_blocks = re.findall(r'Filename: (\S+)\s*```[\w]*\n(.*?)\n```', refined_output, re.DOTALL)
    create_folder_structure(project_name, folder_structure, code_blocks)
    create_download_link(project_name)

    max_length = 25
    truncated_objective = sanitized_objective[:max_length] if len(sanitized_objective) > max_length else sanitized_objective
    markdownfile = f"{timestamp}_{truncated_objective}.md"

    exchange_log = f"Objective: {objective}\n\n" + "=" * 40 + " Task Breakdown " + "=" * 40 + "\n\n"
    for i, (prompt, result) in enumerate(task_exchanges, start=1):
        exchange_log += f"Task {i}:\nPrompt: {prompt}\nResult: {result}\n\n"
    exchange_log += "=" * 40 + " Refined Final Output " + "=" * 40 + "\n\n" + refined_output


    with open(markdownfile, 'w') as file:
        file.write(exchange_log)
    print(f"\nFull exchange log saved to {markdownfile}")

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
    page_title="AI World",
    page_icon=":speach_ballon:"
)

models = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


with st.sidebar:
    st.subheader("Settings")
    
    st.write("Hello To AI World")


    st.selectbox("select a senior",models,key="senior")
    st.selectbox("select a junior",models,key="junior")
    st.selectbox("select a refiner",models,key="refiner")

user_query = st.chat_input("Type your prompt ....")

if user_query is not None and user_query.strip() != "":
    user = call_chat_bot("Human")
    user.markdown(user_query)
    load(user_query)
   

