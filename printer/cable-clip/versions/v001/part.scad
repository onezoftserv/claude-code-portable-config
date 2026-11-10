// Example: screw-down cable clip. No libraries needed.
// Build: python scripts/build_part.py printer/cable-clip -D cable_d=6
// Prints on its side as modelled (profile on the plate): no supports.

/* [Cable] */
cable_d = 5;        // cable diameter
gap     = 3.5;      // opening the cable snaps through; smaller than cable_d

/* [Body] */
wall    = 2.4;
width   = 10;       // extrusion height when printed
tab_len = 12;
screw_d = 3.4;      // M3 clearance

$fn = 72;

outer_r = cable_d / 2 + wall;

module profile() {
    difference() {
        union() {
            circle(outer_r);
            // mounting tab, flush with the bottom of the ring
            translate([0, -outer_r])
                square([outer_r + tab_len, wall]);
        }
        circle(d = cable_d);
        // snap-in opening at the top
        translate([-gap / 2, 0])
            square([gap, outer_r + 1]);
    }
}

difference() {
    linear_extrude(width) profile();
    // screw hole down through the tab
    translate([outer_r + tab_len / 2, -outer_r - 1, width / 2])
        rotate([-90, 0, 0])
            cylinder(d = screw_d, h = wall + 2);
}
