.PHONY: run tunnel dev install

run:
	.venv/bin/python -m gcal_mcp_remote

tunnel:
	tailscale funnel 8001

dev:
	tmux new-session -d -s gcal 'make run' \; split-window -h 'make tunnel' \; attach

install:
	python -m venv .venv
	.venv/bin/pip install -e .
