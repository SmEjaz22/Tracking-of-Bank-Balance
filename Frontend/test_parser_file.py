from sms_parser import parse

# HBL credit
print(parse('HBLPAK', 'Dear Customer, Rs.4,500 has been credited to your account.'))

# MCB debit
print(parse('MCBBANK', 'Your MCB account has been debited PKR 12,000 for purchase.'))

# Not a bank SMS
print(parse('Telenor', 'Your balance is Rs.50'))
