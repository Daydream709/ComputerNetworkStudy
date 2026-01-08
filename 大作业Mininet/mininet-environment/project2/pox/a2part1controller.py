# Part 1 of UWCSE's Mininet-SDN project2
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

# TODO:请完成s1_setup，s2_setup，s3_setup，cores21_setup，dcs31_setup的编写
# 请注意可能需要引入新的包


log = core.getLogger()

# Convenience mappings of hostnames to ips
IPS = {
    "h10": "10.0.1.10",
    "h20": "10.0.2.20",
    "h30": "10.0.3.30",
    "serv1": "10.0.4.10",
    "hnotrust": "172.16.10.100",
}

# Convenience mappings of hostnames to subnets
SUBNETS = {
    "h10": "10.0.1.0/24",
    "h20": "10.0.2.0/24",
    "h30": "10.0.3.0/24",
    "serv1": "10.0.4.0/24",
    "hnotrust": "172.16.10.0/24",
}


class Part3Controller(object):
    """
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        """
        初始化Part3Controller对象，为指定的交换机连接设置流表规则

        Args:
            connection: 与交换机的连接对象
        """
        print(connection.dpid)
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        def _add_flow(match, actions, priority=0):
            """
            内部辅助函数，用于向交换机添加流表项

            Args:
                match: 匹配条件对象
                actions: 要执行的动作列表
                priority: 流表项优先级，默认为0
            """
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
            print("UNKNOWN SWITCH")
            exit(1)

    def s1_setup(self, _add_flow):
        """
        为交换机s1设置流表规则

        Args:
            _add_flow: 添加流表项的回调函数
        """
        # 添加ARP流表项，优先级为10，将ARP包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 添加IPv4流表项，优先级为5，将IPv4包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0800), actions=[of.ofp_action_output(port=of.OFPP_FLOOD)], priority=5
        )

    def s2_setup(self, _add_flow):
        """
        为交换机s2设置流表规则

        Args:
            _add_flow: 添加流表项的回调函数
        """
        # 添加ARP流表项，优先级为10，将ARP包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 添加IPv4流表项，优先级为5，将IPv4包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0800), actions=[of.ofp_action_output(port=of.OFPP_FLOOD)], priority=5
        )

    def s3_setup(self, _add_flow):
        """
        为交换机s3设置流表规则

        Args:
            _add_flow: 添加流表项的回调函数
        """
        # 添加ARP流表项，优先级为10，将ARP包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 添加IPv4流表项，优先级为5，将IPv4包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0800), actions=[of.ofp_action_output(port=of.OFPP_FLOOD)], priority=5
        )

    def dcs31_setup(self, _add_flow):
        """
        为交换机dcs31设置流表规则

        Args:
            _add_flow: 添加流表项的回调函数
        """
        # 添加ARP流表项，优先级为10，将ARP包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 添加IPv4流表项，优先级为5，将IPv4包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0800), actions=[of.ofp_action_output(port=of.OFPP_FLOOD)], priority=5
        )

    def cores21_setup(self, _add_flow):
        """
        为核心交换机cores21设置流表规则，包含安全策略和路由规则

        Args:
            _add_flow: 添加流表项的回调函数
        """
        # 添加ARP流表项，优先级为10，将ARP包泛洪到所有端口
        _add_flow(
            match=of.ofp_match(dl_type=0x0806),
            actions=[of.ofp_action_output(port=of.OFPP_FLOOD)],
            priority=10,
        )

        # 阻止从不信任主机到服务器的特定流量，优先级为200
        _add_flow(
            match=of.ofp_match(dl_type=0x0800, nw_src="172.16.10.100", nw_dst="10.0.4.10"),
            actions=[],  # drop
            priority=200,
        )
        # 阻止从不信任主机到服务器子网的特定流量，优先级为200
        _add_flow(
            match=of.ofp_match(dl_type=0x0800, nw_src="172.16.10.100", nw_dst="10.0.4.0/24"),
            actions=[],  # drop
            priority=200,
        )

        # 阻止从不信任主机到其他主机的ICMP流量，优先级为190
        for dst in ["10.0.1.10", "10.0.2.20", "10.0.3.30", "10.0.4.10"]:
            _add_flow(
                match=of.ofp_match(dl_type=0x0800, nw_proto=1, nw_src="172.16.10.100", nw_dst=dst),
                actions=[],  # drop
                priority=190,
            )

        # 设置路由规则，将目标IP映射到对应的输出端口
        routes = [
            ("10.0.1.10", 1),  # to s1
            ("10.0.2.20", 2),  # to s2
            ("10.0.3.30", 3),  # to s3
            ("10.0.4.10", 4),  # to dcs31/serv1
            ("172.16.10.100", 5),  # to hnotrust1
        ]
        for ip, out_port in routes:
            _add_flow(
                match=of.ofp_match(dl_type=0x0800, nw_dst=ip),
                actions=[of.ofp_action_output(port=out_port)],
                priority=100,
            )

        # 默认规则：丢弃其他IPv4包，保持行为确定性
        _add_flow(match=of.ofp_match(dl_type=0x0800), actions=[], priority=1)  # drop

    # used in part 4 to handle individual ARP packets
    # not needed for part 3 (USE RULES!)
    # causes the switch to output packet_in on out_port
    def resend_packet(self, packet_in, out_port):
        """
        重新发送数据包到指定端口

        Args:
            packet_in: 输入的数据包对象
            out_port: 输出端口
        """
        msg = of.ofp_packet_out()
        msg.data = packet_in
        action = of.ofp_action_output(port=out_port)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        处理未被路由器规则处理的数据包

        Args:
            event: PacketIn事件对象
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        # 检查是否为IPv6数据包，如果是则忽略（不打印Unhandled packet消息）
        if packet.type == 0x86DD:  # IPv6
            # 可以选择完全忽略IPv6数据包
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.
        print("Unhandled packet from " + str(self.connection.dpid) + ":" + packet.dump())


def launch():
    """
    启动组件并注册连接建立事件监听器
    """

    def start_switch(event):
        """
        当交换机连接建立时的回调函数

        Args:
            event: 连接建立事件对象
        """
        log.debug("Controlling %s" % (event.connection,))
        Part3Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
