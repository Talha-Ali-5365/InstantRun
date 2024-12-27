from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List,Dict,Any,Literal
import nest_asyncio
from langchain_core.output_parsers import JsonOutputParser
import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
import subprocess

# Initialize the language model
llm = ChatOpenAI(
    model = 'hf:meta-llama/Llama-3.3-70B-Instruct',
    api_key = 'YOUR_API_KEY',
    base_url = 'https://glhf.chat/api/openai/v1'
)

# Define Pydantic models for data structures
class SetupFiles(BaseModel):
    readme : str = Field(description="The readme file of the repo")
    requirements : str = Field(description="The requirements file of the repo")

class container_setup(BaseModel):
    dockerfile : str = Field(description="The docker file content")
    dockerfile_status : bool = Field(description="The status of the dockerfile key in the json")
    commands : List[str] = Field(description="The commands to run the docker file and the repo")

# Define a JSON output parser for SetupFiles
folder_parser = JsonOutputParser(pydantic_object=SetupFiles)

# Define the state for the LangGraph
class State(MessagesState):
    github_repo_url : str
    imp_files: SetupFiles
    execution_commands: container_setup
    repo_structure: str

# Define the prompt for extracting file paths
format_dir = """
Output the directory content in following format:
{
    readme : path of readme if exist else empty strings like "" (eg: ./folder1/folder2/README.md)
    requirements : path of requirements if exist else empty strings like "" (eg: ./folder1/folder2/requirements.txt)
}

Remeber we are already in the repo folder so double check the path you generate. It should be accurate!!
OUTPUT SHOULD BE THE ABOVE JSON FORMAT ANY NOTHING ELSE NOT EVEN A SINGLE CHARACTER EXTRA, NO EXPLANATION , NOTHING ELSE JUST THE JSON FORMAT.
"""
  
# Node to clone the repository
def clone_repo(state: State):
    print('Cloning the repository!!!')
    print('+'*50)
    os.system(f"git clone {state['github_repo_url']}")
    os.chdir(state['github_repo_url'].split('/')[-1])
    print(f"Current directory = {os.getcwd()}")
    directory_content = os.popen(f"ls -R ./").read()
    messages = [HumanMessage(content=f"OUTPUT FROM CLONE_REPO NODE:\nCloned the repository. The directory structure of repo is: {directory_content}.")]
    output = llm.invoke(messages + [HumanMessage(content=format_dir)])
    parsed_output = folder_parser.parse(output.content)
    if parsed_output:
        print('+'*50)
        print('Repo cloned successfully!!!')
        print('+'*50)
    return {'messages': messages,'imp_files': parsed_output, 'repo_structure': directory_content}

# Prompt for extracting setup instructions from README
readme_prompt = """
Find the setup instructions in the readme file and output only the setup instructions part in a well formatted manner if setup instructions are present otherwise no if not present. 
Output should be setup instructions or no, and nothing else.
Remember to output the setup instructions only and not the entire readme file.
"""
# Node to get setup instructions from the README file
def get_readme(state: State):
    print('Finding setup instructions in readme file!!!')
    print('+'*50)
    readme_content = os.popen(f"cat {state['imp_files']['readme']}").read()
    messages = [HumanMessage(content=f"Readme content: {readme_content}"), HumanMessage(content=readme_prompt)]
    output = llm.invoke(messages)
    if "no" in output.content:
        print('Setup instructions not found!!!')
        print('+'*50)
        return {'messages': [HumanMessage(content='There is no setup instructions in the readme file')]}
    
    print('Setup instructions found!!!')
    print('+'*50)
    return {'messages': [HumanMessage(content=f'The setup instructions from README file of this repo are: {readme_content}')]}

# Conditional edge to check if README exists
def check_readme(state: State) -> Literal["get_readme", "plan"]:
    if state['imp_files']['readme']:
        return "get_readme"
    return "plan"

# Prompt for planning the setup
plan_prompt = """
## Task

Create a step-by-step plan to set up a GitHub repository on my Linux PC using Docker. The repository has already been cloned, and we are currently in that directory.

## Instructions

1. **Detailed Steps:** Provide a thorough plan, including every step needed to get the repository running.
2. **Docker Setup:**  Assume Docker, Docker Compose, and all related components are installed. The setup must be done entirely within a Docker container.
3. **Starting Point:** Begin your plan from the current state: the repository is cloned, and we have already changed the directory to repository's.
4. **Include All Essentials:** Your plan should list all necessary commands, code (like Dockerfiles), and any other actions required.
5. **Execution:** Remember, any command you include will be executed directly in the terminal.
6. **System:** The operating system is Arch Linux, So tailor you commands accordingly.

# Command Instructions
- **Avoid using `cd`:** We are already in the right directory after cloning the repository. So, avoid using `cd repository` in your plan.

# For Python Repositories
- **Python Version:** Use Python 3.10 or later.
- **Dependency installation:** Use only requirements.txt for dependency installation. Do not install any dependency directly using `pip install` and leave them if there is no requirements.txt.

## Output Format

Provide a detailed plan to set up the repository. This plan should include:

-   **Dockerfile:** If a Dockerfile is not present in the repository, provide the content for one. If it exists, leave this field empty (e.g., "").
-   **Commands:** A list of commands to build and run the Docker container.

**Strictly adhere to the following JSON format without any backticks:**

{
    "dockerfile": "Content of Dockerfile or empty string",
    "dockerfile_status": "True/False (false if dockerfile key content is empty else true)",
    "commands": ["List of commands"]
}

**DO NOT OUTPUT ANY SINGLE CHARACTER OUTSIDE OF THIS JSON STRUCTURE.**
**Sometimes paths may contains spaces like "folder 1" , alway wrap that kind of paths in double quotes and make sure to start and end with same backward slash and double qoute like \"./temp/folder 1\"**
***Note:*** *The docker run command should have a prefix "alacritty -e " cause this will open up a new window for user. DO THIS ONLY FOR RUNNING NOT BUILDING**
"""

