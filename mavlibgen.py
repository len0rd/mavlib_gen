#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
################################################################################
# \file cli
#
# Top level Command Line Interface to the mavlib_gen library
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import argparse
import sys
import logging
from pathlib import Path
from typing import List, Union

from mavlib_gen.validator import MavlinkXmlValidator
from mavlib_gen.generator import MavlibGenerator
from schema import Schema, SchemaError
from ruamel.yaml import YAML


class MavlibgenRunner:
    """
    Top-level class to run mavlib_gen's validation and generation components.
    """

    def __init__(
        self, mavlink_xmls: Union[str, List[str]], config_file: str = None, generator: any = None
    ):
        """
        :param config_file: path to the yaml configuration file that specifies the
            settings for this MavlibgenRunner instance. Will be used by @ref run
        :param mavlink_xmls: List of 1 or more paths to mavlink xmls to validate and generate
            with this MavlibgenRunner instance
        :param generator: Optional. Manually specify a generator to use. Will be overwritten by
            functions like @ref load_configuration if the provided :param: config_file specifies
            generators. A generator only needs a function that looks like
            MavlibGenerator.generate_all
        """
        self.config_file = Path(config_file).resolve() if config_file is not None else None
        if not isinstance(mavlink_xmls, list):
            mavlink_xmls = [mavlink_xmls]
        self.mavlink_xmls = [Path(xml_file).resolve() for xml_file in mavlink_xmls]
        self.generator = generator
        self.validator = MavlinkXmlValidator()

    def load_configuration(self) -> bool:
        """
        Verify the configuration file provided at construction complies with the libraries schema
        """
        if self.config_file is None:
            return True
        elif not self.config_file.is_file():
            logging.error(f"Unable to locate the configuration file {self.config_file}")
            return False
        yaml = YAML(type="safe")
        config_schema = Schema(MavlibGenerator.yaml_schema())
        with open(self.config_file, "r") as conf_raw:
            user_config = yaml.load(conf_raw)
            try:
                config_schema.validate(user_config)
                logging.debug("User config file is compliant to the mavlib schema")
            except SchemaError as se:
                logging.error(
                    f"Encountered an error while validating {self.config_file} against the schema"
                )
                raise se
            self.generator = MavlibGenerator.from_config(user_config.get("generate", {}))

    def run(self) -> bool:
        # load settings from configuration file
        if not self.load_configuration():
            return False

        validated_xmls = self.validator.validate(self.mavlink_xmls)
        if validated_xmls is None:
            return False  # failed to validated xml files

        if self.generator is not None:
            return self.generator.generate_all(validated_xmls)
        return True

    @classmethod
    def generate_once(
        cls, xmls: Union[str, List[str]], output_lang: str, output_location: str
    ) -> bool:
        """
        Do a single language generation using default configuration. No YAML required

        Arguments:
            xmls: One or more paths to MAVLink xml files to validate and generate
            output_lang: the language to generate
            output_location: base directory to place resulting files
        """
        # input validation
        if xmls is None:
            logging.fatal("No valid Mavlink xml paths provided")
            return False

        if not isinstance(xmls, list):
            xmls = [xmls]

        validator = MavlinkXmlValidator()

        validated_xmls = validator.validate(xmls)
        if validated_xmls is None:
            return False  # failed to validate

        generator = MavlibGenerator(outdir=output_location)
        return generator.generate_one(validated_xmls, output_lang)

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        """
        Specify CLI args that can be used to construct and run MavlibgenRunner
        """
        parser.add_argument(
            "config_file",
            help="yaml configuration file for this run of mavlibgen. See docs for config file schema",
        )

        parser.add_argument(
            "xmls",
            nargs="+",
            help="One or more XMLs to work with. Validation will expand any includes so you do not need to add all of those XMLs as arguments",
        )


def main() -> int:
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    MavlibgenRunner.add_args(parser)
    args = parser.parse_args()
    runner = MavlibgenRunner(mavlink_xmls=args.xmls, config_file=args.config_file)
    if runner.run():
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
