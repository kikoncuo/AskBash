import os
import sys
import re
import subprocess
import signal
import glob
import shlex
import json
from dotenv import load_dotenv
from prompt_toolkit import PromptSession

from langchain.chat_models import ChatOpenAI

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)
from langchain import LLMChain
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

######################################## Global variables and initial setup ########################################

# Verbose flag
verboseFlag = True
# Params string
params = ''

# Create a prompt session for the interactive terminal
session = PromptSession()

# Load environment variables from .env file
load_dotenv()

# Get username and hostname they are used for context and given to the promt template
username = os.getenv('USER')
useMemory = os.getenv('ASKBASH_MEMORY').lower() == "true"
hostname = os.uname().nodename


######################################## Helper functions ########################################

# Functions to handle message history used for context, there are defo better ways to do it, but this is the easiest for now
def save_message_to_history(sender, message, file_path='history.json'):
    # Load existing messages from the JSON file
    try:
        with open(file_path, 'r') as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

    # Append the new message to the list
    messages.append({
        'sender': sender,
        'message': message
    })

    # Save the updated messages back to the JSON file
    with open(file_path, 'w') as f:
        json.dump(messages, f)

def clear_history(file_path='history.json'):
    with open(file_path, 'w') as f:
        json.dump([], f)


def load_history(file_path='history.json'):
    try:
        with open(file_path, 'r') as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

    return messages

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
    
def join_strings_with_quotes(my_array):
    result = []
    for item in my_array:
        if " " in item:
            result.append(f'"{item}"')
        else:
            result.append(item)
    return " ".join(result)
    
