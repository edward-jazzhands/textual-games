
# This will run the tmux script.
# see tmux.sh for more details.
tmux:
	chmod +x tmux.sh
	./tmux.sh

console:
	uv run textual console -x EVENT -x SYSTEM -x WORKER

run-dev:
	uv run textual run --dev textual_games:TextualGames

run:
	uv run textual run textual_games:TextualGames