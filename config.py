from pydantic import BaseModel, Field
from typing import List,Dict,Any,Literal
from langgraph.graph import StateGraph, MessagesState
# Define Pydantic models for data structures
class SetupFiles(BaseModel):
    readme : str = Field(description="The readme file of the repo")
    requirements : str = Field(description="The requirements file of the repo")

class container_setup(BaseModel):
    dockerfile : str = Field(description="The docker file content")
    dockerfile_status : bool = Field(description="The status of the dockerfile key in the json")
    commands : List[str] = Field(description="The commands to run the docker file and the repo")

# Define the state for the LangGraph
class State(MessagesState):
    github_repo_url : str
    imp_files: SetupFiles
    execution_commands: container_setup
    repo_structure: str

graph_config = {"recursion_limit": 100,"configurable": {"thread_id": "1"}}
