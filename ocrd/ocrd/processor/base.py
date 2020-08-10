"""
Processor base class and helper functions
"""

__all__ = [
    'Processor',
    'generate_processor_help',
    'run_cli',
    'run_processo'
]

from os import makedirs
from os.path import exists, isdir, join
from pkg_resources import resource_filename
from shutil import copyfileobj
import json
import os
import re

import requests

from ocrd_utils import (
    getLogger,
    VERSION as OCRD_VERSION,
    MIMETYPE_PAGE,
    list_resource_candidates,
    list_all_resources,
    XDG_CACHE_HOME
)
from ocrd_validators import ParameterValidator

# XXX imports must remain for backwards-compatibilty
from .helpers import run_cli, run_processor, generate_processor_help # pylint: disable=unused-import

log = getLogger('ocrd.processor')

class Processor():
    """
    A processor runs an algorithm based on the workspace, the mets.xml in the
    workspace (and the input files defined therein) as well as optional
    parameter.
    """

    def __init__(
            self,
            workspace,
            ocrd_tool=None,
            parameter=None,
            # TODO OCR-D/core#274
            # input_file_grp=None,
            # output_file_grp=None,
            input_file_grp="INPUT",
            output_file_grp="OUTPUT",
            page_id=None,
            show_help=False,
            show_version=False,
            dump_json=False,
            version=None
    ):
        if parameter is None:
            parameter = {}
        if dump_json:
            print(json.dumps(ocrd_tool, indent=True))
            return
        self.ocrd_tool = ocrd_tool
        if show_help:
            self.show_help()
            return
        self.version = version
        if show_version:
            self.show_version()
            return
        self.workspace = workspace
        # FIXME HACK would be better to use pushd_popd(self.workspace.directory)
        # but there is no way to do that in process here since it's an
        # overridden method. chdir is almost always an anti-pattern.
        if self.workspace:
            os.chdir(self.workspace.directory)
        self.input_file_grp = input_file_grp
        self.output_file_grp = output_file_grp
        self.page_id = None if page_id == [] or page_id is None else page_id
        parameterValidator = ParameterValidator(ocrd_tool)
        report = parameterValidator.validate(parameter)
        if not report.is_valid:
            raise Exception("Invalid parameters %s" % report.errors)
        self.parameter = parameter

    def show_help(self):
        print(generate_processor_help(self.ocrd_tool))

    def show_version(self):
        print("Version %s, ocrd/core %s" % (self.version, OCRD_VERSION))

    def verify(self):
        """
        Verify that the input fulfills the processor's requirements.
        """
        return True

    def process(self):
        """
        Process the workspace
        """
        raise Exception("Must be implemented")

    def resolve_resource(self, parameter_name, val):
        """
        Resolve a resource name with the algorithm in
        https://ocr-d.de/en/spec/ocrd_tool#file-parameters

        Args:
            parameter_name (string): name of parameter to resolve resource for
            val (string): resource value to resolve
        """
        executable = self.ocrd_tool['executable']
        try:
            param = self.ocrd_tool['parameter'][parameter_name]
        except KeyError:
            raise ValueError("Parameter '%s' not defined in ocrd-tool.json" % parameter_name)
        if not param['mimetype']:
            raise ValueError("Parameter '%s' is not a file parameter (has no 'mimetype' field)" %
                             parameter_name)
        if val.startswith('http:') or val.startswith('https:'):
            cache_dir = join(XDG_CACHE_HOME, executable)
            cache_key = re.sub('[^A-Za-z0-9]', '', val)
            cache_fpath = join(cache_dir, cache_key)
            # TODO Proper caching (make head request for size, If-Modified etc)
            if not exists(cache_fpath):
                if not isdir(cache_dir):
                    makedirs(cache_dir)
                with requests.get(val, stream=True) as r:
                    with open(cache_fpath, 'wb') as f:
                        copyfileobj(r.raw, f)
            return cache_fpath
        ret = next([cand for cand in list_resource_candidates(executable, val) if exists(cand)])
        if ret:
            return ret
        bundled_fpath = resource_filename(__name__, val)
        if exists(bundled_fpath):
            return bundled_fpath
        raise FileNotFoundError("Could not resolve '%s' file parameter value '%s'" %
                                (parameter_name, val))

    def list_all_resources(self):
        """
        List all resources found in the filesystem
        """
        return list_all_resources(self.ocrd_tool['executable'])

    @property
    def input_files(self):
        """
        List the input files.

        - If there's a PAGE-XML for the page, take it (and forget about all
          other files for that page)
        - Else if there's only one image, take it (and forget about all other
          files for that page)
        - Otherwise raise an error (complaining that only PAGE-XML warrants

          having multiple images for a single page)
        (https://github.com/cisocrgroup/ocrd_cis/pull/57#issuecomment-656336593)
        """
        ret = self.workspace.mets.find_files(
            fileGrp=self.input_file_grp, pageId=self.page_id, mimetype=MIMETYPE_PAGE)
        if ret:
            return ret
        ret = self.workspace.mets.find_files(
            fileGrp=self.input_file_grp, pageId=self.page_id, mimetype="//image/.*")
        if self.page_id and len(ret) > 1:
            raise ValueError("No PAGE-XML %s in fileGrp '%s' but multiple images." % (
                "for page '%s'" % self.page_id if self.page_id else '',
                self.input_file_grp
                ))
        return ret
