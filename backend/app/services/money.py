from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

def to_money(value)->Decimal:
    """Convert a float/int/str/Decimal amount to an exact 2-decimal Decimal for storage. Going through str() avoids binary-float artifacts like 0.30000000000000004."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)