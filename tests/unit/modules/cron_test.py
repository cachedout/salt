# -*- coding: utf-8 -*-
'''
    :codauthor: :email:`Mike Place <mp@saltstack.com>`
'''

# Import Salt Testing libs
from salttesting import TestCase, skipIf
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import MagicMock, patch, call, DEFAULT

import copy

ensure_in_syspath('../../')

from salt.modules import cron

STUB_USER = 'root'
STUB_PATH = '/tmp'

STUB_CRON_TIMESTAMP = {'minute': '1',
                       'hour': '2',
                       'daymonth': '3',
                       'month': '4',
                       'dayweek': '5'}

STUB_SIMPLE_RAW_CRON = '5 0 * * * /tmp/no_script.sh'
STUB_SIMPLE_CRON_DICT = {'pre': ['5 0 * * * /tmp/pre_script.sh'], 'crons': [
    {'cmd': '/tmp/no_script.sh', 'spec': None, 'minute': '5', 'hour': '0', 'daymonth': '*', 'month': '*',
     'dayweek': '*', 'comment': ''}], 'env': [], 'special': []}

__grains__ = {}


class CronTestCase(TestCase):
    def test__needs_change(self):
        self.assertTrue(cron._needs_change(True, False))

    def test__needs_change_random(self):
        '''
        Assert that if the new var is 'random' and old is '* that we return True
        '''
        self.assertTrue(cron._needs_change('*', 'random'))

    ## Still trying to figure this one out.
    # def test__render_tab(self):
    #     pass

    def test__get_cron_cmdstr_solaris(self):
        cron.__grains__ = __grains__
        with patch.dict(cron.__grains__, {'os': 'Solaris'}):
            self.assertEqual('su - root -c "crontab /tmp"',
                             cron._get_cron_cmdstr(STUB_USER, STUB_PATH))

    def test__get_cron_cmdstr(self):
        cron.__grains__ = __grains__
        with patch.dict(cron.__grains__, {'os': None}):
            self.assertEqual('crontab -u root /tmp',
                             cron._get_cron_cmdstr(STUB_USER, STUB_PATH))

    def test__date_time_match(self):
        '''
        Passes if a match is found on all elements. Note the conversions to strings here!
        :return:
        '''
        self.assertTrue(cron._date_time_match(STUB_CRON_TIMESTAMP,
                                              minute=STUB_CRON_TIMESTAMP['minute'],
                                              hour=STUB_CRON_TIMESTAMP['hour'],
                                              daymonth=STUB_CRON_TIMESTAMP['daymonth'],
                                              dayweek=STUB_CRON_TIMESTAMP['dayweek']
        ))

    @patch('salt.modules.cron.raw_cron', new=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_RAW_CRON)))
    def test_list_tab(self):
        self.assertDictEqual({'pre': ['5 0 * * * /tmp/no_script.sh'], 'crons': [], 'env': [], 'special': []},
                             cron.list_tab('DUMMY_USER'))

    @patch.multiple('salt.modules.cron', _write_cron_lines=DEFAULT,
                    list_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)),
                    _render_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)))
    def test_set_special(self, _write_cron_lines):
        user = 'DUMMY_USER'
        expected_write_call = call(user, STUB_SIMPLE_CRON_DICT)
        cron.set_special(user, '@hourly', 'echo Hi!')
        _write_cron_lines.assert_has_calls(expected_write_call)

    def test__get_cron_date_time(self):
        ret = cron._get_cron_date_time(minute=STUB_CRON_TIMESTAMP['minute'],
                                       hour=STUB_CRON_TIMESTAMP['hour'],
                                       daymonth=STUB_CRON_TIMESTAMP['daymonth'],
                                       dayweek=STUB_CRON_TIMESTAMP['dayweek'],
                                       month=STUB_CRON_TIMESTAMP['month'])
        self.assertDictEqual(ret, STUB_CRON_TIMESTAMP)

    ## FIXME: More sophisticated _get_cron_date_time checks should be added here.

    @patch.multiple('salt.modules.cron', _write_cron_lines=DEFAULT, raw_cron=DEFAULT)
    def test_set_job(self, raw_cron, _write_cron_lines):
        cron.__grains__ = __grains__
        with patch.dict(cron.__grains__, {'os': None}):
            cron.set_job('DUMMY_USER', 1, 2, 3, 4, 5,
                         '/bin/echo NOT A DROID',
                         'WERE YOU LOOKING FOR ME?')
            expected_call = call('DUMMY_USER',
                                 ['5 0 * * * /tmp/no_script.sh\n',
                                  '# Lines below here are managed by Salt, do not edit\n',
                                  '# WERE YOU LOOKING FOR ME?\n',
                                  '1 2 3 4 5 /bin/echo NOT A DROID\n'])
            _write_cron_lines.call_args.assert_called_with(expected_call)

    @patch.multiple('salt.modules.cron', _write_cron_lines=MagicMock(return_value={'retcode': False}),
                    raw_cron=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_RAW_CRON)))
    def test_rm_job_is_absent(self):
        with patch.dict(cron.__grains__, {'os': None}):
            ret = cron.rm_job('DUMMY_USER', '/bin/echo NOT A DROID', 1, 2, 3, 4, 5)
            self.assertEqual('absent', ret)

    @patch.multiple('salt.modules.cron', _write_cron_lines=MagicMock(return_value={'retcode': False}),
                    list_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)))
    def test_rm_job(self):
        ret = cron.rm_job(None, '/tmp/no_script.sh')
        self.assertEqual(ret, 'removed')

    @patch.multiple('salt.modules.cron', _write_cron_lines=MagicMock(return_value={'retcode': False}),
                    list_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)))
    def test_set_env(self):
        with patch.dict(cron.__grains__, {'os': None}):
            user = 'DUMMY_USER'
            cron.set_env(user, 'MAILTO', 'nobody@saltstack.com')
            expected_call_arg = ['5 0 * * * /tmp/pre_script.sh\n',
                                 '# Lines below here are managed by Salt, do not edit\n',
                                 'MAILTO=nobody@saltstack.com\n', '# \n', '5 0 * * * /tmp/no_script.sh\n']
            cron._write_cron_lines.assert_call_has(expected_call_arg)

    @patch.multiple('salt.modules.cron', _write_cron_lines=MagicMock(return_value={'retcode': False}),
                    list_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)),
                    )
    def test_set_env_update(self):
        ## WARNING: Potential dependency on rm_env here.

        test_env = 'TEST_ENV'
        test_user = 'DUMMY_USER'
        expected_call_arg = ['5 0 * * * /tmp/pre_script.sh\n',
                             '# Lines below here are managed by Salt, do not edit\n',
                             'MAILTO=nobody@saltstack.com\n', '# \n', '5 0 * * * /tmp/no_script.sh\n']
        cron.list_tab.return_value['env'] = [{'name': 'TEST_ENV', 'value': None}]
        with patch.dict(cron.__grains__, {'os': None}):
            ret = cron.set_env(test_user, test_env, 'NEW_VALUE')
        cron._write_cron_lines.assert_call_has(expected_call_arg)
        self.assertEqual('updated', ret)

    @patch.multiple('salt.modules.cron', _write_cron_lines=MagicMock(return_value={'retcode': False}),
                    list_tab=MagicMock(return_value=copy.deepcopy(STUB_SIMPLE_CRON_DICT)),
                    )
    def test_rm_env(self):

        test_env = 'TEST_ENV'
        test_user = 'DUMMY_USER'

        cron.list_tab.return_value['env'] = [{'name': 'TEST_ENV', 'value': None}]

        with patch.dict(cron.__grains__, {'os': None}):
            ret = cron.rm_env(test_user, test_env)
        self.assertEqual('removed', ret)
