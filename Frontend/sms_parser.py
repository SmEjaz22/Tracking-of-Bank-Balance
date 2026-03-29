"""
sms_parser.py

Parses SMS messages from Pakistani banks and extracts:
  - amount      (int, always positive)
  - direction   ('credit' or 'debit')
  - bank        (str, e.g. 'HBL', 'MCB')

Returns a ParsedSMS namedtuple, or None if the SMS is not a bank transaction.

Supports: HBL, MCB, UBL, Meezan, Allied, Bank Alfalah, Standard Chartered
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedSMS:
    amount:    int
    direction: str   # 'credit' or 'debit'
    bank:      str


# ---------------------------------------------------------------------------
# Bank sender IDs — used to identify which bank sent the SMS
# ---------------------------------------------------------------------------

BANK_SENDERS = {
    'HBL':   ['HBL', 'HBLPAK', '+923452945985'],
    'MCB':   ['MCB', 'MCBBANK', 'MCB-BANK'],
    'UBL':   ['UBL', 'UBLBANK', 'UBL-ALERTS'],
    'MEEZAN':['MEEZAN', 'MEEZANBANK', 'MEEZAN-BK'],
    'ALLIED':['ALLIED', 'ALLIEDBANK', 'ABL'],
    'ALFALAH':['ALFALAH', 'BANKALFALAH', 'BAF'],
    'SCB':   ['SCB', 'SCBANK', 'STANDARD-CH'],
    'HABIB': ['HMB', 'HABIBMETRO'],
}


# ---------------------------------------------------------------------------
# Regex patterns — order matters, more specific first
# ---------------------------------------------------------------------------

# Matches amounts like: Rs.4,500  Rs 4500  PKR 4,500  PKR4500  4,500.00
AMOUNT_PATTERN = r'(?:Rs\.?|PKR\.?)\s*([\d,]+(?:\.\d{1,2})?)'

# Credit keywords
CREDIT_KEYWORDS = [
    r'\bcredited\b', r'\bdeposit(?:ed)?\b', r'\breceived\b',
    r'\binward\b',   r'\bpayment\s+received\b', r'\brefund\b',
    r'\bsalary\b',   r'\bpayroll\b',
]

# Debit keywords
DEBIT_KEYWORDS = [
    r'\bdebited\b',   r'\bpurchase\b',  r'\bwithdraw(?:al|n)?\b',
    r'\bpaid\b',      r'\btransfer(?:red)?\b(?!\s+to\s+your)',
    r'\bcharged\b',   r'\bdeducted\b',  r'\boutward\b',
    r'\bpayment\s+of\b',
]


def parse(sender: str, body: str) -> Optional[ParsedSMS]:
    """
    Main entry point.
    Returns ParsedSMS if this looks like a bank transaction, else None.
    """
    bank = _identify_bank(sender)
    if bank is None:
        return None

    body_lower = body.lower()

    amount = _extract_amount(body)
    if amount is None:
        return None

    direction = _extract_direction(body_lower)
    if direction is None:
        return None

    return ParsedSMS(amount=amount, direction=direction, bank=bank)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _identify_bank(sender: str) -> Optional[str]:
    sender_upper = sender.upper().strip()
    for bank, aliases in BANK_SENDERS.items():
        for alias in aliases:
            if alias in sender_upper:
                return bank
    return None


def _extract_amount(body: str) -> Optional[int]:
    match = re.search(AMOUNT_PATTERN, body, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).replace(',', '').split('.')[0]  # strip decimals
    try:
        return int(raw)
    except ValueError:
        return None


def _extract_direction(body_lower: str) -> Optional[str]:
    for pattern in CREDIT_KEYWORDS:
        if re.search(pattern, body_lower):
            return 'credit'
    for pattern in DEBIT_KEYWORDS:
        if re.search(pattern, body_lower):
            return 'debit'
    return None
