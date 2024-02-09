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
from .lang_generators.generator_base import AbstractLangGenerator
from .lang_generators.generator_python import PythonLangGenerator
from .lang_generators.generator_graphviz import GraphvizLangGenerator
from .model.mavlink_xml import MavlinkXmlFile
from schema import Optional, Literal, Or
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

GENERATOR_MAP = {
    "python": PythonLangGenerator,
    "graphviz": GraphvizLangGenerator,
}


@dataclass
class MavlibGenerator:
    """
    Primary generation class. Generates mavlib code using validated mavlink model objects and
    user configuration. Exists as a intermediary between yaml configuration and the language
    generators
    """

    # Output directory for generated files
    outdir: str = ""
    generators: List[AbstractLangGenerator] = field(default_factory=list)

    @classmethod
    def yaml_schema() -> Dict[any, any]:
        """
        Get YAML schema for the mavgen generation component. Includes schema for all language
        generators
        """
        generate_options = {}
        generate_options[
            Literal(
                "outdir",
                description="Output directory for generated files (will be created if necessary)."
                + "Relative to the configuration file",
            )
        ] = str
        # append each possible generation language as an option
        for lang_name, lang_cls in GENERATOR_MAP.items():
            generate_options[
                Optional(Literal(lang_name, description=f"generate Mavlink in {lang_name}"))
            ] = Or(lang_cls.config_schema(), None)
        return {
            Optional(
                Literal("generate", description="Root element for configuring Mavlink generation")
            ): generate_options
        }

    @classmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        print(conf)
        gen = MavlibGenerator()
        for k in conf.keys():
            if k in GENERATOR_MAP.keys():
                value = conf.get(k, {})
                value = {} if value is None else value
                gen.generators.append(GENERATOR_MAP[k].from_config(value))
            elif k == "outdir":
                gen.outdir = conf.get(k, "")
        return gen

    def __repr__(self) -> str:
        return f"MavlibGenerator(\n\toutdir: {self.outdir},\n\tgenerators: {self.generators}\n)"

    def generate(self, mav_xmls: Dict[str, MavlinkXmlFile]) -> bool:
        result = True
        for generator in self.generators:
            out_path = Path(self.outdir).resolve() / generator.lang_name()
            result = result and generator.generate(mav_xmls, out_path)
        return result

    def generate_one(self, mav_xmls: Dict[str, MavlinkXmlFile], output_language: str) -> bool:
        output_language = output_language.lower()
        if output_language not in GENERATOR_MAP:
            log.fatal(f"Desired output language '{output_language}' not recognized")
            return False
        lang_generator = GENERATOR_MAP[output_language]()
        return lang_generator.generate(mav_xmls, Path(self.outdir))
