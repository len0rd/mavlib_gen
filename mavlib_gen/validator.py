################################################################################
# \file validator
#
# Methods and helpers for ensuring XML files are valid Mavlink message
# definitions
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
import os, logging
import xmlschema

log = logging.getLogger(__name__)

def report_schama_validation_error(validation_exception, xml_file):
    """Helper method to report validation errors in a useful way that I like"""
    log.error("Validation of message definition file '{}' failed!".format(os.path.relpath(xml_file)))
    reason = ""
    if validation_exception.reason is not None:
        reason += "Reason: {}".format(validation_exception.reason)
    if validation_exception.path is not None:
        reason += " At path '{}':".format(validation_exception.path)
    log.error(reason)
    if xmlschema.etree.is_etree_element(validation_exception.elem):
        log.error("\n{}".format(xmlschema.etree.etree_tostring(validation_exception.elem, validation_exception.namespaces, '', 5)))

def validate_single_xml(xml):
    """Validate an individual xml. Note if messages are generated from multiple XMLs, the validation will also be performed on the 'combined' xml"""
    # start by validating each xml individually
    script_dir = os.path.dirname(__file__)
    base_url = os.path.abspath(os.path.join(script_dir, 'schema'))
    schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'), base_url=base_url)

    try:
        schema.validate(xml)
    except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
        report_schama_validation_error(e, xml)
        quit()
    log.debug("{} passed validation".format(xml))


# def validate(xmls):
