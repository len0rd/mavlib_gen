################################################################################
# \file message_def_xml
#
# Model object that represents a single message definition xml file
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import os
from typing import List

class MessageDefXml(object):

    def __init__(self, absolute_path, xml_dict):
        """
        Construct a Message Definition xml object. These objects must contain
        their base filename (ie: 'common.xml'), the absolute path to the file
        ('/home/len0rd/common.xml') and their schema-validated xml dictionary
        (as produced by the xmlschema library)
        """
        self.absolute_path = absolute_path
        self.filename = os.path.basename(absolute_path)
        self.xml_dict = xml_dict
        self.dependencies = None

    def set_dependencies(self, deps : List[str]):
        """
        Update this objects list of dependencies.
        The dependency list is a list of all xml message definition files
        this xml directly or indirectly includes
        """
        self.dependencies = deps
