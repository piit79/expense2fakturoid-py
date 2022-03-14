from typing import Any, Dict, List, Optional, Type

from fakturoid import Fakturoid, Expense, InvoiceLine, Subject

from .parsers import *


class InvalidConfigException(Exception):
    """Raised when the configuration is invalid"""


class Suppliers:
    @classmethod
    def get_all_parsers(cls) -> List[Type[ParserBase]]:
        # FIXME: only supports direct concrete subclasses
        return ParserBase.__subclasses__()

    @classmethod
    def get_valid_codes(cls) -> List[str]:
        """
        Return the list of valid supplier codes
        """
        return [c.SUPPLIER_CODE for c in cls.get_all_parsers()]

    @classmethod
    def get_parser_class(cls, supplier_code) -> Optional[Type[ParserBase]]:
        """
        Return the parser class given a supplier code or None if not found
        """
        for c in cls.get_all_parsers():
            if c.SUPPLIER_CODE == supplier_code:
                return c
        return None


class Expense2Fakturoid:
    APP_NAME = 'Expense2Fakturoid'

    def __init__(
            self,
            config: Dict[str, Any],
            supplier_code: str,
            filename: str,
            bank_account_id: Optional[int] = None
    ):
        self.fa = Fakturoid(config.get('slug'), config.get('email'), config.get('api_key'), self.APP_NAME)
        self.config = config
        self.supplier_code = supplier_code
        self.filename = filename
        self.bank_account_id = bank_account_id
        self.supplier_config = self.config.get(self.supplier_code, {})
        self.validate_supplier_config()
        self.parser = None

    def validate_supplier_config(self):
        """
        Validate the supplier config

        :raises: InvalidConfigException
        """
        if (bank_account_id := self.supplier_config.get('bank_account_id')) is not None:
            try:
                self.supplier_config['bank_account_id'] = int(bank_account_id)
            except ValueError:
                raise InvalidConfigException(
                    f'Invalid `bank_account_id` specified in {self.supplier_code} config: {bank_account_id}'
                )

    def find_subject(self, email: str) -> Optional[Subject]:
        """
        Return the Fakturoid subject with the given email, or None if not found
        """
        return next((s for s in self.fa.subjects.search(email) if s.email == email), None)

    def create_expense(self, data) -> Expense:
        """
        Create the expense in Fakturoid and return it
        """
        expense = Expense(**data)
        self.fa.save(expense)

        return expense

    def get_bank_account_id(self) -> Optional[int]:
        """
        Return the bank account id to use for the payment entry
        """
        return self.bank_account_id or self.supplier_config.get('bank_account_id')

    def mark_expense_paid(self, expense, paid_on):
        """
        Mark the expense as paid in Fakturoid
        """
        self.fa.fire_expense_event(
            expense.id, 'pay', paid_on=paid_on, bank_account_id=self.get_bank_account_id()
        )

    def run(self) -> str:
        """
        Run the import and return the URL of the expense in Fakturoid
        """
        if not (parser_class := Suppliers.get_parser_class(self.supplier_code)):
            raise ValueError(f'Unknown supplier {self.supplier_code}')

        parser = parser_class(self.filename, self.supplier_config)

        supplier_email = parser.get_supplier_email()
        if not (subject := self.find_subject(supplier_email)):
            raise InvalidConfigException(f'Subject with e-mail {supplier_email} not found in Fakturoid')

        data = parser.parse()

        lines = data.pop('lines')
        data['subject_id'] = subject.id
        data['lines'] = [InvoiceLine(**line) for line in lines]

        expense = self.create_expense(data)

        if parser.pay:
            self.mark_expense_paid(expense, paid_on=data['issued_on'])

        return expense.html_url
