#include "include/std_defines.p4"
#include "include/std_headers.p4"
#include "include/std_parser.p4"
#include "include/std_actions.p4"

#define SELECTOR_WIDTH 128

/* wcmp machinery */
header_type wcmp_meta_t {
    fields {
        groupId : 16;
        numBits: 16; // TODO dependent on SELECTOR_WIDTH
        selector : SELECTOR_WIDTH;
    }
}

metadata wcmp_meta_t wcmp_meta;

field_list wcmp_hash_fields {
    intrinsic_metadata.ingress_global_timestamp;
    ethernet.dstAddr;
    ethernet.srcAddr;
    ipv4.srcAddr;
    ipv4.dstAddr;
    ipv4.protocol;
    tcp.srcPort;
    tcp.dstPort;
    udp.srcPort;
    udp.dstPort;
}

field_list_calculation wcmp_hash {
    input {
        wcmp_hash_fields;
    }
    algorithm : crc32;
    output_width : 32;
}

action wcmp_group(groupId) {
    modify_field(wcmp_meta.groupId, groupId);
    // GENERATE A SELECTOR with the first x bits set to 1, where x is the result of hash
    modify_field_with_hash_based_offset(wcmp_meta.numBits, // dest field
                                        2, // base
                                        wcmp_hash, // hash calculation
                                        (SELECTOR_WIDTH - 2)); // size (modulo divisor)
}

action wcmp_set_selector() {
    modify_field(wcmp_meta.selector,
                 (((1 << wcmp_meta.numBits) - 1) << (SELECTOR_WIDTH - wcmp_meta.numBits)));
}

action count_packet() {
    count(ingress_counter, standard_metadata.ingress_port);
    count(egress_counter, standard_metadata.egress_spec);
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
        wcmp_group;
        send_to_cpu;
        _drop;
    }
    support_timeout: true;
}

table wcmp_set_selector_table {
    actions {
        wcmp_set_selector;
    }
}

table wcmp_group_table {
    reads {
        wcmp_meta.groupId : exact;
        wcmp_meta.selector : lpm;
    }
    actions {
        set_egress_port;
    }
}

table port_count {
    actions {
        count_packet;
    }
}

counter table0_counter {
    type: packets;
    direct: table0;
    min_width : 32;
}

counter wcmp_group_table_counter {
    type: packets;
    direct: wcmp_group_table;
    min_width : 32;
}


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

/* Control flow */
control ingress {
    apply(table0) {
        wcmp_group { // wcmp action was used
            apply(wcmp_set_selector_table) {
                wcmp_set_selector {
                    apply(wcmp_group_table);
                }
            }
        }
    }
    
    apply(port_count);
}