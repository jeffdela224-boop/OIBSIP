"""
Entry point — launches the GUI by default.
Pass --cli to use the command-line interface instead.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if "--cli" in sys.argv:
    from cli.main import main
else:
    from gui.app import main

main()