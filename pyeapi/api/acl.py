#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""Module for working with EOS access control list resources

This module provides an implementation for configuring and managing access
access control lists on Arista EOS nodes.  Access control lists can be
specified as either 'standard' or 'extended' ACLs.  This module provides the
following class implementations:

    * Acls -- The top-level class used to manage both standard and extended
        access control lists in EOS
    * StandardAcls -- Class that manages the set of standard ACLs
    * ExtendedAcls -- Class that manages the set of extended ACLs

"""
import re

import netaddr

from pyeapi.api import EntityCollection

STANDARD_ACL_NAME = re.compile(r'^Standard\sIP\sAccess\sList\s(\S+)$\n', re.M)

def mask_to_prefixlen(mask):
    """Converts a subnet mask from dotted decimal to bit length

    Args:
        mask (str): The dotted decimal subnet mask to convert

    Returns:
        str: The subnet mask as a valid prefix length
    """
    mask = mask or '255.255.255.255'
    return netaddr.IPAddress(mask).netmask_bits()


def prefixlen_to_mask(prefixlen):
    """Converts a prefix length to a dotted decimal subnet mask

    Args:
        prefixlen (str): The prefix length value to convert

    Returns:
        str: The subt mask as a dotted decimal string
    """
    prefixlen = prefixlen or '32'
    addr = '0.0.0.0/%s' % prefixlen
    return str(netaddr.IPNetwork(addr).netmask)


def parse_acls(config):
    """Takes the output of 'show ip access-lists' and breaks the configuration
    into a list where each entry is a dictionary with keys 'name' and 'text'.
    The 'name' key holds the ACL name and the 'text' key holds the ACL
    configuration text.
    """
    blocks = list()
    for acl in STANDARD_ACL_NAME.finditer(config):
        name = acl.group(1)
        block_start, line_end = acl.regs[0]

        match = re.search(r'^$', config[line_end:], re.M)
        _, block_end = match.regs[0]
        block_end = line_end + block_end

        text = config[block_start:block_end]
        blocks.append(dict(name=name, text=text))

    return blocks


class StandardAcls(EntityCollection):

    entry_re = re.compile(r'(\d+)'
                          r'(?: ([p|d]\w+))'
                          r'(?: (any))?'
                          r'(?: (host))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?:/([0-9]{1,2}))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?: (log))?')

    def get(self, name):
        commands = list()
        commands.append('show ip access-lists %s' % name)
        try:
            result = self.node.enable(commands, encoding='text')
            config = result[0]['result']['output']
        except:
            return None

        if not config:
            return None

        resource = dict(name=name, type='standard')
        resource.update(self._parse_entries(config))
        return resource

    def getall(self):
        commands = list()
        commands.append('show ip access-lists')
        try:
            result = self.node.enable(commands, encoding='text')
            config = result[0]['result']['output']
        except:
            return None

        if not config:
            return None

        acls = parse_acls(config)
        resources = dict()

        for acl in acls:
            resources[acl['name']] = self._parse_entries(acl['text'])
        return resources

    def _parse_entries(self, config):
        entries = dict()
        for item in re.finditer(r'\d+ [p|d].*$', config, re.M):
            match = self.entry_re.match(item.group(0))
            if match:
                (seq, act, anyip, host, ip, mlen, mask, log) = match.groups()
                entry = dict()
                entry['action'] = act
                entry['srcaddr'] = ip or '0.0.0.0'
                entry['srclen'] = mlen or mask_to_prefixlen(mask)
                entry['log'] = log is not None
                entries[seq] = entry
        return dict(entries=entries)

    def create(self, name):
        return self.configure('ip access-list standard %s' % name)

    def delete(self, name):
        return self.configure('no ip access-list standard %s' % name)

    def default(self, name):
        return self.configure('default ip access-list standard %s' % name)

    def update_entry(self, name, seqno, action, addr, prefixlen, log=False):
        cmds = ['ip access-list standard %s' % name]
        cmds.append('no %s' % seqno)
        entry = '%s %s %s/%s' % (seqno, action, addr, prefixlen)
        if log:
            entry += ' log'
        cmds.append(entry)
        cmds.append('exit')
        return self.configure(cmds)

    def add_entry(self, name, action, addr, prefixlen, log=False):
        cmds = ['ip access-list standard %s' % name]
        entry = '%s %s/%s' % (action, addr, prefixlen)
        if log:
            entry += ' log'
        cmds.append(entry)
        cmds.append('exit')
        return self.configure(cmds)

    def remove_entry(self, name, seqno):
        cmds = ['ip access-list standard %s' % name, 'no %s' % seqno, 'exit']
        return self.configure(cmds)


def instance(node):
    return StandardAcls(node)
