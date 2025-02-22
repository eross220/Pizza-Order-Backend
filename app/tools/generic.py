
def check_password(v: str) -> str:
    if not v:
        return "Password cannot be empty."
    if len(v) < 8:
        return "Password must be at least 8 characters long."

    conditions_met = sum(
        [
            any(char.isupper() for char in v),
            any(char.islower() for char in v),
            any(char.isdigit() for char in v),
            any(not char.isalnum() for char in v),
        ]
    )

    if conditions_met < 2:
        return (
            "Password must meet at least two of the following: "
            "contain an uppercase letter, a lowercase letter, a number, or a special character."
        )
    return ""
