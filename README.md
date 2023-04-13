# 🚀 ASKBASH 🚀

## 📚 Index
1. [What is ASKBASH?](#what-is-askbash)
2. [How does it work?](#how-does-it-work)
3. [How do I use it?](#how-do-i-use-it)
4. [How do I contribute?](#how-do-i-contribute)
5. [Dedicated to](#dedicated-to)

## ❓ What is ASKBASH?
AskBash is a script designed to simplify the process of using the terminal 🖥️. It takes in requests from users written with natural language 📝 and converts them into bash commands 💻.

It works for multiple commands, can be used to automate tasks ⚙️ and can also be run with memory enabled to remember previous commands and use them in future requests 🧠 or to provide feedback context and correct it.

![UsageExample](https://github.com/kikoncuo/AskBash/blob/main/images/MemoryExample.gif)

It gets a bit of context by default of where it's running and who the user is, so it can do more complicated requests such as full complex git processes, or commands like scp, docker, tmux that tend to give me problems due to the amount of flags they have.
In the future I'll add a way for users to easily define what contenxt they want to provide to the model 🤔.

## 🤔 How does it work?
It's a python script 🐍 that uses chatGPT through langchain to generate responses to user input and subprocesses to run the bash commands.

It streams the response and explains the commands, it can be run in silent mode with the -s flag 🔇. IE: ``` python3 askbash.py REQUEST FLAGS ```

Use the -h flag to see all the available flags 🚩 and learn how to install it, use memory and flush.

It works best with smaller requests, but can handle more complex ones with multiples steps as well 📈.

![gitExample](https://github.com/kikoncuo/AskBash/blob/main/images/gitExample.gif)

Or requests with multiple flags and parameters 🚩.

![dockerExample](https://github.com/kikoncuo/AskBash/blob/main/images/dockerExample.png)

## 👨‍💻 How do I use it?
1. Clone the repository 📦

``` git clone https://github.com/kikoncuo/AskBash.git ```

2. Install the requirements 🛠️

``` pip install -r requirements.txt ```

3. Write your openai key in the .env file or set an env variable with your openai key 🔑. For example, in a Unix shell, run:

```export OPENAI_API_KEY=<your_api_key>```

You can get yours by creating a free dev account and creating a key at https://platform.openai.com/account/api-keys

4. Run the script 🏃‍♂️

``` python3 askbash.py REQUEST ```

5. (Optional) Install a permanent alias so you don't need to type the whole command every time 🚀

We created a handy dandy way to do this for you 🧰

``` python3 askbash.py -i ```

5. (Optional) Enable the memory feature but beware of the higher costs if you don't flush often 💰 ($0.0004 per request vs $0.008 absolutetly worst case with memory enabled)

Go to the .env file and set the ASKBASH_MEMORY variable to true.


## 🤝 How do I contribute?
Always looking for new ideas and ways to improve the script, just do a PR and we'll take a look at it 👀. 

The biggest missing thing right now is the command result context, the model doesn't see the result of the comand so it misses some context when you have history enabled. We're working on it, but if you have any ideas on how to solve this, please let us know 🤗.

## 💖 Dedicated to
P.