from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import Literal
import nest_asyncio
from langchain_core.output_parsers import JsonOutputParser
import os
from langchain_core.messages import HumanMessage
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
import subprocess
import pprint
from constants import plan_prompt, output_schema, format_dir, readme_prompt
from config import SetupFiles, container_setup, State
# For github
# Initialize the language model
llm = ChatOpenAI(
    model = 'gpt-4o-mini',
    api_key = 'YOUR_API_KEY',
)

# Define a JSON output parser for SetupFiles
folder_parser = JsonOutputParser(pydantic_object=SetupFiles)
  
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
    print(f'Following commands are being executed:\n')
    pprint.pprint(f"{state['execution_commands']['commands']}")
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
        print(f'Error: \n {message.content}')
        print('!'*50)
        return "fix_errors"
    
    print('No error detected!!!')
    print('+'*50)
    print('Setup completed successfully!!!')
    print('+'*50)
    print(f'Final output = {state["messages"][-1]}')
    return END


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



#uncomment the following lines to generate the png of flow graph
########################################################################################
# image = Image(graph.get_graph(xray=True).draw_mermaid_png())
# with open("graph.png", "wb") as f:
#     f.write(image.data)
# display(image)
