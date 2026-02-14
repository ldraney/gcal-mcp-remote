.PHONY: run tunnel dev install

run:
	.venv/bin/python server.py

tunnel:
	tailscale funnel 8001

dev:
	tmux new-session -d -s gcal 'make run' \; split-window -h 'make tunnel' \; attach

install:
	python -m venv .venv
	.venv/bin/pip install -e ../calendar-mcp
	.venv/bin/pip install cryptography python-dotenv httpx
