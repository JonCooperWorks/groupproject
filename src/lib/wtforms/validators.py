from __future__ import unicode_literals

import re

from wtforms.compat import string_types, text_type

__all__ = (
    'DataRequired', 'data_required', 'Email', 'email', 'EqualTo', 'equal_to',
    'IPAddress', 'ip_address', 'InputRequired', 'input_required', 'Length',
    'length', 'NumberRange', 'number_range', 'Optional', 'optional',
    'Required', 'required', 'Regexp', 'regexp', 'URL', 'url', 'AnyOf',
    'any_of', 'NoneOf', 'none_of', 'MacAddress', 'mac_address', 'UUID'
)


class ValidationError(ValueError):

    """
    Raised when a validator fails to validate its input.
    """

    def __init__(self, message='', *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)


class StopValidation(Exception):

    """
    Causes the validation chain to stop.

    If StopValidation is raised, no more validators in the validation chain are
    called. If raised with a message, the message will be added to the errors
    list.
    """

    def __init__(self, message='', *args, **kwargs):
        Exception.__init__(self, message, *args, **kwargs)


class EqualTo(object):

    """
    Compares the values of two fields.

    :param fieldname:
        The name of the other field to compare to.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated with `%(other_label)s` and `%(other_name)s` to provide a
        more helpful error.
    """

    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(
                field.gettext("Invalid field name '%s'.") % self.fieldname)
        if field.data != other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname
            }
            if self.message is None:
                self.message = field.gettext(
                    'Field must be equal to %(other_name)s.')

            raise ValidationError(self.message % d)


class Length(object):

    """
    Validates the length of a string.

    :param min:
        The minimum required length of the string. If not provided, minimum
        length will not be checked.
    :param max:
        The maximum length of the string. If not provided, maximum length
        will not be checked.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated using `%(min)d` and `%(max)d` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """

    def __init__(self, min=-1, max=-1, message=None):
        assert min != -1 or max != - \
            1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, form, field):
        l = field.data and len(field.data) or 0
        if l < self.min or self.max != -1 and l > self.max:
            if self.message is None:
                if self.max == -1:
                    self.message = field.ngettext('Field must be at least %(min)d character long.',
                                                  'Field must be at least %(min)d characters long.', self.min)
                elif self.min == -1:
                    self.message = field.ngettext('Field cannot be longer than %(max)d character.',
                                                  'Field cannot be longer than %(max)d characters.', self.max)
                else:
                    self.message = field.gettext(
                        'Field must be between %(min)d and %(max)d characters long.')

            raise ValidationError(
                self.message % dict(min=self.min, max=self.max))


class NumberRange(object):

    """
    Validates that a number is of a minimum and/or maximum value, inclusive.
    This will work with any comparable number type, such as floats and
    decimals, not just integers.

    :param min:
        The minimum required value of the number. If not provided, minimum
        value will not be checked.
    :param max:
        The maximum value of the number. If not provided, maximum value
        will not be checked.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated using `%(min)s` and `%(max)s` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """

    def __init__(self, min=None, max=None, message=None):
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, form, field):
        data = field.data
        if data is None or (self.min is not None and data < self.min) or \
                (self.max is not None and data > self.max):
            if self.message is None:
                # we use %(min)s interpolation to support floats, None, and
                # Decimals without throwing a formatting exception.
                if self.max is None:
                    self.message = field.gettext(
                        'Number must be at least %(min)s.')
                elif self.min is None:
                    self.message = field.gettext(
                        'Number must be at most %(max)s.')
                else:
                    self.message = field.gettext(
                        'Number must be between %(min)s and %(max)s.')

            raise ValidationError(
                self.message % dict(min=self.min, max=self.max))


class Optional(object):

    """
    Allows empty input and stops the validation chain from continuing.

    If input is empty, also removes prior errors (such as processing errors)
    from the field.

    :param strip_whitespace:
        If True (the default) also stop the validation chain on input which
        consists of only whitespace.
    """
    field_flags = ('optional', )

    def __init__(self, strip_whitespace=True):
        if strip_whitespace:
            self.string_check = lambda s: s.strip()
        else:
            self.string_check = lambda s: s

    def __call__(self, form, field):
        if not field.raw_data or isinstance(field.raw_data[0], string_types) and not self.string_check(field.raw_data[0]):
            field.errors[:] = []
            raise StopValidation()


class DataRequired(object):

    """
    Validates that the field contains data. This validator will stop the
    validation chain on error.

    If the data is empty, also removes prior errors (such as processing errors)
    from the field.

    :param message:
        Error message to raise in case of a validation error.
    """
    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if not field.data or isinstance(field.data, string_types) and not field.data.strip():
            if self.message is None:
                self.message = field.gettext('This field is required.')

            field.errors[:] = []
            raise StopValidation(self.message)


class Required(DataRequired):

    """
    Legacy alias for DataRequired.

    This is needed over simple aliasing for those who require that the
    class-name of required be 'Required.'

    This class will start throwing deprecation warnings in WTForms 1.1 and be removed by 1.2.
    """


class InputRequired(object):

    """
    Validates that input was provided for this field.

    Note there is a distinction between this and DataRequired in that
    InputRequired looks that form-input data was provided, and DataRequired
    looks at the post-coercion data.
    """
    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if not field.raw_data or not field.raw_data[0]:
            if self.message is None:
                self.message = field.gettext('This field is required.')

            field.errors[:] = []
            raise StopValidation(self.message)


