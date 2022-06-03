class ValidationError(ValueError):
    """
    Raised when a validator fails to validate its input.
    """

    def __init__(self, message="", *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)

class PhoneNumber:

    def __init__(self, message=None) -> None:

        self.message = message
    
    def __call__(self, form, field):

        data = field.data
        length = len(data)

        if self.message is not None:
            message = self.message

        if length != 11:
            field.gettext("phone number must be 11 digits")
        
        if data[0] != '+':
            field.gettext("phone number must start with '+'")

        if not data[1:10].isdigit():
            field.gettext("digits after the '+' must be integers")
        
        
        raise ValidationError(message)

        
