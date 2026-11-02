/* Kindle PW1 / EY21 wall dock — compact prototype v0.2, dimensions in mm.
   User measurements are authoritative; curved rear shell and corner radii
   remain approximate. See hinweise.txt before printing. No mains enclosure.
*/
part = "assembly"; // assembly, holder, cover, profile_coupon, section
print_orientation = true;
$fn = 64;

// Device and measured lower-edge profile, front view, x from left edge.
kindle_w = 117;
kindle_h = 169;
kindle_max_t = 9.1;
edge_t = 3;
block_t = 9;
transition_start = 35;
transition_end = 40;
lower_bezel = 27;
fit = 0.6;                  // prototype clearance on each side
corner_r = 7;               // APPROXIMATION, reference model only

// Existing straight cable; body length excludes the metal USB plug.
usb_x = 45;
usb_from_front = 4.5;        // UNMEASURED: adjustable port centre depth
plug_w = 9;
plug_t = 5;
plug_l = 16;
relief_l = 4;
wire_d = 3;
body_end_play = 0.6;
plug_side_play = 1.2;
plug_depth_play = 1.6;       // lets the plug align before tightening the lid
wire_channel = 4.4;
bend_r = 10;                // provisional room for a relaxed 180-degree return

// Mounting and structure.
mount_pitch = 60;
mount_shaft = 4.0;          // clearance slot: use the box's own device screws
mount_head = 8.0;           // verify actual screw head fits
mount_slot = 8;
back_t = 2.8;
wall = 3;
front_lip_t = 1.6;
front_lip_h = 20;           // within the measured 27mm lower bezel
profile_contact_h = 0.8;    // contacts only the measured lower edge
lid_t = 2.2;
lid_pilot = 2.7;            // two M3x10 screws thread into PETG; do not overtighten
lid_clearance = 3.4;

rear_wire_z = back_t + wire_channel/2 + 1;
usb_z = rear_wire_z + 2*bend_r;
front_z = usb_z + usb_from_front;
retainer_z = front_z + fit;
frame_front = retainer_z + front_lip_t;
body_y = -plug_l-body_end_play;
turn_y = body_y-relief_l;
bay_h = ceil(-turn_y+bend_r+wire_channel/2+wall);
support_w = 80;
mount_x = kindle_w/2;
mount_y = 30;
x0 = mount_x-support_w/2;
x1 = mount_x+support_w/2;
y0 = -bay_h;
y1 = mount_y+40;
plate_y0 = mount_y-40;
pod_w = 28;
pod_x0 = usb_x-pod_w/2;
pod_x1 = usb_x+pod_w/2;
lid_screw_x = [usb_x-8,usb_x+8];
lid_y0 = y0+0.25;
lid_y1 = -wall-0.25;
lid_screw_y = (lid_y0+lid_y1)/2;

assert(front_lip_h < lower_bezel-3, "Front lip must stay below display");
assert(usb_x-plug_w/2 > transition_start, "USB pocket hits outer thin section");
assert(wire_channel > wire_d, "Cable clearance missing");
echo("Overall W/H/depth (without screw heads)",x1-x0,y1-y0,frame_front);
echo("Cable bay below Kindle",bay_h,"USB depth estimate",usb_from_front);

