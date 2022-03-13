################################################################################
# \file generator_base
#
# Abstract Base Class that should be used by all language generators
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from abc import ABC, abstractmethod
from ..model.mavlink_xml import MavlinkXmlFile
from typing import Dict


class AbstractLangGenerator(ABC):
    """
    Abstract class for a specific language generator.
    The generator for each language (C, C++, etc) should
    implement this class
    """

    @abstractmethod
    def lang_name(self) -> str:
        """
        Returns the name of the language this generator handles ie: 'c'
        """
        pass

    @abstractmethod
    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: str) -> bool:
        """
        Top-level generate method. Generates mavlink messages in the
        implemented language from the provided dialect file
        """
        pass
