################################################################################
# \file generator
#
# top-level generator api
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import logging
from pathlib import Path
from typing import List, Dict
from .validator import MavlinkXmlValidator
from .lang_generators.generator_python import PythonLangGenerator
from .lang_generators.generator_graphviz import GraphvizLangGenerator
from schema import Optional, Literal, Or

# from .lang_generators.generator_base import AbstractLangGenerator

log = logging.getLogger(__name__)

GENERATOR_MAP = {
    "python": PythonLangGenerator,
    "graphviz": GraphvizLangGenerator,
}


def yaml_schema() -> Dict[any, any]:
    """
    Get YAML schema for the mavgen generation component. Includes schema for all language generators
    """
    lang_schemas = {}
    for lang_name, lang_cls in GENERATOR_MAP.items():
        lang_schemas[
            Optional(Literal(lang_name, description=f"generate Mavlink in {lang_name}"))
        ] = Or(lang_cls.config_schema(), None)
    return {
        Optional(
            Literal("generate", description="Root element for configuring Mavlink generation")
        ): lang_schemas
    }


def generate(xmls: List[str], output_lang: str, output_location: str) -> bool:
    """
    Validate the provided xml(s) and generate into MAVLink code of output_lang in output_location
    @param xmls
        String list of filepaths to mavlink message definition xmls to generate messages from
    """

    # input validation
    output_lang = output_lang.lower()
    if output_lang not in GENERATOR_MAP:
        log.fatal(f"Desired output language '{output_lang}' not recognized")
        return False

    if xmls is None:
        log.fatal("No valid Mavlink xml paths provided")
        return False

    if not isinstance(xmls, list):
        xmls = [xmls]

    validator = MavlinkXmlValidator()

    validated_xmls = validator.validate(xmls)
    if validated_xmls is None:
        return False  # failed to validate

    # generate output
    lang_generator = GENERATOR_MAP[output_lang]()
    outdir = Path(output_location)
    return lang_generator.generate(validated_xmls, outdir)
