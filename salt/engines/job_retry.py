# -*- coding: utf-8 -*-
'''
An engine that reads messages from the salt event bus and pushes
them onto a logstash endpoint.

.. versionadded: 2015.8.0

:configuration:

    Example configuration

    .. code-block:: yaml

        engines:
          - logstash:
            host: log.my_network.com
            port: 5959
            proto: tcp

:depends: logstash
'''

# Import python libraries
from __future__ import absolute_import, print_function, unicode_literals
import logging

# Import salt libs
import salt.utils.event
import salt.cache

def __virtual__():
    if __opts__['job_retry']:
        return True
    else:
        return False

log = logging.getLogger(__name__)


def start():
    '''
    Listen to salt events and forward them to logstash
    '''
    cache = salt.cache.factory(__opts__)
    mminion = salt.minion.MasterMinion(__opts__)
    client = salt.client.get_local_client(mopts=__opts__)
    if __opts__.get('id').endswith('_master'):
        event_bus = salt.utils.event.get_master_event(
                __opts__,
                __opts__['sock_dir'],
                listen=True)
    log.info('JOB_RETRY_ENGINE_ENABLED')
    while True:
        event = event_bus.get_event()
        print(event)
        if event:
            if event.get('tag') and event.get('tag').endswith('start'):
                log.info('START EVENT DETECTED')
                # Now check the cache system
                jobs = cache.fetch('minions/{0}'.format(event.get('id')), 'enqueued_jobs')
                print('JOBS')
                print(jobs)
                load = mminion.returners['local_cache.get_load'](jobs)
                print(load)
                client.pub(event.get('id'), load['fun'], load['arg'])

