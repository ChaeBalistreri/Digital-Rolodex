import re 
# Python’s regular expression module.
# The re library allows pattern matching in strings. Useful for 
# validating inputs like email addresses, phone numbers, zip codes, etc.


from datetime import datetime
# The datetime module supplies classes for manipulating dates and times.


class Contact:
    """Blueprint for each contact in Digital Rolodex"""

    def __init__(self, name, address=None, phone_num=None, email=None, birth_date=None): # name is required, while all other parameters are optional
        self.name = name
        self.address = address
        self.phone_num = phone_num
        self.email = email
        self.birth_date = birth_date    # Expecting format YYYY-MM-DD

    
    def __str__(self):
        """This is what gets printed when you use print(contact_object).
        Need to have this for clean, readable data from each Contact object."""
        
        return (f"Name: {self.name}\n"
                f"Address: {self.address}\n"
                f"Phone: {self.phone_num}\n"
                f"Email: {self.email}\n"
                f"Date of Birth: {self.birth_date}")
    
    
    def to_dict(self):
        """This converts a Contact object into a Python dictionary. Or serializes the contact into a dictionary for storage or export."""
        
        return {
            "name": self.name,
            "address": self.address,
            "phone_num": self.phone_num,
            "email": self.email,
            "birth_date": self.birth_date
        }
    
    
    def is_minimally_complete(self) -> bool:
        """Return True if this contact has the minimally useful fields.

        Policy:
        - Name must be present (guaranteed by constructor usage)
        - At least one reliable point of contact is present: email OR phone

        Note: Storage may enforce stricter requirements (e.g., require email)
        and skip records; this helper is used for soft warnings and UI hints.
        """

        return bool(self.name and (self.email or self.phone_num))

    
    @classmethod
    def from_dict(cls, data):
        """This is a class method that reconstructs a Contact object from 
        a dictionary (e.g., one you loaded from JSON). cls means the method works on the class itself, not an instance."""
        
        # Only require 'name'; use dict.get for optional fields with sensible defaults (None).
        # This makes loading tolerant of partially filled records while keeping 'name' mandatory.
        name = data.get("name")
        if not name:
            raise ValueError("Contact 'name' is required")

        return cls(
            name=name,
            address=data.get("address"),
            phone_num=data.get("phone_num"),
            email=data.get("email"),
            birth_date=data.get("birth_date"),
        )

    
    @classmethod
    def create_validated(cls, name, address, phone_num, email, birth_date):
        """Safely create a validated Contact object by checking inputs first.
        This function relies upon the is_valid_email() and is_valid_birth_date() functions."""

        if not cls.is_valid_email(email):
            raise ValueError("Invalid email")
        if not cls.is_valid_birth_date(birth_date):
            raise ValueError("Invalid birth date")
        return cls(name, address, phone_num, email, birth_date)

    
    @staticmethod   # @staticmethod is a decorator that tells Python this method belongs to the class, but it does not need access to the instance (self) or the class (cls).
    def is_valid_email(email):
        """Check to see if email matches an expected pattern.
        Explanation of the regex:
        [^@]+       : at least one character that is NOT @
        @           : must contain exactly one @
        [^@]+       : again, one or more characters after the @
        backslash   : a literal
        [^@]+       : some characters after the dot (domain)"""

        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

   
    @staticmethod   # this allows to call the function without being required to reference a Contact class object.
    def is_valid_birth_date(birth_date):
        """This uses datetime.strptime() to verify if the date string is in YYYY-MM-DD format:"""

        try:
            datetime.strptime(birth_date, "%Y-%m-%d")
            return True
        except ValueError:
            return False
