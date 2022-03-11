import argparse
import sys
import yaml
from typing import Any, Dict, List, Optional, Type

from fakturoid import Fakturoid, Expense, InvoiceLine, Subject
from requests.exceptions import HTTPError

from parsers import *


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


class Expenses2Fakturoid:
    APP_NAME = 'Expense2Fakturoid'

    def __init__(self, config, supplier_code, filename):
        self.fa = Fakturoid(config.get('slug'), config.get('email'), config.get('api_key'), self.APP_NAME)
        self.config = config
        self.supplier_code = supplier_code
        self.filename = filename
        self.supplier_config = self.config.get(self.supplier_code, {})
        self.parser = None

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

    def mark_expense_paid(self, expense, paid_on):
        """
        Mark the expense as paid in Fakturoid
        """
        self.fa.fire_expense_event(
            expense.id, 'pay', paid_on=paid_on, bank_account_id=self.supplier_config.get('bank_account_id')
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


def get_args():
    """
    Parse and return the command-line arguments
    """
    parser = argparse.ArgumentParser(description='Parse supplier invoice and create it in Fakturoid')
    parser.add_argument('--config', '-c', help='config file name', default='expense2fakturoid.yaml')
    parser.add_argument('--supplier', '-s', help='supplier type', required=True, choices=Suppliers.get_valid_codes())
    parser.add_argument('filename', help='supplier invoice file name')

    return parser.parse_args()


def get_config(config_file) -> Dict[str, Any]:
    """
    Return the configuration file data
    """
    with open(config_file, 'r') as f:
        return yaml.load(f, yaml.SafeLoader)


def validate_config(config_data: Dict[str, Any]):
    """
    :rases: InvalidConfigException
    """
    required_keys = ['slug', 'email', 'api_key']
    if missing := [key for key in required_keys if not config_data.get(key)]:
        raise InvalidConfigException('Required configuration key(s) not set: ' + ', '.join(missing))


def main():
    args = get_args()
    try:
        config = get_config(args.config)
        validate_config(config)
    except FileNotFoundError:
        print(f'Config file {args.config} not found, please specify --config/-c')
        sys.exit(1)
    except IOError as e:
        print(f'Cannot open config file: {e}')
        sys.exit(2)
    except InvalidConfigException as e:
        print(e)
        sys.exit(3)

    e2fa = Expenses2Fakturoid(config, args.supplier, args.filename)
    try:
        url = e2fa.run()
    except HTTPError as e:
        print(f'Error connecting to Fakturoid: {e}')
        sys.exit(4)
    except (FileNotFoundError, IOError) as e:
        print(f'Cannot open input file: {e}')
        print(repr(e))
        sys.exit(5)
    except (InvalidConfigException, ParseError) as e:
        print(e)
        sys.exit(6)

    print(f'Expense imported successfully: {url}')


if __name__ == '__main__':
    main()
