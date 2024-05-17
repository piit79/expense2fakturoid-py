import re
from datetime import date
from itertools import cycle
from typing import Any, Dict, Optional, Union

from .base import ParserBase, ParseError
from .utils import decimal, quantity

SERVICE_CODES = {
    '282': 'Cenný balík do zahraničí - ekonomický (max. 30kg)',
    # '282': 'Cenný balík do zahraničí - prioritní (max. 30kg)',
    '254': 'Doporučená slepecká zásilka do zahraničí (max. 7kg)',
    '251': 'Doporučená zásilka do zahraničí (max. 2kg)',
    '258': 'EMS do zahraničí (max. 30kg)',
    '285': 'Obchodní balík do zahraničí (max. 30kg)',
    '253': 'Obyčejná slepecká zásilka do zahraničí (max. 7kg)',
    '250': 'Obyčejná zásilka do zahraničí (max. 2kg)',
    '280': 'Standardní balík do zahraničí - ekonomický (max. 30kg)',
    # '280': 'Standardní balík do zahraničí - prioritní (max. 30kg)',
    '256': 'Tiskovinový pytel do zahraničí - Doporučený (max. 30kg)',
    '255': 'Tiskovinový pytel do zahraničí - Obyčejný (max. 30kg)',
}
SERVICE_DEFAULT = 'Doporučená zásilka'


line_types = {
    'quantity': quantity,
    'unit_price': decimal,
    'vat_rate': decimal,
}


class ParserCPost(ParserBase):
    SUPPLIER_CODE = 'cpost'
    DEFAULT_EMAIL = 'info@cpost.cz'
    DEFAULT_PAYMENT_METHOD = 'card'
    MARK_PAID = True

    REGEXES_HEADER = [
        (r'POŠTA:\s+(?P<post_office>.+?)\s+'
         r'DATUM PODÁNÍ:\s+(?P<issue_day>\d+)\.(?P<issue_month>\d{1,2})\.(?P<issue_year>\d{4})'),
        r'Kontakty\s+Hmotnost',
    ]
    REGEXES_LINE = (
        (r'\d+\s+(?P<tracking>[A-Z]{2}\d{9}[A-Z]{2})\s+(?P<type>\S+)\s+(?P<customer_name>.+?)\s+'
         r'\d+\.\d+\s+(?P<unit_price>\d+\.\d+)'),
        r'^\s+(?P<service_code>\d+)\s*$',
        r'^\s+(?P<customer_email>\S+@\S+)\s*$',
    )
    REGEX_STOP = r'^\s*Celkem zásilek'

    recipient_name: str
    recipient_email: str
    tracking_number: str
    posting_office: str

    def __init__(self, filename, supplier_config: Optional[Dict] = None, debug: bool = False):
        super().__init__(filename, supplier_config, debug)
        self.recipient_name = None
        self.recipient_email = None
        self.tracking_number = None
        self.posting_office = None

    def get_service(self, service_code) -> str:
        """
        Return the service name for the given service code
        """
        return SERVICE_CODES.get(service_code, self.supplier_config.get('default_service') or SERVICE_DEFAULT)

    def get_header(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert and return the invoice/receipt header data
        """
        header = super().get_header(data)
        issued_on = date(int(data['issue_year']), int(data['issue_month']), int(data['issue_day']))
        header.update({
            'document_type': 'bill',
            'invoice_number': f"{data['issue_year']}{data['issue_month']}{data['issue_day']}",
            'issued_on': issued_on,
            'due_on': issued_on,
            'taxable_fulfillment_due': issued_on,
        })

        return header

    def get_line(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert and return the invoice/receipt line data
        """
        line = {
            'name': self.get_service(data['service_code']),
            'quantity': 1,
            'unit_name': 'ks',
            'unit_price': decimal(data['unit_price']),
            'vat_rate': 0,
        }

        return line

    def add_notes(self, data, bill_line):
        """
        Add expense private notes
        """
        self.invoice['private_note'] = (
            f"Pošta: {data['post_office']}\n"
            f"{bill_line['tracking']} {bill_line['customer_name']} ({bill_line['customer_email']})"
        )

    def parse(self) -> Dict[str, Any]:
        """
        Parse the invoice/receipt and return the data

        :raises: ParseError
        """
        data = {}
        regexi = iter(self.REGEXES_HEADER)
        regex = next(regexi)
        lines_iter = iter(self.lines)
        try:
            while True:
                line = next(lines_iter)
                if match := re.search(regex, line):
                    data.update(match.groupdict())
                    if not (regex := next(regexi, None)):
                        # This was the last regex
                        break
        except StopIteration:
            raise ParseError(f'Lines exhausted, regex not matched: {regex}')

        self.invoice = self.get_header(data)
        regexi = cycle(self.REGEXES_LINE)
        regex = next(regexi)
        bill_line = {}
        try:
            while True:
                line = next(lines_iter)
                if match := re.search(regex, line):
                    bill_line.update(match.groupdict())
                    if regex == self.REGEXES_LINE[-1]:
                        # This was the last line regex, add the invoice/receipt
                        self.invoice['lines'].append(self.get_line(bill_line))
                        if 'private_note' not in self.invoice:
                            self.add_notes(data, bill_line)
                            self.recipient_name = bill_line['customer_name']
                            self.recipient_email = bill_line['customer_email']
                            self.tracking_number = bill_line['tracking']
                            self.posting_office = data['post_office']
                        bill_line = {}
                    regex = next(regexi)
                elif re.search(self.REGEX_STOP, line):
                    # Parsing complete
                    break
        except StopIteration:
            raise ParseError('Lines exhausted, STOP regex not matched')

        return self.invoice
