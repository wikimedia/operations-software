#!/usr/bin/env python3
"""A simple, easy to use, pattern-matching quote reviewer.

Currently limited to quotes issued by Dell.
"""

# Copyright © 2018 Wikimedia Foundation, Inc.
# Copyright © 2018 Faidon Liambotis <faidon@wikimedia.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY CODE, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import re

import yaml

try:
    import logging
    from colorlog import ColoredFormatter as Formatter, StreamHandler

    LOG_FORMAT = "%(log_color)s%(message)s"
except ImportError:
    import logging
    from logging import Formatter, StreamHandler

    LOG_FORMAT = "%(message)s"


logger = logging.getLogger()
FORMAT_IDENTIFIER = 'Your Shopping Cart'


class ConfigParseError(Exception):
    """Configuration file parsing error."""


class PdfParseError(Exception):
    """PDF file parsing error."""


class PdfToTextNotFound(Exception):
    """pdftotext (i.e. poppler) not found error."""


try:
    import pdftotext

    def extract_text_from_pdf(pdf_file, physical=False):
        """Extract text from a PDF file handle; return a list of pages."""
        try:
            pdf = pdftotext.PDF(pdf_file, physical=physical)
        except pdftotext.Error as exc:
            raise PdfParseError("Unable to PDF -> text: " + str(exc))
        return pdf

except ImportError:
    import os
    import subprocess
    import textwrap

    def extract_text_from_pdf(pdf_file, physical=False):
        """Extract text from a PDF file handle; return a list of pages."""
        command = ["pdftotext"]
        if physical:
            command.append("-layout")

        command += ["-enc", "UTF-8", "-", "-"]
        try:
            subp = subprocess.run(command, stdin=pdf_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subp.check_returncode()
        except subprocess.CalledProcessError as exc:
            err = subp.stderr.decode("utf8", "ignore").strip()
            err = textwrap.indent(err, "  ")
            raise PdfParseError("Unable to PDF -> text:\n" + err)
        except IOError as exc:
            if exc.errno == os.errno.ENOENT:
                raise PdfToTextNotFound("pdftotext not found")
            else:
                raise

        # decode as utf-8 and split on form-feed characters
        pdf = subp.stdout.decode("utf8", "ignore").split("\f")
        return pdf


def parse_pdf(pdf_file):
    """Parse the PDF quote, extract all SKUs and return them in a dict."""
    pdf = extract_text_from_pdf(pdf_file)
    if any(FORMAT_IDENTIFIER in page for page in pdf):
        return parse_portal_pdf(pdf)
    else:
        pdf_file.seek(0)
        pdf = extract_text_from_pdf(pdf_file, physical=True)
        return parse_legacy_pdf(pdf)


def parse_legacy_pdf(pdf):
    """Parse the PDF quote, extract all SKUs and return them in a dict."""
    item_res = [
        # ~2018-style quotes
        r"(?P<sku>\d{3}-[0-9A-Z]{4}) +(?P<description>.+?) +(\d+) +- +-",
        # ~2019-style quotes
        r" +(?P<description>.+?) +(?P<sku>\d{3}-[0-9A-Z]{4}) + - + (\d+) +-",
    ]
    parsed = {}
    for page in pdf:
        for line in page.splitlines():
            # check against the multiple regexps
            for item_re in item_res:
                match = re.match(item_re, line)
                if match is not None:
                    break

            # no matches found
            if match is None:
                continue

            parsed[match.group("sku")] = match.group("description")

    return parsed


def parse_portal_pdf(pdf):
    parsed = {}
    for page_num, page in enumerate(pdf, 1):
        if not page:
            continue

        tokens = []
        in_token = False
        for line in page.splitlines():
            if not line:
                in_token = False
                continue

            if not in_token:
                tokens.append(line)
            else:
                if tokens[-1] == FORMAT_IDENTIFIER:  # Missing separator on new page
                    tokens.append(line)
                else:
                    last = tokens.pop()
                    tokens.append(last + f' {line}')

            in_token = True

        try:
            start = tokens.index('Category')
        except ValueError:
            logger.warning('No SKUs found on page {num}'.format(num=page_num))
            continue

        headers = ['Category', 'Description', 'Code', 'SKU', 'ID']
        key_index = 3
        value_index = 1
        batch = len(headers)
        if tokens[start:start+batch] != headers:
            raise PdfParseError('Unable to find the table headers')

        for i in range(start+batch, len(tokens), batch):
            line = tokens[i:i+batch]
            if len(line) < batch:
                continue  # Reached end of page

            skus = re.findall(r'\[(\d{3}-[0-9A-Z]{4})\]', line[key_index])
            for sku in skus:
                parsed[sku] = line[value_index]

    return parsed


def parse_args(argv):
    """Parse and return the parsed command line arguments."""
    parser = argparse.ArgumentParser(
        prog="quotereviewer",
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all SKUs present in the quote file",
    )
    parser.add_argument(
        "--config",
        type=argparse.FileType("r"),
        default=parser.prog + ".yml",
        help="Configuration file",
    )
    parser.add_argument(
        "filename",
        type=argparse.FileType("rb"),
        help="Filename of the quote to review",
    )
    return parser.parse_args(argv)


def parse_config(config_file):
    """Parse the YAML config file, return the three SKU lists."""
    try:
        config = yaml.safe_load(config_file)
    except yaml.scanner.ScannerError as exc:
        raise ConfigParseError("Could not parse the config file: " + str(exc))

    if config is None:
        config = {}

    return (
        config.get("required", {}),
        config.get("disallowed", {}),
        config.get("optional", {}),
    )


def setup_logging(level=logging.DEBUG):
    """Sets up a logger instance."""
    handler = StreamHandler()
    handler.setFormatter(Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(level)


def main(argv=None):
    """Main entry point"""
    args = parse_args(argv)
    setup_logging()

    try:
        required, disallow, optional = parse_config(args.config)
        parsed = parse_pdf(args.filename)
    except (ConfigParseError, PdfParseError, PdfToTextNotFound) as exc:
        logger.critical(exc)
        raise SystemExit(2)
    except Exception as exc:
        logger.exception("Unhandled error while parsing: %s", exc)
        raise SystemExit(3)

    if args.show_all:
        logger.debug("SKUs in quote:")
        for sku in sorted(parsed):
            logger.debug("  • %s %s", sku, parsed[sku])

    missing = set(required) - set(parsed)
    if missing:
        logger.error("The following required SKUs are missing:")
        for sku in sorted(missing):
            logger.error("  • %s %s", sku, required[sku])

    disallowed = set(disallow) & set(parsed)
    if disallowed:
        logger.error("The following disallowed SKUs are present:")
        for sku in sorted(disallowed):
            logger.error("  • %s %s", sku, disallow[sku])

    unknown = set(parsed) - set(required) - set(disallow) - set(optional)
    if unknown:
        logger.warning("The following SKUs are unknown:")
        for sku in sorted(unknown):
            logger.warning("  • %s %s", sku, parsed[sku])

    if not missing | disallowed | unknown:
        logger.info("Quote looks good!")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
