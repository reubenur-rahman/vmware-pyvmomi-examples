'''
Copyright 2014-2015 Reubenur Rahman
All Rights Reserved
@author: reuben.13@gmail.com
'''

import atexit

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect


inputs = {'vcenter_ip': '15.22.10.11',
          'vcenter_password': 'Password123',
          'vcenter_user': 'Administrator',
          'host_name': '15.22.11.6',
          'switch_name': 'TestvSwitch',
          'num_ports': 100,
          'nic_name': 'vmnic1',
          'port_group_name': 'TestPortGroup'
          }


def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def create_vswitch(host_network_system, vss_name, num_ports, nic_name):
    vss_spec = vim.host.VirtualSwitch.Specification()
    vss_spec.numPorts = num_ports
    #vss_spec.bridge = vim.host.VirtualSwitch.SimpleBridge(nicDevice='pnic_key')
    vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=[nic_name])

    host_network_system.AddVirtualSwitch(vswitchName=vss_name, spec=vss_spec)

    print "Successfully created vSwitch ",  vss_name


def create_port_group(host_network_system, pg_name, vss_name):
    port_group_spec = vim.host.PortGroup.Specification()
    port_group_spec.name = pg_name
    port_group_spec.vlanId = 0
    port_group_spec.vswitchName = vss_name

    security_policy = vim.host.NetworkPolicy.SecurityPolicy()
    security_policy.allowPromiscuous = True
    security_policy.forgedTransmits = True
    security_policy.macChanges = False

    port_group_spec.policy = vim.host.NetworkPolicy(security=security_policy)

    host_network_system.AddPortGroup(portgrp=port_group_spec)

    print "Successfully created PortGroup ",  pg_name


def add_virtual_nic(host_network_system, pg_name):
    vnic_spec = vim.host.VirtualNic.Specification()
    vnic_spec.ip = vim.host.IpConfig(dhcp=True)
    vnic_spec.mac = '00:50:56:7d:5e:0b'

    host_network_system.AddServiceConsoleVirtualNic(portgroup=pg_name, nic=vnic_spec)


def main():

    try:
        si = None
        try:
            print "Trying to connect to VCENTER SERVER . . ."
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'], version="vim.version.version8")
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        print "Connected to VCENTER SERVER !"

        content = si.RetrieveContent()

        host = get_obj(content, [vim.HostSystem], inputs['host_name'])

        host_network_system = host.configManager.networkSystem

#         for pnic in host.config.network.pnic:
#             if pnic.device == inputs['nic_name']:
#                 pnic_key = pnic.key

        create_vswitch(host_network_system, inputs['switch_name'], inputs['num_ports'], inputs['nic_name'])

        create_port_group(host_network_system, inputs['port_group_name'], inputs['switch_name'])

        #add_virtual_nic(host_network_system, inputs['port_group_name'])

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1

# Start program
if __name__ == "__main__":
    main()
