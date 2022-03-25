from setuptools import setup


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

long_description = """
Allows creating complete expense entries in the on-line invoicing system Fakturoid <https://www.fakturoid.cz/>
by parsing the PDF invoices/bills.
"""

setup(
    name='expense2fakturoid',
    version='1.1.0',
    packages=['expense2fakturoid', 'expense2fakturoid.parsers'],
    url='https://github.com/piit79/expense2fakturoid-py',
    license='GPLv3',
    author='Petr Sedlacek',
    author_email='petr@sedlacek.biz',
    description='Import expenses from PDF to Fakturoid',
    long_description=long_description,
    platforms='any',
    keywords=['fakturoid', 'expense', 'import'],
    install_requires=requirements,
    # tests_require=['mock'],  # No tests yet, sorry
    # test_suite="tests",
    scripts=['bin/expense2fakturoid'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
)
