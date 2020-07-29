import json
import logging
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from os.path import join

import click
from click.testing import CliRunner

from tests.base import CapturingTestCase as TestCase, assets, main, copy_of_directory # pylint: disable=import-error, no-name-in-module
from tests.data import DummyProcessor, DUMMY_TOOL

from ocrd import Resolver
from ocrd.decorators import (
    ocrd_cli_options,
    ocrd_loglevel,
    ocrd_cli_wrap_processor,
)    # pylint: disable=protected-access
from ocrd_utils import initLogging, pushd_popd, VERSION as OCRD_VERSION

@click.command()
@ocrd_cli_options
def cli_with_ocrd_cli_options(*args, **kwargs):      # pylint: disable=unused-argument
    pass

@click.command()
@ocrd_cli_options
def cli_param_dumper(*args, **kwargs):      # pylint: disable=unused-argument
    print(json.dumps(kwargs['parameter']))

@click.command()
@ocrd_loglevel
def cli_with_ocrd_loglevel(*args, **kwargs):         # pylint: disable=unused-argument
    pass

@click.command()
@ocrd_cli_options
def cli_dummy_processor(*args, **kwargs):
    return ocrd_cli_wrap_processor(DummyProcessor, *args, **kwargs)

DEFAULT_IN_OUT = ('-I', 'OCR-D-IMG', '-O', 'OUTPUT')

