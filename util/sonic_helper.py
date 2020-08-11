from enum import Enum


class AclTableType(Enum):
    L2 = 1
    L3 = 2
    L3V6 = 3
    MIRROR = 4
    MIRRORV6 = 5
    MIRROR_DSCP = 6
    CTRLPLANE = 7

    def __str__(self):
        return self.name


class AclTableStage(Enum):
    INGRESS = 1
    EGRESS = 2

    def __str__(self):
        return self.name.lower()


class AclPacketAction(Enum):
    DROP = 1
    ACCEPT = 2
    REJECT = 3

    def __str__(self):
        return self.name


class IPProtocol(Enum):
    IP_ICMP = 1
    IP_TCP = 6
    IP_UDP = 17

    def __str__(self):
        return self.name


class VLANTaggingMode(Enum):
    TAGGED = 1
    UNTAGGED = 2

    def __str__(self):
        return self.name.lower()
