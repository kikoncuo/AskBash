import os
import sys
import re
import subprocess
import signal
import glob
import shlex
from prompt_toolkit import PromptSession

from langchain.chat_models import ChatOpenAI

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain import LLMChain
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

######################################## Global variables ########################################

# Verbose flag
verboseFlag = False
# Params string
params = ''

# Create a prompt session for the interactive terminal
session = PromptSession()

# Get username and hostname they are used for context and given to the promt template
username = os.getenv('USER')
hostname = os.uname().nodename


######################################## Helper functions ########################################

# Function to replace a substring in a string
def replace_string(source_str, replace_str, word):
    # Find the index of the specified word in the source string
    index = source_str.find(word)
    if index == -1:
        # Word not found in source string
        return source_str
    else:
        # Replace the substring at the specified index with the replace string
        return source_str[:index] + replace_str + source_str[index+len(word):]

def find_bash_substring(s):
    pattern = r'```(.*?)```'
    match = re.search(pattern, s, re.DOTALL)
    
    if match:
        return match.group(1)
    else:
        return False
    
def stream_command_output(command):
    if command=='':
        print("Skipping this command")
        return
    my_array = shlex.split(command)
    if '*' in my_array:
        index = my_array.index('*')
        my_array = my_array[:index] + glob.glob('*') + my_array[index+1:]
    process = subprocess.Popen(my_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    # Collect any remaining output
    remaining_output, remaining_errors = process.communicate()

    if remaining_output:
        print(remaining_output.strip())

    if remaining_errors:
        print(remaining_errors.strip())

    return process.returncode

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


######################################## Context prep ########################################

# Prompt template
SystemMessageContent = """If someone asks you to perform a task, your job is to come up with a series of bash commands that will perform the task. There is no need to put "#!/bin/bash" in your answer. Make sure to reason step by step, here is an example:
User message: "copy the files in the directory named 'target' into a new directory at the same level as target called 'myNewDirectory'"
AI message: "
I need to take the following actions:
- List all files in the directory
- Create a new directory
- Copy the files from the first directory into the second directory
```bash
ls
mkdir myNewDirectory
cp -r target/* myNewDirectory
```

your username is usernameREPLACE and your hostname is hostnameREPLACE

Your response must follow the structure defined in AI message"""

SystemMessageContent = replace_string(SystemMessageContent, username, 'usernameREPLACE')
SystemMessageContent = replace_string(SystemMessageContent, hostname, 'hostnameREPLACE')

######################################## Input processing and checks ########################################


# Check if OPENAI_API_KEY environment variable is set
if 'OPENAI_API_KEY' not in os.environ:
    print("Error: The OPENAI_API_KEY environment variable is not set.")
    print("Please set the variable to your OpenAI API key before running the script.")
    print("For example, in a Unix shell, run:")
    print("export OPENAI_API_KEY=<your_api_key>")
    sys.exit(1)

# Check if -h flag is passed
if '-h' in sys.argv:
    print("This script takes questions about how to perform a task in bash and returns a series of bash commands that will perform the task.")
    print("Usage: python askbash.py [question] [options]")
    print("Options:")
    print("  -h  Show this help message and exit")
    print("  -v  Verbose mode")
    print("  -i  Install alias")
    sys.exit(0)

# Check if -i flag is passed
if '-i' in sys.argv:
    script_name = 'askbash.py'
    alias_name = 'askbash'


    script_path = os.path.abspath(os.path.join(os.getcwd(), script_name))
    bashrc_path = os.path.expanduser('~/.bashrc')

    pythonInterpreter = ''

    try:
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True, check=True)
        pythonInterpreter = 'python3'
    except subprocess.CalledProcessError:
        print("No python3 found in your system, trying python instead python")
        try:
            result = subprocess.run(['which', 'python'], capture_output=True, text=True, check=True)
            pythonInterpreter = 'python'
        except subprocess.CalledProcessError:
            print("Error: no python interpreter found, this is weird since you are running a python script, your alias is likley different, try to go to the script. look for this line and change the f.write below to the correct python interpreter path.")
            sys.exit(1)

    message = f"You used the -i flag, this will install the following alias for you:\nalias {alias_name}='{pythonInterpreter} {script_path}'\nin your ~/.bashrc file.\nThis means you will be able to use {alias_name} from anywhere by typing askbash followed by your question\nPress enter to confirm..."

    edited_text = session.prompt(message="> ", default=message)

    with open(bashrc_path, 'a') as f:
        f.write(f"\nalias {alias_name}='{pythonInterpreter} {script_path}'\n")

    print(f"Alias created '{alias_name}' for script '{script_name}'... remember restarting your terminal to use the alias or refresh it with `source ~/.bashrc`.")
    sys.exit(0)

# Check if -v flag is passed
if '-v' in sys.argv:
    if sys.argv.index('-v') != len(sys.argv) - 1:
        print("Error: The -v flag must be the last command-line argument.")
        print("Usage: python script.py [arguments] -v")
        sys.exit(1)
    print("Verbose mode enabled, more complicated commands or flows will be explained.")
    params = ' '.join(sys.argv[1:-1])
    verboseFlag = True
else:
    params = ' '.join(sys.argv[1:])

if params == '':
    print("Error: No instructions were passed to the script.")
    print("Usage: python script.py [arguments] -v")
    sys.exit(1)


######################################## Model config and execution ########################################


# Create a chat model
chat = ChatOpenAI(streaming=True, callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]), verbose=verboseFlag, temperature=0)
system_message_prompt = SystemMessagePromptTemplate.from_template(SystemMessageContent)
human_template="{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
chain = LLMChain(llm=chat, prompt=chat_prompt)


commandResult = chain.run(params)

######################################## Response parsing and output treatment ########################################


bashLookup = find_bash_substring(commandResult)

if bashLookup==False:
    print("No bash commands were found in the response, there is nothing to execute.")
else:
    command_list = bashLookup.split("\n")

    # Remove comments
    for item in command_list:
        if item.startswith("#"):
            command_list.remove(item)

    # Remove the first and last substrings
    command_list = [s for s in command_list[1:-1]]

    concatenated_commands = "\n".join(command_list)

    if verboseFlag == False:
        print("The following commands will be executed:")
        print(concatenated_commands)

    print("\n Hit enter to run the commands or edit them, If there are multiple command they will be shown and executed one by one.")
    try:
        for command in command_list:
            edited_text = session.prompt(message="> ", default=command)
            print(edited_text)
            output = stream_command_output(edited_text)
    except IndexError:
        print("")
    except KeyboardInterrupt:
        print('Cancelled execution...')
        sys.exit(0)



