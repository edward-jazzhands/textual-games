#!/bin/bash

# Use `just tmux` to set permissions and run this script.

# This script is designed for a terminal that is maximized on a wide screen.
# It will, with a single command:
# - starts a new tmux session
# - splits the window horizontally (left and right panes)
# - adjusts the width of the panes to be roughly 2/3 and 1/3 of the screen
# - runs the textual dev console on the right(small) side
# - runs the textual app on the left(large) side
# - finally it focuses on the left pane and attaches to the session

# Start a new tmux session named "textual_games"
tmux new-session -d -s textual_games     # -d is for detached mode, -s is for session name 'textual_games'

# Rename the first window and split horizontally
tmux rename-window -t textual_games:0 'Main'
tmux split-window -h     # -h splits the window horizontally

tmux resize-pane -t textual_games:0.1 -x 17   # puts it roughly 1/3 of screen

tmux send-keys -t textual_games:0.1 'just console' C-m
sleep 2           # give dev console a second or two to start
tmux send-keys -t textual_games:0.0 'just run-dev' C-m

# Select left pane and attach to the session
tmux select-pane -t textual_games:0.0
tmux attach-session -t textual_games
