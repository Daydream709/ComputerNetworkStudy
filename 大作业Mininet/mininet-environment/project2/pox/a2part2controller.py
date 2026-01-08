from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.icmp import icmp

# TODO:请完成s1_setup，s2_setup，s3_setup，cores21_setup，dcs31_setup的编写（与part3相似）
# 自定义函数实现学习型路由器
# 请注意可能需要引入新的包
# 需要对_handle_PacketIn函数进行修改

log = core.getLogger()

# 便利的主机名到IP的映射
IPS = {
    "h10": "10.0.1.10",
    "h20": "10.0.2.20",
    "h30": "10.0.3.30",
    "serv1": "10.0.4.10",
    "hnotrust": "172.16.10.100",
}

# 便利的主机名到子网的映射
SUBNETS = {
    "h10": "10.0.1.0/24",
    "h20": "10.0.2.0/24",
    "h30": "10.0.3.0/24",
    "serv1": "10.0.4.0/24",
    "hnotrust": "172.16.10.0/24",
}


class Part4Controller(object):
    """
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # ARP/L2 learning table: IPAddr -> (EthAddr, Port)
        # Port is the port on cores21 that leads toward that IP (e.g., to s1/s2/s3/dcs31/hnotrust1).
        self.arp_table = {}

        # Router (gateway) MAC Address (shared across subnets per assignment)
        self.gw_mac = EthAddr("00:00:00:00:00:FE")

        def _add_flow(match, actions, priority=0):
            # 创建流修改消息
            msg = of.ofp_flow_mod()
            msg.match = match
            msg.actions = actions
            msg.priority = priority
            msg.idle_timeout = 0
            msg.hard_timeout = 0
            msg.buffer_id = of.NO_BUFFER
            self.connection.send(msg)

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # use the dpid to figure out what switch is being created
        if connection.dpid == 1:
            self.s1_setup(_add_flow)
        elif connection.dpid == 2:
            self.s2_setup(_add_flow)
        elif connection.dpid == 3:
            self.s3_setup(_add_flow)
        elif connection.dpid == 21:
            self.cores21_setup(_add_flow)
        elif connection.dpid == 31:
            self.dcs31_setup(_add_flow)
        else:
            log.warning("UNKNOWN SWITCH dpid=%s" % (connection.dpid,))

    def s1_setup(self, _add_flow):
        # Flood ARP + IPv4 like a dumb L2 switch
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.ARP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=5,
        )

    def s2_setup(self, _add_flow):
        # Flood ARP + IPv4 like a dumb L2 switch
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.ARP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=5,
        )

    def s3_setup(self, _add_flow):
        # Flood ARP + IPv4 like a dumb L2 switch
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.ARP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=5,
        )

    def cores21_setup(self, _add_flow):
        # Put core switch rules here
        # Part4: cores21 is a learning L3 router.
        # - DO NOT flood at cores21
        # - handle ARP in controller (PacketIn)
        # - dynamically install IP forwarding rules once destination is learned
        # - enforce the same L3 policy rules as in Part1/Part3

        # 策略1：阻止来自hnotrust子网到serv1的所有IP流量
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE, nw_src=SUBNETS["hnotrust"], nw_dst=IPS["serv1"]),
            actions=[],  # No actions -> Drop
            priority=200,
        )

        # 策略2：阻止来自hnotrust子网到常规主机和serv1的ICMP
        for dst in [IPS["h10"], IPS["h20"], IPS["h30"], IPS["serv1"]]:
            _add_flow(
                match=of.ofp_match(
                    dl_type=ethernet.IP_TYPE, nw_proto=1, nw_src=SUBNETS["hnotrust"], nw_dst=dst
                ),
                actions=[],  # No actions -> Drop
                priority=190,
            )

        # Send all ARP to controller (controller will learn + reply for gateways)
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.ARP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_CONTROLLER)],
            priority=1,
        )

        # Send other IPv4 to controller initially (unknown routes get dropped by controller;
        # known routes will get their own higher-priority flow entries installed dynamically)
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_CONTROLLER)],
            priority=1,
        )

    def dcs31_setup(self, _add_flow):
        # Flood ARP + IPv4 like a dumb L2 switch
        _add_flow(
            match=of.ofp_match(dl_type=ethernet.ARP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        _add_flow(
            match=of.ofp_match(dl_type=ethernet.IP_TYPE),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=5,
        )

    # used in part 4 to handle individual ARP packets
    # causes the switch to output packet_in on out_port
    def resend_packet(self, packet_in, out_port):
        # 创建数据包输出消息
        msg = of.ofp_packet_out()
        msg.data = packet_in
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        Packets not handled by the router rules will be
        forwarded to this method to be handled by the controller
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        if self.connection.dpid == 21:
            self.handle_cores21_packet(event)
        else:
            if packet.type == 0x86DD:  # IPv6
                return
            print("Unhandled packet from " + str(self.connection.dpid) + ":" + packet.dump())

    def handle_cores21_packet(self, event):
        # 解析数据包
        packet = event.parsed
        # 输入端口
        in_port = event.port

        # 首先处理ARP数据包
        if packet.type == ethernet.ARP_TYPE:
            arp_packet = packet.payload
            # Learn the source of ARP packets
            self.arp_table[arp_packet.protosrc] = (packet.src, in_port)

            # Process ARP requests for gateway addresses
            if arp_packet.opcode == arp.REQUEST:
                # Check if request is for one of our gateway IPs
                gateway_ips = [
                    IPAddr("10.0.1.1"),
                    IPAddr("10.0.2.1"),
                    IPAddr("10.0.3.1"),
                    IPAddr("10.0.4.1"),
                    IPAddr("172.16.10.1"),
                ]

                if arp_packet.protodst in gateway_ips:
                    # Create ARP reply
                    arp_reply = arp()
                    arp_reply.opcode = arp.REPLY
                    arp_reply.hwsrc = self.gw_mac
                    arp_reply.hwdst = arp_packet.hwsrc
                    arp_reply.protosrc = arp_packet.protodst
                    arp_reply.protodst = arp_packet.protosrc

                    # Create ethernet frame for ARP reply
                    eth_frame = ethernet()
                    eth_frame.type = ethernet.ARP_TYPE
                    eth_frame.src = self.gw_mac
                    eth_frame.dst = packet.src
                    eth_frame.payload = arp_reply

                    self.resend_packet(eth_frame.pack(), in_port)
            # Don't forward ARP packets between subnets
            return
        # Handle IPv4 packets
        elif packet.type == ethernet.IP_TYPE:
            ip_packet = packet.payload
            # Learn source IP -> MAC mapping
            self.arp_table[ip_packet.srcip] = (packet.src, in_port)

            target_ip = ip_packet.dstip

            # Only route if we have learned the destination
            if target_ip in self.arp_table:
                target_mac, output_port = self.arp_table[target_ip]

                # Install flow rule for future packets to this destination
                flow_msg = of.ofp_flow_mod()
                flow_msg.priority = 100
                flow_msg.match.dl_type = ethernet.IP_TYPE
                flow_msg.match.dl_dst = self.gw_mac
                flow_msg.match.nw_dst = target_ip

                # Set up actions: update MAC addresses and forward
                flow_msg.actions.append(of.ofp_action_dl_addr.set_src(self.gw_mac))
                flow_msg.actions.append(of.ofp_action_dl_addr.set_dst(target_mac))
                flow_msg.actions.append(of.ofp_action_output(port=output_port))
                self.connection.send(flow_msg)

                # Forward the current packet
                packet.src = self.gw_mac
                packet.dst = target_mac
                self.resend_packet(packet.pack(), output_port)
            # If target not in table, drop the packet (as required by spec)
        else:
            # Non-ARP and non-IPv4 packets are ignored
            return


def launch():
    """Starts the component"""

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Part4Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
