# System prompt for the agent
system_prompt = """
You are a helpful AI ASSISTANT inside a complex Agentic graph that can setup any github online repository on user's PC.
If an Output schema is defined by the user then do not output any single character other than that schema
"""

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

# Prompt for extracting setup instructions from README
readme_prompt = """
Find the setup instructions in the readme file and output only the setup instructions part in a well formatted manner if setup instructions are present otherwise no if not present. 
Output should be setup instructions or no, and nothing else.
Remember to output the setup instructions only and not the entire readme file.
"""

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
**Repositories that are terminal based make sure to use docker -it for interactive mode.**
***Note:*** *The docker run command should have a prefix "alacritty -e " cause this will open up a new window for user. DO THIS ONLY FOR RUNNING NOT BUILDING**
"""

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
**Repositories that are terminal based make sure to use docker -it for interactive mode.**
***Note:*** *The docker run command should have a prefix "alacritty -e " cause this will open up a new window for user. DO THIS ONLY FOR RUNNING NOT BUILDING**
"""