import secrets


def generate_secure_number(digits: int = 6) -> int:
    if digits <= 0:
        digits = 6

    # Calculate the lower and upper bounds based on the number of digits
    lower_bound = 10 ** (digits - 1)
    upper_bound = 10 ** digits - 1

    # Generate a random number within the bounds
    return secrets.randbelow(upper_bound - lower_bound + 1) + lower_bound
