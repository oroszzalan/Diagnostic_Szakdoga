class HexInt(int):
    def __new__(cls, value, width=2):
        obj = super().__new__(cls, value)
        obj.width = width
        return obj

    def __str__(self):
        return f"0x{self:0{self.width}x}"

    def __repr__(self):
        return str(self)