class Regexp(object):

    """
    Validates the field against a user provided regexp.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored if
        `regex` is not a string.
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, regex, flags=0, message=None):
        if isinstance(regex, string_types):
            regex = re.compile(regex, flags)
        self.regex = regex
        self.message = message

    def __call__(self, form, field):
        if not self.regex.match(field.data or ''):
            if self.message is None:
                self.message = field.gettext('Invalid input.')

            raise ValidationError(self.message)


class Email(Regexp):

    """
    Validates an email address. Note that this uses a very primitive regular
    expression and should only be used in instances where you later verify by
    other means, such as email activation or lookups.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        super(Email, self).__init__(
            r'^.+@[^.].*\.[a-z]{2,10}$', re.IGNORECASE, message)

    def __call__(self, form, field):
        if self.message is None:
            self.message = field.gettext('Invalid email address.')

        super(Email, self).__call__(form, field)


class IPAddress(object):

    """
    Validates an IP address.

    :param ipv4:
        If True, accept IPv4 addresses as valid (default True)
    :param ipv6:
        If True, accept IPv6 addresses as valid (default False)
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, ipv4=True, ipv6=False, message=None):
        if not ipv4 and not ipv6:
            raise ValueError(
                'IP Address Validator must have at least one of ipv4 or ipv6 enabled.')
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.message = message

    def __call__(self, form, field):
        value = field.data
        valid = False
        if value:
            valid = (self.ipv4 and self.check_ipv4(value)) or (
                self.ipv6 and self.check_ipv6(value))

        if not valid:
            if self.message is None:
                self.message = field.gettext('Invalid IP address.')
            raise ValidationError(self.message)

    def check_ipv4(self, value):
        parts = value.split('.')
        if len(parts) == 4 and all(x.isdigit() for x in parts):
            numbers = list(int(x) for x in parts)
            return all(num >= 0 and num < 256 for num in numbers)
        return False

    def check_ipv6(self, value):
        parts = value.split(':')
        if len(parts) > 8:
            return False

        num_blank = 0
        for part in parts:
            if not part:
                num_blank += 1
            else:
                try:
                    value = int(part, 16)
                except ValueError:
                    return False
                else:
                    if value < 0 or value >= 65536:
                        return False

        if num_blank < 2:
            return True
        elif num_blank == 2 and not parts[0] and not parts[1]:
            return True
        return False


class MacAddress(Regexp):

    """
    Validates a MAC address.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        pattern = r'^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$'
        super(MacAddress, self).__init__(pattern, message=message)

    def __call__(self, form, field):
        if self.message is None:
            self.message = field.gettext('Invalid Mac address.')

        super(MacAddress, self).__call__(form, field)


class URL(Regexp):

    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    :param require_tld:
        If true, then the domain-name portion of the URL must contain a .tld
        suffix.  Set this to false if you want to allow domains like
        `localhost`.
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, require_tld=True, message=None):
        tld_part = (require_tld and r'\.[a-z]{2,10}' or '')
        regex = r'^[a-z]+://([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        super(URL, self).__init__(regex, re.IGNORECASE, message)

    def __call__(self, form, field):
        if self.message is None:
            self.message = field.gettext('Invalid URL.')

        super(URL, self).__call__(form, field)


class UUID(Regexp):

    """
    Validates a UUID.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        pattern = r'^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$'
        super(UUID, self).__init__(pattern, message=message)

    def __call__(self, form, field):
        if self.message is None:
            self.message = field.gettext('Invalid UUID.')

        super(UUID, self).__call__(form, field)


class AnyOf(object):

    """
    Compares the incoming data to a sequence of valid inputs.

    :param values:
        A sequence of valid inputs.
    :param message:
        Error message to raise in case of a validation error. `%(values)s`
        contains the list of values.
    :param values_formatter:
        Function used to format the list of values in the error message.
    """

    def __init__(self, values, message=None, values_formatter=None):
        self.values = values
        self.message = message
        if values_formatter is None:
            values_formatter = lambda v: ', '.join(text_type(x) for x in v)
        self.values_formatter = values_formatter

    def __call__(self, form, field):
        if field.data not in self.values:
            if self.message is None:
                self.message = field.gettext(
                    'Invalid value, must be one of: %(values)s.')

            raise ValidationError(
                self.message % dict(values=self.values_formatter(self.values)))


class NoneOf(object):

    """
    Compares the incoming data to a sequence of invalid inputs.

    :param values:
        A sequence of invalid inputs.
    :param message:
        Error message to raise in case of a validation error. `%(values)s`
        contains the list of values.
    :param values_formatter:
        Function used to format the list of values in the error message.
    """

    def __init__(self, values, message=None, values_formatter=None):
        self.values = values
        self.message = message
        if values_formatter is None:
            values_formatter = lambda v: ', '.join(text_type(x) for x in v)
        self.values_formatter = values_formatter

    def __call__(self, form, field):
        if field.data in self.values:
            if self.message is None:
                self.message = field.gettext(
                    'Invalid value, can\'t be any of: %(values)s.')

            raise ValidationError(
                self.message % dict(values=self.values_formatter(self.values)))


email = Email
equal_to = EqualTo
ip_address = IPAddress
mac_address = MacAddress
length = Length
number_range = NumberRange
optional = Optional
required = Required
input_required = InputRequired
data_required = DataRequired
regexp = Regexp
url = URL
any_of = AnyOf
none_of = NoneOf
