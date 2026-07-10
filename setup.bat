@echo off
echo [llmwiki] Setting up...
python -m pip install -e . 2>nul || python3 -m pip install -e .
echo [llmwiki] Setup complete. Run: llmwiki init --source PATH
