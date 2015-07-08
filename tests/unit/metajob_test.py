# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Mike Place <mp@saltstack.com>`

    tests.metajob_test
    ~~~~~~~~~~~~~~~~~~
'''

# Import Salt libs
from __future__ import absolute_import

import salt.config
import salt.master
import salt.daemons.masterapi

# Import Salt testing libs
import integration
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import MagicMock, NO_MOCK, NO_MOCK_REASON, patch

# Import python libs
import logging

log = logging.getLogger(__name__)

ensure_in_syspath('../')



class MetaJobConfigTestCase(integration.ModuleCase):
    '''
    Test various configuration varieties and ensure
    appropriate errors are thrown on invalid configurations
    '''

    def test_valid_config(self):
        '''
        Ensure that a valid config passes the validation process
        '''
        valid_config = {'master_tx': {'test.echo': 'fakearg1'},
                        'minion_tx': {'test.echo': 'fakearg2'}
                        }

        self.assertEqual(salt.config._validate_job_meta(valid_config), valid_config)

    def test_invalid_hook(self):
        '''
        Ensure that an appropriate warning is raised if a daemon
        is started with an invalid hook specified.
        '''
        invalid_config = {'not_a_valid_hook': {'test.echo': 'fakearg1'}}

        self.assertFalse(salt.config._validate_job_meta(invalid_config))

    def test_malformed_exec(self):
        '''
        Ensure that malformed execution modules, such as strs
        that are not dot-delimited raise a warning
        '''
        invalid_hook = {'master_tx': {'not_a_valid_exc': 'fakearg1'}}
        self.assertFalse(salt.config._validate_job_meta(invalid_hook))

    def test_master_opts(self):
        '''
        Ensure that the job meta dictionary gets stuffed into
        master_opts, regardless of whether or not the entire
        master_opts dict is delivered
        '''
        opts = dict(self.get_config('master'))
        remote_funcs = salt.daemons.masterapi.RemoteFuncs(opts)
        self.assertIn('job_meta', remote_funcs._master_opts({}))


@skipIf(NO_MOCK, NO_MOCK_REASON)
class MetaJobHooksTestCase(integration.ModuleCase):
    '''
    Test various job hooks to ensure that they fire
    when appropriate
    '''
    def test_pub_hook_fire(self, *args, **kwargs):
        '''
        Test that the pub hook is fired on master job publication
        '''
        opts = dict(self.get_config('master'))
        opts['job_meta'] = {'master_tx': {'test.echo': 'fakearg1'}}

        opts['client_acl'] = {'plato': ''}
        clear_load = {'fun': 'test.ping',
                      'arg': '',
                      'tgt': '*',
                      'tgt_type': 'glob',
                      'user': 'plato',
                      'key': 'traffic',
                      'jid': '12345',
                      'ret': '',
                     }

        clear_funcs = salt.master.ClearFuncs(opts, {'plato': 'traffic'})

        clear_funcs.event = MagicMock()
        clear_funcs._prep_jid = MagicMock(return_value=str(clear_load['jid']))
        clear_funcs._send_pub = MagicMock()
        clear_funcs.ckminions = MagicMock(return_value=['minion1'])
        clear_funcs.mminion.functions = MagicMock()

        clear_funcs.publish(clear_load)
        clear_funcs.mminion.functions.__getitem__.assert_called_with('test.echo')

        # We'll eventually swing this over to masterapi, so re-test there to prevent
        # future regressions

        clear_load = {'fun': 'test.ping',
                      'arg': '',
                      'tgt': '*',
                      'tgt_type': 'glob',
                      'user': 'plato',
                      'key': 'traffic',
                      'jid': '12345',
                      'ret': '',
                     }

        clear_funcs = salt.daemons.masterapi.LocalFuncs(opts, {'plato': 'traffic'})

        clear_funcs.event = MagicMock()
        clear_funcs.key = {'plato': 'traffic'}
        clear_funcs._prep_jid = MagicMock(return_value=str(clear_load['jid']))
        clear_funcs._send_pub = MagicMock()
        clear_funcs.ckminions = MagicMock(return_value=['minion1'])
        clear_funcs.mminion.functions = MagicMock()

        clear_funcs.publish(clear_load)
        clear_funcs.mminion.functions.__getitem__.assert_called_with('test.echo')

    def test_rec_hook_fire(self):
        '''
        Test that the rec hook is fired on minion job reciept
        '''
        # TODO

    def test_job_start_fire(self):
        '''
        Test that the job_start hook is fired
        '''
        # TODO

    def test_job_finish_fire(self):
        '''
        Test that the job finish hook is fired
        '''
        # TODO

    def test_meta_load(self):
        '''
        Test to ensure that the metadata for a load is written
        on load publication
        '''
        # TODO

    def test_meta_ret(self):
        '''
        Test to ensure that metadata for a return is written out
        '''
        # TODO

    def test_warn_on_unsupported_returner(self):
        '''
        If a returner does not expose an interface for storing metadata
        for a return, then warn cleanly
        '''
        # TODO
