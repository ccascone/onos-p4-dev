#include "include/std_defines.p4"
#include "include/std_headers.p4"
#include "include/std_parser.p4"
#include "include/std_actions.p4"

/* ECMP machinery */
header_type ecmp_metadata_t {
    fields {
        groupId : 16;
        hash : 16;
    }
}

metadata ecmp_metadata_t ecmp_metadata;

field_list ecmp_hash_fields {
    ipv4.srcAddr;
    ipv4.dstAddr;
    tcp.srcPort;
    tcp.dstPort;
}

field_list_calculation ecmp_hash {
    input {
        ecmp_hash_fields;
    }
    algorithm : crc16;
    output_width : 16;
}

action ecmp_group(groupId, numPorts) {
    modify_field(ecmp_metadata.groupId, groupId);
    // The modify_field_with_hash_based_offset works in this way (base + (hash_value % size))
    // e.g. if we want to select a port between 0 and 4 we use: (0 + (hash_value % 4))
    modify_field_with_hash_based_offset(ecmp_metadata.hash, 0, ecmp_hash, numPorts);
}

table ecmp_group_table {
    reads {
        ecmp_metadata.groupId : ternary;
        ecmp_metadata.hash : ternary;
    }
    actions {
        set_egress_port;
    }
}

/* Port counters */
counter ingress_counter {
    type : packets; // bmv2 always counts both bytes and packets 
    instance_count : 1024;
    min_width : 32;
}

counter egress_counter {
    type: packets;
    instance_count : 1024;
    min_width : 32;
}

action count_packet() {
    count(ingress_counter, standard_metadata.ingress_port);
    count(egress_counter, standard_metadata.egress_spec);
}

table port_count {
    actions {
        count_packet;
    }
}


/* Main table */
table table0 {
    reads {
        standard_metadata.ingress_port : ternary;
        ethernet.dstAddr : ternary;
        ethernet.srcAddr : ternary;
        ethernet.etherType : ternary;
    }
    actions {
        set_egress_port;
        ecmp_group;
        send_to_cpu;
        _drop;
    }
    support_timeout: true;
}

/* Table 0 counters */
// counter table0_counter {
//    type: packets;
//    direct: table0;
//    min_width : 32;
//}

/* Control flow */
control ingress {
    apply(table0) {
        ecmp_group { // ecmp action was used
            apply(ecmp_group_table);
        }
    }
    // count tx packets
    // TODO (Carmelo): put this in egress pipeline
    apply(port_count);
}