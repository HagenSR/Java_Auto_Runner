# Java auto runner

## Why

This script was made to help facilitate the grading of 161 projects. The professor had students turn in zips of java source code along with a word doc containing the source code. This project unzips the source code, compiles it, runs it and stores it's output in a file. Running the code is faster and more foolproof way of determining if the code is correct. Additionally, the source code can be viewed in VS Code with language support which helps highlight errors in contrast with reading code from a word doc. 

## How to use

Because this script involves arbitrarily executing code student's give you, it is advisable to run this script in a virtual machine. 

1. Put all zips in a folder called 'zips' in the same directory as the script. Other files can exist in this folder however only zips will be compiled. Note that you can bulk download student submissions from the full grade center on blackboard.
2. Optionally provide input in the 'input.in' file. The projects will receive this as standard input.
3. Optionally change the timeout duration in the script on line 125. The duration is in seconds.
4. run the command `python run_zips.py`
5. After the script has completed running, output for each project can be found in the 'out' folder
    - If the project failed to build or run, try running it in the IDE to ensure it really is a faulty project
6. Source code can be viewed in the build folder

## Features

- Project's that run beyond a set timeout duration will be killed
- All output including standard error is written to the output file
- Project's with varying client class names and packages will be run correctly
- Ability to provide input to the project being run
- Runs projects in their working directory

## Doesn't currently support

- Build tools (Maven, Gradel)
    - Ant projects typically work when compiled with just the Java command
- Packages
