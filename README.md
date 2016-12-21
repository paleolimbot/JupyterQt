
# JupyterQt: Easy Data Science in Python

For years I've struggled with the question of what to tell people when they say "I want to learn Python for data analytics...where do I start!?". R has the advantage of RStudio as a well thought-out, project-based IDE. There are many Python IDEs available, the most user-friendly of which is the Jupyter Notebook. Unless I'm very much mistaken, the current workflow behind a Jupyter Notebook goes like this:

1. Open a terminal and run `jupyter-notebook` in the project's working directory
2. Open a web browser
3. Write Python code
4. Close web browser
5. Press Control-C twice to kill the notebook server.

This is no problem for me or for Python developers, but to the average university student, the prospect of opening up a terminal is more than they are willing to do. As a result, they often use R and RStudio, even when superior tools exist in Python. The philosophy behind JupyterQt is to provide an RStudio-like project environment that keeps the Jupyter server away from the user. Thus, the workflow can be simplified:

1. Open JupyterQt
2. Write Python Code
3. Close JupyterQt

It's currently a work in progress, but if you have Python3 and PyQt5 installed, feel free to clone and give it a shot! Collaborators are welcome.