class TestDecorators(TestCase):

    def setUp(self):
        initLogging()
        self.runner = CliRunner()

    def test_minimal(self):
        exit_code, out, err = self.invoke_cli(cli_with_ocrd_cli_options, ['-l', 'DEBUG'])
        print(out, err)
        self.assertEqual(exit_code, 0)

    def test_loglevel_invalid(self):
        result = self.runner.invoke(cli_with_ocrd_loglevel, ['--log-level', 'foo'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('invalid choice: foo', result.output)

    def test_loglevel_override(self):
        self.assertEqual(logging.getLogger('').getEffectiveLevel(), logging.INFO)
        self.assertEqual(logging.getLogger('PIL').getEffectiveLevel(), logging.INFO)
        result = self.runner.invoke(cli_with_ocrd_loglevel, ['--log-level', 'DEBUG'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(logging.getLogger('PIL').getEffectiveLevel(), logging.DEBUG)
        initLogging()

    def test_processor_no_mets(self):
        """
        https://github.com/OCR-D/spec/pull/156
        """
        with TemporaryDirectory() as tempdir:
            with pushd_popd(tempdir):
                _, out_help, _ = self.invoke_cli(cli_dummy_processor, ['--help'])
                exit_code, out_none, _ = self.invoke_cli(cli_dummy_processor, [])
                self.assertEqual(exit_code, 1)
                self.assertEqual(out_help, out_none)

    def test_processor_dump_json(self):
        exit_code, out, err = self.invoke_cli(cli_dummy_processor, ['--dump-json'])
        print("exit_code=%s\nout=%s\nerr=%s" % (exit_code, out, err))
        self.assertEqual(exit_code, 0)

    def test_processor_version(self):
        result = self.runner.invoke(cli_dummy_processor, ['--version'])
        print(result)
        self.assertEqual(result.output, 'Version 0.0.1, ocrd/core %s\n' % OCRD_VERSION)
        self.assertEqual(result.exit_code, 0)

    # XXX cannot be tested in this way because logging is reused and not part of output
    #  def test_processor_non_existing_mets(self):
    #      result = self.runner.invoke(cli_dummy_processor, ['--mets', 'file:///does/not/exist.xml'])
    #      #  self.assertIn('File does not exist: file:///does/not/exist.xml', result.output)
    #      self.assertEqual(result.exit_code, 1)

    def test_processor_run(self):
        with copy_of_directory(assets.path_to('SBB0000F29300010000/data')) as tempdir:
            with pushd_popd(tempdir):
                exit_code, out, err = self.invoke_cli(cli_dummy_processor, ['-p', '{"baz": "forty-two"}', '--mets', 'mets.xml', *DEFAULT_IN_OUT])
                self.assertEqual(exit_code, 0)

    def test_param_merging(self):
        json1 = '{"foo": 23, "bar": 100}'
        json2 = '{"foo": 42}'
        _, out, _ = self.invoke_cli(cli_param_dumper, [*DEFAULT_IN_OUT, '-p', json1, '-p', json2])
        try:
            self.assertEqual(out, '{"foo": 42, "bar": 100}\n')
        except AssertionError:
            self.assertEqual(out, '{"bar": 100, "foo": 42}\n')



    @contextmanager
    def _sample_ws_for_overwrite(self):
        resolver = Resolver()
        with TemporaryDirectory() as tempdir:
            ws = resolver.workspace_from_nothing(directory=tempdir)
            ws.add_file('IN-GRP',  pageId='pID1', ID='fID1', mimetype='image/tiff', content='CONTENT', local_filename=join(tempdir, 'ID1.tif'))
            ws.add_file('OUT-GRP', pageId='pID2', ID='fID2', mimetype='image/tiff', content='CONTENT', local_filename=join(tempdir, 'ID2.tif'))
            ws.add_file('OUT-GRP', pageId='pID3', ID='fID3', mimetype='image/tiff', content='CONTENT', local_filename=join(tempdir, 'ID3.tif'))
            ws.add_file('OUT-GRP', pageId='pID4', ID='fID4', mimetype='image/tiff', content='CONTENT', local_filename=join(tempdir, 'ID4.tif'))
            ws.save_mets()
            yield ws

    def test_overwrite_fail(self):
        with self._sample_ws_for_overwrite() as ws:
            with self.assertRaisesRegex(Exception, 'already in METS'):
                ocrd_cli_wrap_processor(
                    DummyProcessor,
                    ocrd_tool=DUMMY_TOOL,
                    mets=ws.mets_target,
                    input_file_grp='IN-GRP',
                    output_file_grp='OUT-GRP',
                )
            # with overwrite, it shouldn't fail
            ocrd_cli_wrap_processor(
                DummyProcessor,
                ocrd_tool=DUMMY_TOOL,
                mets=ws.mets_target,
                input_file_grp='IN-GRP',
                output_file_grp='OUT-GRP',
                overwrite=True
            )

    # XXX We cannot currently pre-emptively delete files because #505
    # def test_overwrite_group(self):
    #     with self._sample_ws_for_overwrite() as ws:
    #         self.assertTrue(exists(join(ws.directory, 'ID1.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID2.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID3.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID4.tif')), 'files exist')
    #         ocrd_cli_wrap_processor(
    #             DummyProcessor,
    #             ocrd_tool=DUMMY_TOOL,
    #             mets=ws.mets_target,
    #             parameter={"foo": 42},
    #             input_file_grp='IN-GRP',
    #             output_file_grp='OUT-GRP',
    #             overwrite=True,
    #         )
    #         self.assertTrue(exists(join(ws.directory, 'ID1.tif')), 'files exist')
    #         # self.assertFalse(exists(join(ws.directory, 'ID2.tif')), 'files deleted')
    #         # self.assertFalse(exists(join(ws.directory, 'ID3.tif')), 'files deleted')
    #         # self.assertFalse(exists(join(ws.directory, 'ID4.tif')), 'files deleted')

    # XXX We cannot currently pre-emptively delete files because #505
    # as it is the test therefore makes no sense
    # def test_overwrite_group_page_id(self):
    #     with self._sample_ws_for_overwrite() as ws:
    #         self.assertTrue(exists(join(ws.directory, 'ID1.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID2.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID3.tif')), 'files exist')
    #         self.assertTrue(exists(join(ws.directory, 'ID4.tif')), 'files exist')
    #         ocrd_cli_wrap_processor(
    #             DummyProcessor,
    #             ocrd_tool=DUMMY_TOOL,
    #             mets=ws.mets_target,
    #             parameter={"foo": 42},
    #             input_file_grp='IN-GRP',
    #             output_file_grp='OUT-GRP',
    #             overwrite=True,
    #             page_id='pID2,pID4'
    #         )
    #         self.assertTrue(exists(join(ws.directory, 'ID1.tif')), 'files exist')
    #         self.assertFalse(exists(join(ws.directory, 'ID2.tif')), 'files deleted')
    #         self.assertTrue(exists(join(ws.directory, 'ID3.tif')), 'files exist')
    #         self.assertFalse(exists(join(ws.directory, 'ID4.tif')), 'files deleted')

    def test_parameter_override_basic(self):
        with copy_of_directory(assets.path_to('SBB0000F29300010000/data')) as tempdir:
            with pushd_popd(tempdir):
                result = self.runner.invoke(cli_dummy_processor, [
                    '-p', '{"baz": "forty-two"}',
                    '-P', 'baz', 'one',
                    '-P', 'baz', 'two',
                    *DEFAULT_IN_OUT
                ])
                print(result)
                self.assertEqual(result.stdout, '{"baz": "two"}\n')

    def test_parameter_override_wo_param(self):
        with copy_of_directory(assets.path_to('SBB0000F29300010000/data')) as tempdir:
            with pushd_popd(tempdir):
                result = self.runner.invoke(cli_dummy_processor, [
                    '-P', 'baz', 'two',
                    *DEFAULT_IN_OUT
                ])
                print(result)
                self.assertEqual(result.stdout, '{"baz": "two"}\n')

if __name__ == '__main__':
    main(__file__)
