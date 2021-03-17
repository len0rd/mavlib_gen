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
import os, errno
import logging
from .validator import MavlinkXmlValidator

def generate(xmls, output_lang, output_location):
    """
    Validate the provided xml(s) and generate into MAVLink code of output_lang in output_location
    @param xmls
        String list of filepaths to mavlink message definition xmls to generate messages from
    """
    if not isinstance(xmls, list):
        xmls = [xmls]

    validator = MavlinkXmlValidator()

    xml_dicts = validator.validate(xmls)
    if xml_dicts is None:
        print("Failed!")
        return False # failed to generate

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # generate('common.xml', 'c', 'test/')
    generate('simple_msg.xml', 'c', 'test/')
