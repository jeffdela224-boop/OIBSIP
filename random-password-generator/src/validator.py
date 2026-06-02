from generator import generate_password


    
class validator:
    def __init__(self):
        self.user_length = None
        self.include_digits = None
        self.include_special_chars = None
        self.include_lowercase = None
        self.include_uppercase = None
    
    def validate_user_input(self):
        print("Welcome to the Random Password Generator!")
        print("Please select the options for your password:")
        print("1. Go with default settings - Recommended (8 characters, includes digits, special characters, letters, lowercase and uppercase)")
        print("2. Customize your password settings")

        choice = input("Enter your choice (1 or 2): ")
        if choice == '1':
            return generate_password()
        elif choice == '2':
            try:
                user_length = int(input("Enter the desired password length (default is 8): ") or 8)
                raise ValueError if user_length <= 0 or user_length > 64 else None
            
            except ValueError:
                print("Invalid input for length. Using default length of 8.")
                user_length = 8

            try:
                include_digits = input("Include digits? (y/n, default is y): ").lower() == 'y'
            except ValueError:
                print("Invalid input for digits. Using default setting (yes).")
                include_digits = True

            try:
                include_special_chars = input("Include special characters? (y/n, default is y): ").lower() == 'y'
            except ValueError:
                print("Invalid input for special characters. Using default setting (yes).")
                include_special_chars = True

            try:
                include_lowercase = input("Include lowercase letters? (y/n, default is y): ").lower() == 'y'
            except ValueError:
                print("Invalid input for lowercase letters. Using default setting (yes).")
                include_lowercase = True

            try:
                include_uppercase = input("Include uppercase letters? (y/n, default is y): ").lower() == 'y'
            except ValueError:
                print("Invalid input for uppercase letters. Using default setting (yes).")
                include_uppercase = True
            else:
                if not (include_digits or include_special_chars or include_lowercase or include_uppercase):
                    print("At least one character type must be included. Please try again.")
                    return self.validate_user_input()

            return generate_password(length=user_length, include_digits=include_digits, include_special_chars=include_special_chars, include_lowercase=include_lowercase, include_uppercase=include_uppercase)
        else:
            print("Invalid choice. Please select either 1 or 2.")
            return self.validate_user_input()
        