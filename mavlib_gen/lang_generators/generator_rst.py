################################################################################
# \file generator_rst
#
# ReStructuredText (rst) mavlink message doc generator
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from mavlib_gen.lang_generators.generator_base import AbstractLangGenerator
from pathlib import Path
from dataclasses import dataclass
from typing import Dict
from mavlib_gen.model.mavlink_xml import MavlinkXmlFile


@dataclass
class RstLangGenerator(AbstractLangGenerator):
    """
    MavlibGen RST generator

    Attributes
    """


    def lang_name(self) -> str:
        return "rst"

    @classmethod
    def config_schema(cls) -> Dict[any,any]:
        return {}

    @classmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        return RstLangGenerator()


    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: Path) -> bool:
        return False
