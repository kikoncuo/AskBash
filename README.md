# ASKBASH

## What is ASKBASH?
AskBash is a script designed to simplify the process of using the terminal
It takes in requests from users written with natural language and converts them into bash commands

It works for multiple commands and can be used to automate tasks

![UsageExample](https://github.com/kikoncuo/AskBash/blob/main/images/Example.png)

It gets a bit of context of where it's running and who the user is, so it can do more complicated requests such as full complex git processes, or commands like scp, docker, tmux that tend to give me problems due to the amount of flags they have.

## How does it work?
It's a python script that uses chatGPT through langchain to generate responses to user input and subprocesses to run the bash commands.

It streams the response and can explain the commands it runs if you use the -v flag
IE: ``` python3 askbash.py REQUEST -v ```

![VerboseExample](https://github.com/kikoncuo/AskBash/blob/main/images/verboseExample.png)

It works best with smaller requests, but can handle more complex ones with multiples steps as well

![gitExample](https://github.com/kikoncuo/AskBash/blob/main/images/gitExample.png)

Or requests with multiple flags and parameters

![dockerExample](https://github.com/kikoncuo/AskBash/blob/main/images/dockerExample.png)


## How do I use it?
1. Clone the repository

``` git clone repo ```

2. Install the requirements

``` pip install -r requirements.txt ```

3. Set an env variable with your openai key, For example, in a Unix shell, run:

```export OPENAI_API_KEY=<your_api_key>```

You can get yours by creating a free dev account and creating a key at https://platform.openai.com/account/api-keys
You may want to make it permanent by adding it to your .bashrc or .zshrc, we can add that to the script in the future if people request it

4. Run the script

``` python3 askbash.py REQUEST ```

5. (Optional) Install a permanent alias so you don't need to type the whole command every time

We created a handy dandy way to do this for you

``` python3 askbash.py -i ```

## How do I contribute?
We're always looking for new ideas and ways to improve the script, just do a PR and we'll take a look at it.