def stream_command_output(command):
    if command=='':
        print('\033[94m' + "Skipping this command")
        return
    index = command.find('#')
    if index != -1:
        command = command[:index]
    my_array = shlex.split(command)
    # We need to handle cd separetely, this executres the command in the current shell since subprocess.Popen(), it runs in a new subprocess, so any changes to the environment, like the current directory, are only applied within that subprocess and do not affect the parent process 
    if my_array[0] == 'cd':
        try:
            os.chdir(my_array[1])
            print(f"Changed directory to {my_array[1]}")
            return 0
        except Exception as e:
            print('\033[93m' + "Error: Command failed unexpectedly")
            print(e.args[1])
            return e.args[0]
    # We need to handle the * wildcard and delete files created in the command itself from it
    if '*' in my_array:
        index = my_array.index('*')
        my_array = my_array[:index] + glob.glob('*') + my_array[index + 1:]

    command_str =join_strings_with_quotes(my_array)


    try:
        process = subprocess.Popen(command_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    except Exception as e:
        print('\033[93m' + "Error: Command failed unexpectedly")
        print('\033[93m' + e.args[1] + '\033[0m')
        return e.args[0]
        
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
        print('\033[93m' + remaining_errors.strip() + '\033[0m')

    return process.returncode

def signal_handler(sig, frame):
    print('\033[93m' + 'You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def orderCommands(commands_list):
    try:
        for command in command_list:
            edited_text = session.prompt(message="> ", default=command)
            print(edited_text)
            output = stream_command_output(edited_text)
            if(output != 0 and output != None):
                print('\033[93m' + "\n Seems like that command failed, you can edit it and try again, skip it by deleting the command, or cancel the execution with Ctrl+C" + '\033[0m')
                print('\033[93m' + "Command output code:" + str(output) + '\033[0m')
                orderCommands(commands_list)
                return
    except KeyboardInterrupt:
        print('\033[93m' + 'Cancelled execution...')
        sys.exit(0)


######################################## Context prep ########################################

# Prompt template
SystemMessageContent = """If someone asks you to perform a task, your job is to come up with a series of bash commands that will perform the task. 
There is no need to put "#!/bin/bash" in your answer.
You can use the context of the previous messages to help you come up with the commands.
Make sure to reason step by step

Here is an example:

User message: "copy the files in the directory named 'target' into a new directory at the same level as target called 'myNewDirectory'"
Your response: "
I need to take the following actions:
- List all files in the directory
- Create a new directory
- Copy the files from the first directory into the second directory
```bash
ls
mkdir myNewDirectory
cp -r target/* myNewDirectory
```

Here is a second example:
User message: "Delete the directory you just created"
Your response: "
I need to take the following actions:
- Delete the directory myNewDirectory and all its contents
```bash
rm -r myNewDirectory
```

your username is usernameREPLACE and your hostname is hostnameREPLACE
"""

SystemMessageContent = replace_string(SystemMessageContent, username, 'usernameREPLACE')
SystemMessageContent = replace_string(SystemMessageContent, hostname, 'hostnameREPLACE')

######################################## Input processing and checks ########################################


# Check if OPENAI_API_KEY environment variable is set
if 'OPENAI_API_KEY' not in os.environ:
    print('\033[93m' + "Error: The OPENAI_API_KEY environment variable is not set.")
    print("Please set the variable to your OpenAI API key before running the script.")
    print("For example, in a Unix shell, run:")
    print("export OPENAI_API_KEY=<your_api_key>")
    sys.exit(1)

# Check if -h flag is passed
if '-h' in sys.argv:
    print('\033[94m' + "This script takes questions about how to perform a task in bash and returns a series of bash commands that will perform the task.")
    print("Usage: python askbash.py [question] [options]")
    print("Options:")
    print("  -h  Show this help message and exit")
    print("  -s  Silent mode")
    print("  -f  flushes the memory of your conversation, it's recommended you use this option often if your variable USE_HISTORY is set to True in .env to reduce costs or if you hit the token limit")
    print("  -i  Install alias and OPENAI_API_KEY as persistent variables so you can run it from anywhere"+ '\033[0m')
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
        print('\033[93m' + "No python3 found in your system, trying python instead python")
        try:
            result = subprocess.run(['which', 'python'], capture_output=True, text=True, check=True)
            pythonInterpreter = 'python'
        except subprocess.CalledProcessError:
            print('\033[93m' + "Error: no python interpreter found, this is weird since you are running a python script, your alias is likley different, try to go to the script. look for this line and change the f.write below to the correct python interpreter path.")
            sys.exit(1)

    message = '\033[94m' + f"You used the -i flag, this will install the following alias for you:\nalias {alias_name}='{pythonInterpreter} {script_path}'\nin your ~/.bashrc file.\nThis means you will be able to use {alias_name} from anywhere by typing askbash followed by your question\nPress enter to confirm..."+ '\033[0m'

    edited_text = session.prompt(message="> ", default=message)

    with open(bashrc_path, 'a') as f:
        f.write(f"\nalias {alias_name}='{pythonInterpreter} {script_path}'\n")

    print('\033[94m' + "Alias created '{alias_name}' for script '{script_name}'... remember restarting your terminal to use the alias or refresh it with `source ~/.bashrc`."+ '\033[0m')
    sys.exit(0)

# Check if -f flag is passed
if '-f' in sys.argv:
    message = f"You used the -f flag, this will flush any memory of the chat, this is good and required to reduce costs if your variable USE_HISTORY is set to True in .env to reduce costs or if you hit the token limit.\nHit enter to continue..."
    edited_text = session.prompt(message="> ", default=message)
    clear_history()
    print('\033[94m' + "Memory flushed..."+ '\033[0m')
    sys.exit(1)
# Check if -s flag is passed
if '-s' in sys.argv:
    if sys.argv.index('-s') != len(sys.argv) - 1:
        print('\033[93m' + "Error: The -s flag must be the last command-line argument.")
        print("Usage: python askbash.py [arguments] -s")
        sys.exit(1)
    print('\033[94m' + "Silent mode enabled, commands won't be explained."+ '\033[0m')
    params = ' '.join(sys.argv[1:-1])
    verboseFlag = False
else:
    params = ' '.join(sys.argv[1:])
    

if params == '':
    print('\033[93m' + "Error: No instructions were passed to the askbash.")
    print('\033[94m' + "Usage: python askbash.py [arguments] [flags], use python askbash.py -h for help."+ '\033[0m')
    sys.exit(1)


######################################## Model config and execution ########################################


# Create a chat model
chat = ChatOpenAI(streaming=True, callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]), verbose=verboseFlag, temperature=0)
system_message_prompt = SystemMessagePromptTemplate.from_template(SystemMessageContent)
human_template="{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
chatHistory = [system_message_prompt]
if useMemory:
    chat_memories = load_history()
    if(len(chat_memories) != 0):
        print('\033[94m' +"Loading chat history of " + str(len(chat_memories)) + " messages, remember to use the -f flag to flush the memory if you want to delete them."+ '\033[0m')
        for memory in chat_memories:
            if (memory['sender'] == "user"):
                chatHistory.append(HumanMessagePromptTemplate.from_template(memory['message']))
            elif(memory['sender'] == "ai"):
                chatHistory.append(AIMessagePromptTemplate.from_template(memory['message']))
            else:
                print("Error: unknown format in history.json")
chatHistory.append(human_message_prompt)
chat_prompt = ChatPromptTemplate.from_messages(chatHistory)
chain = LLMChain(llm=chat, prompt=chat_prompt)
print('\033[95m')
commandResult = chain.run(params)
print('\033[0m')
save_message_to_history("user",params)
save_message_to_history("ai",commandResult)

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
        print('\033[94m' +"The following commands will be executed:")
        print(concatenated_commands)

    print('\033[94m' +"\n Hit enter to run the commands or edit them, If there are multiple command they will be shown and executed one by one."+ '\033[0m')
    orderCommands(command_list)
    




