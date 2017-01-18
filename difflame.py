#!/usr/bin/python

# tool to see who introduced changes on files
# Copyright Edmundo Carmona Antoranz 2017
# Released under the terms of GPLv2

# for starters, will get 2 parameters: two treeishs to compare
# For lines added, will use normal blame operation of the file
# For lines removed, will use reverse blame operation

import subprocess
import sys

def run_git_command(args):
    """
    Run a git command. If there is an error, will throw an exception. Otherwise, output will be returned
    """
    command = ["git"]
    command.extend(args)
    return subprocess.check_output(command)

def process_hunk_from_diff_output(output_lines, starting_line, original_name, final_name):
    """
    Process a diff hunk from a file
    A hunk starts with a line that starts with @ and describes the position of the block of code in original file and ending file
        (more datails to come)
    Then we have lines that start with:
        - ' ': Line didn't change
        - '+': Line was added
        - '-': Line was deleted
    Until we have a line that starts with a 'd' or a '@' (begining of new file or begining of new hunk)
    """
    i = starting_line
    hunk_description_line = output_lines[i]
    if len(hunk_description_line) == 0:
        # reached EOF, probably
        return i+1
    
    if not hunk_description_line[0] == '@':
        # not the begining of a hunk
        raise Exception("Not the begining of a hunk on line " + str(i + 1) + " (" + original_name + ", " + final_name + ")")
    
    # ok.... got a hunk
    print hunk_description_line
    
    hunk_description_info = hunk_description_line.split()
    original_file_info = hunk_description_info[1]
    final_file_info = hunk_description_info[2]
    
    hunk_lines = []
    # let's get the lines until we get to next hunk, next file or EOF
    i+=1
    while i < len(output_lines) and len(output_lines[i]) > 0 and output_lines[i][0] in [' ', '+', '-']:
        # a valid line in the hunk
        hunk_lines.append(output_lines[i])
        i+=1
    
    for line in hunk_lines:
        print line
    
    # got to one of the cases that makes hunk finish (EOF, end of file or end of hunk)
    return i

def process_file_from_diff_output(output_lines, starting_line):
    """
    process diff output for a line.
    Will return position of next file in diff outtput
    
    TODO support mode changes without changing content
    """
    # First is a 'diff' line
    i=starting_line
    diff_line = output_lines[i].split()
    if diff_line[0] != "diff":
        raise Exception("Doesn't seem to exist a 'diff' line at line " + str(i + 1) + ": " + output_lines[i])
    original_name = diff_line[1]
    final_name = diff_line[2]
    print output_lines[i]; i+=1
    
    # let's get to the line that starts with ---
    while i < len(output_lines) and not output_lines[i].startswith("---"):
        print output_lines[i]; i+=1
    
    if i >= len(output_lines):
        raise Exception("Couln't find line starting with --- for a file (" + original_name + ", " + final_name + ")")
    
    print output_lines[i]; i+=1 # line with ---
    
    # next should begin with +++
    if not output_lines[i].startswith("+++"):
        raise Exception("Was expecting line with +++ for a file (" + original_name + ", " + final_name + ")")
    
    print output_lines[i]; i+=1 # line with +++
    
    # Now we start going through the hunks until we find a diff
    while i < len(output_lines) and len(output_lines[i]) > 0 and output_lines[i][0] != 'd':
        # hunk starts with a @
        i = process_hunk_from_diff_output(output_lines, i, original_name, final_name)
    
    return i

def process_diff_output(output, treeish1, treeish2):
    """
    process diff output
    """
    
    # process files until output is finished
    lines=output.split("\n")
    i=0
    while i < len(lines):
        starting_line = lines[i]
        if len(starting_line) == 0:
            # got to the end of the diff output
            break
        i = process_file_from_diff_output(lines, i)

if len(sys.argv) < 3:
    # not enough parameters
    sys.stderr.write("Not enough parameters\n")
    sys.stderr.write("Need to provide at least 2 treeishs to work on\n")
    exit(1)

# got at least two parameters
# will probably have to go through all the parameters (when we have them) in order to parse them

# finally, will get the two branches where we will work on
treeish1=sys.argv[-2]
treeish2=sys.argv[-1]

diff_output = None
try:
    diff_output = run_git_command(["diff", treeish1 + ".." + treeish2])
except Exception as e:
    print "there was an error running git"
    print e
    sys.exit(1)

# processing diff output
process_diff_output(diff_output, treeish1, treeish2)