# Define a JSON output parser for container setup
container_parser = JsonOutputParser(pydantic_object=container_setup)

# Node to create a setup plan
def plan(state: State):
    print('Planning to setup the repository!!!')
    print('+'*50)
    messages = [HumanMessage(content=plan_prompt)]
    output = llm.invoke(state['messages']+messages)
    parsed_output = container_parser.parse(output.content)
    if parsed_output:
        print('Plan created successfully!!!')
        print('+'*50)
    return {'messages': [output], 'execution_commands': parsed_output}
    
# Node to execute the commands
def execute_commands(state: State):
    print('Executing the commands!!!')
    print(f'Following commands are being executed:\n {state["execution_commands"]["commands"]}')
    print('+'*50)
    # Create Dockerfile if needed
    if state['execution_commands']['dockerfile_status']:
        with open("Dockerfile", "w") as f:
            f.write(state['execution_commands']['dockerfile'])
    # Execute commands and capture output
    combined_output = ""
    for command in state['execution_commands']['commands']:
        combined_output += f"\n#Output of command: **{command}:**\n"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        combined_output += stdout.decode()
        combined_output += stderr.decode()
        combined_output += "\n\n"
    print('Commands executed successfully!!!')
    return {'messages': [HumanMessage(content=combined_output)]}

# Conditional edge to check for errors
def check_errors(state: State) -> Literal["fix_errors", END]:
    message = state['messages'][-1]
    print('+'*50)
    output = llm.invoke([message,HumanMessage(content="Above message is the output of the commands execution. if there is any error just output yes else no. The output should be yes or no and nothing else.")])
    if "yes" in output.content:
        print('!'*50)
        print("Error detected!!!")
        print('!'*50)
        return "fix_errors"
    
    print('No error detected!!!')
    print('+'*50)
    print('Setup completed successfully!!!')
    print('+'*50)
    print(f'Final output = {state["messages"][-1]}')
    return END

# Output schema for error fixing
output_schema = """
## Output Format

Provide a detailed plan to set up the repository. This plan should include:

-   **Dockerfile:** If a Dockerfile is not present in the repository, provide the content for one. If it exists, leave this field empty (e.g., "").
-   **Commands:** A list of commands to build and run the Docker container.

**Strictly adhere to the following JSON format without any backticks:**

{
    "dockerfile": "Content of Dockerfile or empty string",
    "dockerfile_status": "True/False (false if dockerfile key content is empty else true)",
    "commands": ["List of commands"]
}

**DO NOT OUTPUT ANY SINGLE CHARACTER OUTSIDE OF THIS JSON STRUCTURE.**
**Sometimes paths may contains spaces like "folder 1" , alway wrap that kind of paths in double quotes and make sure to start and end with same backward slash and double qoute like \"./temp/folder 1\"**
***Note:*** *The docker run command should have a prefix "alacritty -e " cause this will open up a new window for user. DO THIS ONLY FOR RUNNING NOT BUILDING**
"""
# Node to fix errors
def fix_errors(state: State):
    print('Fixing the errors!!!')
    print('+'*50)
    output = llm.invoke(state['messages']+[HumanMessage(content=f"There is an error after execution of commands as you can see in the last previous message. Fix the error and rewrite docker file and commands.\n\n {output_schema}")])
    parsed_output = container_parser.parse(output.content)
    return {'messages': [HumanMessage(content="Fix the error"),output], 'execution_commands': parsed_output}

# Define the LangGraph workflow
workflow = StateGraph(State)
workflow.add_node('clone_repo', clone_repo)
workflow.add_node('get_readme', get_readme)
workflow.add_node('plan', plan)
workflow.add_node('execute_commands', execute_commands)
workflow.add_node('fix_errors', fix_errors)
workflow.add_edge(START,'clone_repo')
workflow.add_conditional_edges(
    "clone_repo",
    check_readme
)
workflow.add_edge('get_readme', 'plan')
workflow.add_edge('plan', 'execute_commands')
workflow.add_conditional_edges(
    'execute_commands',
    check_errors
)
workflow.add_edge('fix_errors', 'execute_commands')
workflow.set_entry_point('clone_repo')
graph = workflow.compile(checkpointer=MemorySaver())
# image = Image(graph.get_graph(xray=True).draw_mermaid_png())
# with open("graph.png", "wb") as f:
#     f.write(image.data)
# display(image)

# System prompt for the agent
system_prompt = """
You are a helpful AI ASSISTANT inside a complex Agentic graph that can setup any github online repository on user's PC.
If an Output schema is defined by the user then do not output any single character other than that schema
"""

config = {"recursion_limit": 100,"configurable": {"thread_id": "2"}}
# https://github.com/deviant101/Find-GitHub-Repos-StarLang
# https://github.com/GeorgeZhukov/python-snake
if os.path.exists("python-snake"):
    os.system("rm -r python-snake")
messages = [SystemMessage(content=system_prompt)]
output = graph.invoke({'messages': messages,'github_repo_url': 'https://github.com/GeorgeZhukov/python-snake'},config)
for m in output['messages'][-1:]:
    m.pretty_print()