import random
import string

def generate_password(length: int = 12) -> str:
    """Generate a random password.
    
    Args:
        length: Length of password
        
    Returns:
        Random password string
    """
    # Ensure at least one of each type
    chars = string.ascii_letters + string.digits + string.punctuation
    password = [
        random.choice(string.ascii_letters),  # At least one letter
        random.choice(string.digits),         # At least one digit
        random.choice(string.punctuation)     # At least one special char
    ]
    
    # Fill remaining length with random chars
    password.extend(random.choice(chars) for _ in range(length - len(password)))
    
    # Shuffle the password
    random.shuffle(password)
    
    return ''.join(password)
