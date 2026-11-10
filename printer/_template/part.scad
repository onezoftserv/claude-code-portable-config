// TEMPLATE: copy this folder, rename it, edit.
// Build: python scripts/build_part.py printer/<name>
//
// Rules: millimetres, parameters first, part sits on z=0 in print orientation.
// Libraries (after scripts/fetch_libs.py):
//   include <BOSL2/std.scad>

/* [Size] */
width  = 40;
depth  = 25;
height = 10;
wall   = 2;      // >= 2 perimeters of a 0.4 nozzle

/* [Fit] */
clearance = 0.2; // per side, for parts that slide together; tune after a test print

$fn = 64;

difference() {
    cube([width, depth, height]);
    translate([wall, wall, wall])
        cube([width - 2 * wall, depth - 2 * wall, height]);
}
