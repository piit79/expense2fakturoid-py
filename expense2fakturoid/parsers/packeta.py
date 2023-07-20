import re
from datetime import date
from typing import Any, Dict

from .base import ParserBase, ParseError
from .utils import decimal, quantity


line_types = {
    'quantity': quantity,
    'unit_price': decimal,
    'vat_rate': decimal,
}


class ParserPacketa(ParserBase):
    SUPPLIER_CODE = 'packeta'
    DEFAULT_EMAIL = 'info@zasilkovna.cz'
    REGEXES_HEADER = [
        r'(FAKTURA - DAŇOVÝ DOKLAD č.|Faktura - daňový doklad č.)\s+(?P<invoice_number>\d+)',
        r'Variabilní symbol:?\s+(?P<variable_symbol>\S+)',
        r'Datum vystavení:\s+(?P<issue_day>\d+)\. (?P<issue_month>\d{1,2})\. (?P<issue_year>\d{4})',
        r'Datum splatnosti:\s+(?P<due_day>\d{1,2})\. (?P<due_month>\d{1,2})\. (?P<due_year>\d{4})',
        r'Datum uskutečnění plnění:\s+(?P<tax_day>\d{1,2})\. (?P<tax_month>\d{1,2})\. (?P<tax_year>\d{4})',
        r'Fakturujeme Vám služby\s+Množství',
    ]
    REGEX_LINE = (
        r'^\s*(?P<name>.+?)\s+'
        r'(?P<quantity>\d+\.\d+)\s+'
        r'(?P<unit_price>(:?\d+ )*\d+,\d+)\s+'
        r'(?P<vat_rate>\d+,\d+)\s*%\s+'
    )
    REGEX_STOP = r'^\s*Celkem bez DPH\s+'

    def get_header(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert and return the invoice/receipt header data
        """
        header = super().get_header(data)
        header.update({
            'original_number': data['invoice_number'],
            'variable_symbol': data['variable_symbol'],
            'issued_on': date(int(data['issue_year']), int(data['issue_month']), int(data['issue_day'])),
            'due_on': date(int(data['due_year']), int(data['due_month']), int(data['due_day'])),
            'taxable_fulfillment_due': date(int(data['tax_year']), int(data['tax_month']), int(data['tax_day'])),
        })

        return header

    @staticmethod
    def get_line(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert and return the invoice/receipt line data
        """
        for key, data_type in line_types.items():
            data[key] = data_type(data[key])

        return data

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
        try:
            while True:
                line = next(lines_iter)
                if not line.strip():
                    # Skip emtpy lines
                    continue
                if match := re.search(self.REGEX_LINE, line):
                    self.invoice['lines'].append(self.get_line(match.groupdict()))
                elif re.search(self.REGEX_STOP, line):
                    # Parsing complete
                    break
                else:
                    raise ParseError('Line not matched: ' + line)
        except StopIteration:
            raise ParseError('Lines exhausted, STOP regex not matched')

        return self.invoice
