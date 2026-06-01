import random
import string

def generate_password(length: int = 8, include_digits: bool = True, include_special_chars: bool = True, include_letters: bool = True, include_lowercase: bool = True, include_uppercase: bool = True) -> str:
    passwd_list = []
    if include_digits:
        passwd_list.extend(string.digits)
    if include_special_chars:
        passwd_list.extend(string.punctuation)
    if include_letters:
        if include_lowercase:
            passwd_list.extend(string.ascii_lowercase)
        if include_uppercase:
            passwd_list.extend(string.ascii_uppercase)

    return ''.join(random.choice(passwd_list) for _ in range(length))