from abc import ABC
from typing import Any, Dict, Optional

import base64
import pdftotext


class ParseError(Exception):
    """Raised when the parsing fails"""


class ParserBase(ABC):
    SUPPLIER_CODE: str = None
    DEFAULT_EMAIL: str = None
    DEFAULT_PAYMENT_METHOD = 'bank'
    PAY = False

    def __init__(self, filename, supplier_config: Optional[Dict]):
        self.filename = filename
        self.supplier_config = supplier_config
        self.lines = None
        self.invoice = {}
        self.read_file()

    @property
    def pay(self) -> bool:
        """
        Return True if the expense should be marked as paid
        """
        return self.supplier_config.get('pay', self.PAY)

    def get_supplier_email(self) -> str:
        """
        Return the e-mail of the supplier contact in Fakturoid
        """
        return self.supplier_config.get('email', self.DEFAULT_EMAIL)

    def read_file(self):
        """
        Read the input PDF file as text
        """
        with open(self.filename, 'rb') as f:
            pdf = pdftotext.PDF(f, physical=True)
            self.lines = '\n'.join(pdf).split('\n')

    def get_attachment(self) -> str:
        """
        Return the input file as Base64-encoded attachment string
        """
        with open(self.filename, 'rb') as f:
            data = f.read()
        data_base64 = base64.b64encode(data).decode('UTF-8')

        return 'data:application/pdf;base64,' + data_base64

    def get_header(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Return the invoice/receipt header data
        """
        return {
            'payment_method': self.supplier_config.get('payment_method', self.DEFAULT_PAYMENT_METHOD),
            'attachment': self.get_attachment(),
            'lines': [],
        }

    def parse(self) -> Dict[str, Any]:
        """
        Parse the invoice/receipt and return the data

        :raises: ParseError
        """
        raise NotImplementedError
