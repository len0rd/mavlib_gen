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
from mavlib_gen.model.mavlink_xml import MavlinkXmlFile
from typing import Dict
from pathlib import Path
from dataclasses import dataclass


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

    @classmethod
    @abstractmethod
    def config_schema(cls) -> Dict[any, any]:
        """
        Return a python schema dictionary of configuration options for this generator. This will be
        used to validate a user-provided yaml configuration file before running any generation

        In general your schema should:
            - make all configuration options optional with sensible defaults in place. The top-level
              schema builder assumes a generator can be provided with no options and still function
            - include a description for user documentation
        """
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        """
        Creates an instance of this generator from the provided dictionary of configuration options
        Options in this dictionary are guaranteed to comply to the schema provided by
        @ref config_schema

        Why do it this way instead of using ruamels to_yaml/from_yaml setup?
        - IMO allows simpler/more readable yaml on the user-side (tags not necessary)
        - Want to enforce using @ref config_schema since it can be used for easy documentation of
          yaml configuration

        Maybe some of these dont outweigh the costs of having to implement this for every generator?
            idk, revisit in the future. lets just get something working for now
            There's probably better ways to do this.. generating schema from dataclass
        """
        pass

    @abstractmethod
    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: Path) -> bool:
        """
        Top-level generate method. Generates mavlink messages in the
        implemented language from the provided dialect file
        """
        pass


@dataclass
class OneShotGeneratorWrapper:
    """
    Wrapper that can be used by AbstractLangGenerators to give them a function signature
    similar to MavlibGenerator.generate_all. This lets someone provide specific generator
    instantiations to MavlibgenRunner (by providing it on construction). This is convenient
    for unit testing so the yaml config interface can be bypassed

    Attributes:
        generator_impl: A concrete AbstractLangGenerator implementation instantiation or anything
            that implements a similar generate method to AbstractLangGenerator.generate
        output_dir (str): Path to the output directory to place generated files
    """

    generator_impl: any
    output_dir: str = ""

    def generate_all(self, mav_xmls: Dict[str, MavlinkXmlFile]) -> bool:
        return self.generator_impl.generate(mav_xmls, self.output_dir)
