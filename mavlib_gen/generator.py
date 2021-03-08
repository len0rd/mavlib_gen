################################################################################
# \file generator
#
# top-level generator API
#
# Copyright (c) 2021 len0rd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################
import os, errno
import logging
import validator

class MessageDefinition(object):
    """Model class representing a single message definition XML"""

    def __init__(self, filename):
        # verify the file exists
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        self.filename = filename



def generate(xmls, output_lang, output_location):
    """
    Validate the provided xml(s) and generate into MAVLink code of output_lang in output_location
    @param xmls
        String list of filepaths to mavlink message definition xmls to generate messages from
    """
    if not isinstance(xmls, list):
        xmls = [xmls]

    validator.validate(xmls)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    generate('common.xml', 'c', 'test/')
