#    Copyright 2014 Rackspace Inc.
#    All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import functools
import json
import logging
import os

from ambariclient.client import Ambari, ENTRY_POINTS
from ambariclient import events, base, models, utils

# TODO: override the logger level somehow
logging.basicConfig(level=logging.CRITICAL)
LOG = logging.getLogger(__name__)


def model_event(event, event_state, obj, **kwargs):
    line_end = "\n" if event_state == events.states.FINISHED else ""
    print "%s %s '%s': %s%s" % (utils.normalize_underscore_case(event),
                           utils.normalize_camel_case(obj.__class__.__name__),
                           obj.identifier, event_state, line_end)


def request_progress(request, **kwargs):
    print "Wait for %s: %.2f%%" % (request.request_context, request.progress_percent)


def request_done(request, **kwargs):
    print "Wait for %s: FINISHED\n" % (request.request_context)


def bootstrap_progress(bootstrap, **kwargs):
    hostnames = [x.host_name for x in bootstrap.hosts]
    print "Wait for Bootstrap Hosts %s: %s" % (hostnames, bootstrap.status)


def bootstrap_done(bootstrap, **kwargs):
    hostnames = [x.host_name for x in bootstrap.hosts]
    print "Wait for Bootstrap Hosts %s: FINISHED\n" % (hostnames)


if os.environ.get('PYTHONSTARTUP', '') == __file__:
    for event in ['create', 'update', 'delete']:
        for event_state in [events.states.STARTED, events.states.FINISHED]:
            callback = functools.partial(model_event, event, event_state)
            events.subscribe(base.Model, event, callback, event_state)

    events.subscribe(models.Request, 'wait', request_progress, events.states.PROGRESS)
    events.subscribe(models.Request, 'wait', request_done, events.states.FINISHED)
    events.subscribe(models.Bootstrap, 'wait', bootstrap_progress, events.states.PROGRESS)
    events.subscribe(models.Bootstrap, 'wait', bootstrap_done, events.states.FINISHED)

    config = {
        "host": "c6401.ambari.apache.org",
        "port": 8080,
        "username": "admin",
        "password": "admin"
    }

    config_path = os.path.expanduser('~/.ambari')
    if os.path.isfile(config_path):
        with open(config_path, 'r') as config_file:
            config.update(json.load(config_file))

    ambari = Ambari(**config)

    def dump_hierarchy(model_class=None, stack=None):
        if stack is None:
            stack = ['ambari']

        if model_class:
            relationships = model_class.relationships
        else:
            relationships = ENTRY_POINTS

        for rel in sorted(relationships.keys()):
            new_stack = list(stack)
            new_stack.append(rel)
            print '.'.join(new_stack)
            rel_model_class = relationships[rel]
            new_stack[-1] = "%s(%s)" % (new_stack[-1], rel_model_class.primary_key)
            print '.'.join(new_stack)
            dump_hierarchy(model_class=rel_model_class, stack=new_stack)


    print "\nAmbari client available as 'ambari'"
    print " - Ambari Server is %s" % ambari.host
    print " - Ambari Version is %s\n" % utils.version_str(ambari.version)
