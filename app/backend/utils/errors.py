from flask import jsonify
from enum import Enum


class ErrorCode(Enum):
    """Enum containing error messages."""
    
    USER_NOT_FOUND = "User with such ID doesn't exist."
    UNKNOWN = "An unknown error has occured."


def create_error_response(*error_messages: ErrorCode|str, status_code=400):
    error_list = []
    
    for error_msg in error_messages:
        if isinstance(error_msg, str):
            error_list.append({'msg': error_msg})
        elif isinstance(error_msg, ErrorCode):
            error_list.append({'msg': error_msg.value})
        
    response_dict = {"errors": error_list}
    return jsonify(response_dict), status_code


class PasswordRequirements(Enum):
    """Enum containing password requirement messages."""
    
    UPPERCASE = "The password doesn't have enough Uppercase characters"
    SPECIAL = "The password doesn't have enough Special characters"
    NUMBERS = "The password doesn't have enough Numerical characters"
    NONLETTERS = "The password doesn't have enough Non-Letter characters"
    ENTROPYBITS = "The password is too predictable"
    STRENGTH = "The password is too weak"