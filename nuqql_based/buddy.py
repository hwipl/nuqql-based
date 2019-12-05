"""
Buddies in account's buddy list
"""


class Buddy:
    """
    Storage for buddy specific information
    """

    def __init__(self, name: str = "none", alias: str = "none",
                 status: str = "Available") -> None:
        self.name = name
        self.alias = alias
        self.status = status
