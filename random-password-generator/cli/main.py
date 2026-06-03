"""
CLI entry point — delegates to the existing validator / rules logic.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validator import validator


def main():
    v = validator()
    password = v.validate_user_input()
    print(f"\nYour generated password: {password}\n")


if __name__ == "__main__":
    main()