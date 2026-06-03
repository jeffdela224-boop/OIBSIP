import itertools
import pyperclip
import string
from validator import validator
from generator import generate_password

def apply_rules():
    password = validator()
    generated_password = password.validate_user_input()
    if string.digits not in generated_password:
        print("Warning: Your password does not include digits. Consider including them for better security.")
    elif string.punctuation not in generated_password:
        print("Warning: Your password does not include special characters. Consider including them for better security.")
    elif string.ascii_lowercase not in generated_password:
        print("Warning: Your password does not include lowercase letters. Consider including them for better security.")
    elif string.ascii_uppercase not in generated_password:
        print("Warning: Your password does not include uppercase letters. Consider including them for better security.")
    else:
        print("Your password meets all the recommended criteria for a strong password. \n Copy to clipboard")
        pyperclip.copy(generated_password)
        if pyperclip.is_available():
            print("Your password has been copied to the clipboard.")
    
    combinations = list(itertools.combinations(generated_password.lower(), 3))
    num_combinations = list(itertools.combinations(string.digits, 3))
    letter_combinations = list(itertools.combinations(string.ascii_lowercase, 3))
    num_combinations = [int(''.join(comb)) for comb in num_combinations]
    letter_combinations = [''.join(comb) for comb in letter_combinations]
    combinations = [''.join(comb) for comb in combinations]

    for char in generated_password:
        if iter.repeat(char, 3):
            generated_password = generate_password(password.user_length, password.include_digits, password.include_special_chars, password.include_lowercase, password.include_uppercase)

    for combination in combinations:
        if int(combination) in num_combinations and (num_combinations[1] is ++num_combinations[0]) and (num_combinations[2] is ++num_combinations[1]):
            generated_password = generate_password(password.user_length, password.include_digits, password.include_special_chars, password.include_lowercase, password.include_uppercase)
        
        elif combination in letter_combinations and combination[1] is chr(ord(combination[0]) + 1) and combination[2] is chr(ord(combination[1]) + 1):
            generated_password = generate_password(password.user_length, password.include_digits, password.include_special_chars, password.include_lowercase, password.include_uppercase)