from flask import json, jsonify
from enum import Enum

from pydantic import ValidationError
from pydantic_core import ErrorDetails


class ErrorCode(Enum):
    """Enum containing error messages."""

    USER_NOT_FOUND = "User with such ID doesn't exist."
    UNKNOWN = "An unknown error has occured."
    ALREADY_EXISTS = "Such object already exists."

class PasswordRequirements(Enum):
    """Enum containing password requirement messages."""

    UPPERCASE = "The password doesn't have enough Uppercase characters"
    SPECIAL = "The password doesn't have enough Special characters"
    NUMBERS = "The password doesn't have enough Numerical characters"
    NONLETTERS = "The password doesn't have enough Non-Letter characters"
    ENTROPYBITS = "The password is too predictable"
    STRENGTH = "The password is too weak"


CUSTOM_MESSAGES = {
    'value_error:reason': '{reason}',
    'value_error:error': '{error}',
}
"""Dictionary containing formatting strings for Validation Errors."""


def convert_validation_errors(
        e: ValidationError, custom_messages: dict[str, str]) -> list[ErrorDetails]:
    new_errors: list[ErrorDetails] = []
    for error in e.errors():
        custom_message_code = f"{error['type']}:{','.join(error['ctx'].keys())}"
        custom_message = custom_messages.get(custom_message_code)
        if custom_message:
            ctx = error.get('ctx')
            error['msg'] = (custom_message.format(
                **ctx) if ctx else custom_message)
            # Clear the unneccessarry details
            error.pop('url')
            error.pop('ctx')
        new_errors.append(error)
    return new_errors


def create_error_response(*error_messages: ErrorCode | str | Exception, status_code=400):
    error_list = []

    for error_msg in error_messages:
        if isinstance(error_msg, str):
            error_list.append({'msg': error_msg})
        elif isinstance(error_msg, ErrorCode):
            error_list.append({'msg': error_msg.value})
        # Exceptions:
        elif isinstance(error_msg, ValidationError):
            # Convert errors into a properly styled format
            new_errors = convert_validation_errors(error_msg, custom_messages=CUSTOM_MESSAGES)
            error_list.extend(new_errors)
        elif isinstance(error_msg, Exception):
            error_list.append({'msg': error_msg.args[0]})
        # No match:
        else:
            raise ValueError(
                f'The incompatible object type was given: {type(error_messages)}')

    response_dict = {"errors": error_list}
    return jsonify(response_dict), status_code
