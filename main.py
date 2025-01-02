import os
from instantrun import graph
from langchain_core.messages import SystemMessage
from config import graph_config
from constants import system_prompt

# https://github.com/deviant101/Find-GitHub-Repos-StarLang
# https://github.com/GeorgeZhukov/python-snake
if os.path.exists("python-snake"):
    os.system("rm -r python-snake")
messages = [SystemMessage(content=system_prompt)]
output = graph.invoke({'messages': messages,'github_repo_url': 'https://github.com/GeorgeZhukov/python-snake'},graph_config)
for m in output['messages'][-1:]:
    m.pretty_print()