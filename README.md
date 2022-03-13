# expense2fakturoid-py

If you use [Fakturoid](https://fakturoid.cz) and

 * Receive invoices from [Zasilkovna](https://zasilkovna.cz), or
 * Post parcels by Czech Post and receive electronic posting receipts by e-mail

`expense2fakturoid-py` allows you to automatically import these documents into
Fakturoid by parsing the PDF file.

## Disclaimer

**This is a work in progress.** While it seems to work well for the few invoices/receipts
I tested with, please consider this a beta-quality software. 

If you encounter any problems, please file a [GitHub issue](https://github.com/piit79/expense2fakturoid-py/issues). 

## Getting started

    # Install pdftotext build dependencies
    sudo apt install build-essential pkg-config python3-dev libpoppler-cpp-dev  # Debian/Ubuntu
    sudo yum install gcc-c++ pkgconfig poppler-cpp-devel python3-devel          # Fedora/RedHat
    brew install pkg-config poppler python                                      # macOS

    # Clone the repository
    git clone https://github.com/piit79/expense2fakturoid-py.git
    cd expense2fakturoid-py

    # Create the Python 3 virtualenv and install dependencies
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt

    # Install the expense2fakturoid module
    venv/bin/python setup.py install

    # Copy the sample configuration file
    cp expense2fakturoid.sample.yaml expense2fakturoid.yaml

## Configuration

The path to the configuration file `expense2fakturoid.yaml` can be specified on the command
line (`--config/-c`). If it's not, `expense2fakturoid` will look in the current directory,
or in the operating system configuration directory:
 * `$XDG_CONFIG_HOME` or  `~/.config` on Linux
 * `C:\Users\<username>\AppData` on Windows 

The only required config entries are `slug`, `email` and `api_key`. All entries are described 
in the sample configuration file `expense2fakturoid.sample.yaml`.

## Running

    venv/bin/expense2fakturoid --supplier packeta invoice.pdf

This will parse the PDF invoice and create the complete expense entry in Fakturoid including 
the PDF attachment.

Please note the supplier contact must already exist in Fakturoid.

## How it works

 * `expense2fakturoid-py` uses `pdftotext` module to convert the PDF document into plain text
 * It parses the resulting output to get all the invoice/receipt details
 * It searches for the Fakturoid subject identified by the e-mail specified in the configuration
 * It creates the expense in Fakturoid
 * It marks the expense as paid if specified in the supplier configuration (as is the case with
   Czech Post)
 * Finally, it displays a link to the newly created expense in Fakturoid

## Dependencies

 * Python 3.8+ (I can finally use the [walrus operator](https://docs.python.org/3/whatsnew/3.8.html) :)
 * [pdftotext](https://pypi.org/project/pdftotext/) Python module
 * My fork of the [python-fakturoid](https://github.com/piit79/python-fakturoid) module
   (the upstream module doesn't contain support for expenses yet)

## TODO

 * Add support for supplier auto-detection
 * Add support for more suppliers (AliExpress, JLCPCB are ones I use quite often)
