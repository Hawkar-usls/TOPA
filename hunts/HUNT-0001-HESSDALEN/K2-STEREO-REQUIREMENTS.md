# K2 Stereo Baseline Requirements

TOPA corrected its own earlier wording: two cameras do not become a parallax instrument merely because both are cameras.

For HUNT-0001, useful triangulation requires a separated, surveyed, synchronized and calibrated camera pair.

Required before any physical distance/speed claim:

1. distinct station coordinates with uncertainty;
2. nontrivial baseline length;
3. overlapping field of view;
4. measured clock offset/drift;
5. lens intrinsics and distortion model;
6. boresight/extrinsic calibration;
7. same candidate in raw frames from both stations;
8. uncertainty-propagated ray intersection/closest approach;
9. rejection of solutions dominated by tiny intersection angle.

The two currently documented operational 4K cameras are on the Blue Box mast and point in different directions. This is useful for coverage, not automatically for stereo ranging.

A future third camera at a separated station may satisfy K2 only after its exact position, operational status, clock discipline, calibration and overlapping FOV are independently frozen.
