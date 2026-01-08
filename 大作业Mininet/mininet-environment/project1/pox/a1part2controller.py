# Part 2 of UWCSE's Project 3
#
# based on Lab 4 from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()


class Firewall(object):
    """
    A Firewall object is created for each switch that connects.
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)

        def _add_flow(match, actions, priority=0):
            msg = of.ofp_flow_mod()
            msg.match = match
            msg.actions = actions
            msg.priority = priority
            msg.idle_timeout = 0
            msg.hard_timeout = 0
            msg.buffer_id = of.NO_BUFFER
            self.connection.send(msg)

        # 规则 1: 允许 ARP（泛洪）
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),  # ARP
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 规则 2: 允许 ICMP（泛洪）
        _add_flow(
            match=of.ofp_match(dl_type=0x0800, nw_proto=1),  # IPv4 + ICMP
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=9,
        )

        # 规则 3: 拒绝其他 IP 流量（如 TCP/UDP）
        _add_flow(match=of.ofp_match(dl_type=0x0800), actions=[], priority=8)  # 所有 IPv4  # drop

        # 规则 4: 拒绝 IPv6 流量
        _add_flow(match=of.ofp_match(dl_type=0x86dd), actions=[], priority=8)  # 所有 IPv6  # drop

    def _handle_PacketIn(self, event):
        """
        Packets not handled by the router rules will be
        forwarded to this method to be handled by the controller
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.
        print("Unhandled packet :" + str(packet.dump()))


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Firewall(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