module rounded_rect(w,h,r) {
    hull() for(x=[r,w-r],y=[r,h-r]) translate([x,y]) circle(r=r);
}
module rectangle_at(x,y,w,h,r=2) {translate([x,y]) rounded_rect(w,h,r);}
module prism_at(x,y,w,h,z,t,r=2) {
    translate([0,0,z]) linear_extrude(t) rectangle_at(x,y,w,h,r);
}
module slot_at(x,y,diameter,length,z,h,angle=0) {
    translate([x,y,z]) rotate([0,0,angle]) linear_extrude(h)
        hull() for(d=[-(length-diameter)/2,(length-diameter)/2])
            translate([0,d]) circle(d=diameter);
}
module mounting_holes() {
    for(a=[0,90,180,270]) {
        x=mount_x+mount_pitch/2*cos(a);
        y=mount_y+mount_pitch/2*sin(a);
        slot_at(x,y,mount_shaft,mount_slot,-0.1,back_t+0.2,a);
        slot_at(x,y,mount_head,mount_slot+mount_head-mount_shaft,back_t-1,1.1,a);
    }
}
module back_plate() {
    difference() {
        prism_at(x0,plate_y0,support_w,80,0,back_t,6);
        translate([mount_x,mount_y,-0.1]) cylinder(d=38,h=back_t+0.2);
        mounting_holes();
    }
}
// A rear bearing rib, using the measured thin/ramped/full-thickness profile.
module bottom_profile_bearing() {
    rotate([90,0,0]) linear_extrude(profile_contact_h+0.1)
        polygon([[ x0,back_t ],[x1,back_t],
            [x1,front_z-edge_t-fit],
            [kindle_w-transition_start,front_z-edge_t-fit],
            [kindle_w-transition_end,front_z-block_t-fit],
            [transition_end,front_z-block_t-fit],
            [transition_start,front_z-edge_t-fit],[x0,front_z-edge_t-fit]]);
}
module footer_trough() {
    difference() {
        prism_at(pod_x0,y0,pod_w,bay_h,0,front_z,5);
        prism_at(pod_x0+wall,y0+wall,pod_w-2*wall,bay_h-2*wall,
            back_t,frame_front+1,3);
    }
}
module connector_pod() {
    translate([usb_x-9,turn_y-2,back_t])
        cube([18,-turn_y+2,front_z-back_t]);
}
module lid_posts() {
    for(x=lid_screw_x) translate([x-5,lid_screw_y-5,back_t])
        cube([10,10,front_z-back_t]);
}
module wire_sweep(a,b) {
    hull() {translate(a) sphere(d=wire_channel);translate(b) sphere(d=wire_channel);}
}
module cable_void() {
    // Side opening lets a complete cable be installed before fitting the lid.
    translate([usb_x-plug_w/2-plug_side_play,body_y,usb_z-plug_t/2-plug_depth_play])
        cube([plug_w+2*plug_side_play,plug_l+body_end_play+2,frame_front+2]);
    translate([usb_x-3,turn_y-1,usb_z-3.5])
        cube([6,relief_l+2,frame_front+2]);
    // Continuous toroidal sweep avoids seams between short capsule segments.
    multmatrix([[0,0,1,usb_x],[0,-1,0,turn_y],[1,0,0,usb_z-bend_r],[0,0,0,1]])
        rotate_extrude(angle=180,convexity=10)
            translate([bend_r,0]) circle(d=wire_channel,$fn=32);
    translate([usb_x,turn_y-0.1,rear_wire_z]) rotate([-90,0,0])
        cylinder(d=wire_channel,h=mount_y-bend_r-turn_y+0.2,$fn=32);
    // Turn through the existing aperture, with the cable ending inside the box.
    multmatrix([[0,0,1,usb_x],[0,1,0,mount_y-bend_r],[1,0,0,rear_wire_z-bend_r],[0,0,0,1]])
        rotate_extrude(angle=90,convexity=10)
            translate([bend_r,0]) circle(d=wire_channel,$fn=32);
}
module holder() {
    difference() {
        union() {
            back_plate(); footer_trough(); connector_pod(); lid_posts();
            // Small rear supports resist screen-touch loads; no side wrapping.
            // Optional thin cushioning goes on these faces after checking fit.
            for(x=[mount_x-25,mount_x+25])
                translate([x-5,45,back_t-0.1])
                    cube([10,12,front_z-kindle_max_t-fit-back_t+0.1]);
            // Bottom shelf and front retention strip, open above for removal.
            translate([x0,-wall,0]) cube([x1-x0,wall,frame_front]);
            translate([x0,-wall,retainer_z]) cube([x1-x0,wall+front_lip_h,front_lip_t]);
            // rotate/extrude ends at y=0; shift into the first 0.8mm of device.
            translate([0,profile_contact_h,0]) bottom_profile_bearing();
        }
        cable_void();
        // Keep tool access to both screw orientations. The lower vertical
        // screw sits behind the retaining strip, so it gets an access slot.
        slot_at(mount_x,mount_y-mount_pitch/2,mount_head+1,
            mount_slot+mount_head-mount_shaft+1,back_t+0.01,frame_front,90);
        // Relieve the entire I/O region, including an unmeasured power-button
        // protrusion. The thin outer rim, not the button or USB plug, carries load.
        translate([transition_start,-1,front_z-block_t-fit])
            cube([kindle_w-2*transition_start,1.05,block_t+2*fit]);
        for(x=lid_screw_x) translate([x,lid_screw_y,front_z-12])
            cylinder(d=lid_pilot,h=15);
    }
}
module cover() {
    difference() {
        prism_at(pod_x0+0.25,lid_y0,pod_w-0.5,lid_y1-lid_y0,front_z,lid_t,3);
        for(x=lid_screw_x) {
            translate([x,lid_screw_y,front_z-0.1]) cylinder(d=lid_clearance,h=lid_t+0.2);
            translate([x,lid_screw_y,front_z+lid_t-1.5]) cylinder(d1=lid_clearance,d2=6.4,h=1.6);
        }
    }
}
module reference_kindle() {
    // Visual reference only: back curvature and corner radius are NOT measured.
    color([0.16,0.16,0.16,0.75]) union() {
        hull() {
            prism_at(0,0,kindle_w,kindle_h,front_z-edge_t,edge_t,corner_r);
            prism_at(12,12,kindle_w-24,kindle_h-24,front_z-kindle_max_t,0.1,12);
        }
        intersection() {
            translate([0,2,0]) rotate([90,0,0]) linear_extrude(2)
                polygon([[35,front_z],[82,front_z],[82,front_z-edge_t],
                    [77,front_z-block_t],[40,front_z-block_t],[35,front_z-edge_t]]);
            translate([0,-2,0]) cube([kindle_w,4,front_z+1]);
        }
    }
    color("white") translate([14,lower_bezel,front_z+0.05])
        cube([kindle_w-28,kindle_h-lower_bezel-14,0.1]);
    color("silver") translate([usb_x-plug_w/2,-plug_l,usb_z-plug_t/2])
        cube([plug_w,plug_l,plug_t]);
    color("DimGray") for(a=[0:10:170]) hull() {
        translate([usb_x,turn_y-bend_r*sin(a),usb_z-bend_r+bend_r*cos(a)]) sphere(d=wire_d);
        translate([usb_x,turn_y-bend_r*sin(a+10),usb_z-bend_r+bend_r*cos(a+10)]) sphere(d=wire_d);
    }
}
module coupon() {
    intersection() {
        holder();
        translate([x0,-wall,front_z-12]) cube([x1-x0,wall+front_lip_h,20]);
    }
}
module output_holder() {
    if(print_orientation) rotate([90,0,0]) translate([0,bay_h,0]) holder();
    else holder();
}
if(part=="holder") output_holder();
else if(part=="cover") translate([-pod_x0,-lid_y0,-front_z]) cover();
else if(part=="profile_coupon") rotate([90,0,0]) translate([-x0,wall,-front_z+12]) coupon();
else if(part=="section") intersection() {
    union(){holder();cover();} translate([usb_x-0.3,-bay_h-1,-1]) cube([0.6,kindle_h+bay_h+4,frame_front+2]);
}
else {
    color("Gainsboro") holder();color("Silver") cover();reference_kindle();
}
