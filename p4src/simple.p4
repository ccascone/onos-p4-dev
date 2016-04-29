// Logic ports as defined in the simple_switch target
#define CPU_PORT 255
#define DROP_PORT 511

/*********** HEADERS *************/

header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header ethernet_t ethernet;

header_type intrinsic_metadata_t {
    fields {
        ingress_global_timestamp : 32;
        lf_field_list : 32;
        mcast_grp : 16;
        egress_rid : 16;
    }
}

metadata intrinsic_metadata_t intrinsic_metadata;

/*********** PARSER *************/

parser start {
    return parse_ethernet;
}

parser parse_ethernet {
    extract(ethernet);
    return ingress;
}

/*********** ACTIONS *************/

action fwd(port) {
    modify_field(standard_metadata.egress_spec, port);
}

action flood() {
    modify_field(intrinsic_metadata.mcast_grp, standard_metadata.ingress_port);
}

action _drop() {
    modify_field(standard_metadata.egress_spec, DROP_PORT);
}

action send_to_cpu() {
    modify_field(standard_metadata.egress_spec, CPU_PORT);
}

/*********** TABLES *************/

table table0 {
    reads {
        standard_metadata.ingress_port : ternary;
        ethernet.dstAddr : ternary;
        ethernet.srcAddr : ternary;
        ethernet.etherType : ternary;
    }
    actions {
        fwd; 
        flood;
        send_to_cpu;
        _drop;
    }
}

/*********** CONTROL FLOW *************/

control ingress {
    
    apply(table0);
        
}