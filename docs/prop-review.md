# Prop design and camera review

The 50 chapters in the review reel run for three seconds each. The station clue camera shows a 135-degree turn. The other panels show the back of the model on the rooftop, its size beside the actors in the hallway, and an over-the-shoulder cut in the archive.

## Verification

Blender 4.3.2 on Linux evaluated the saved prop files with the production staging and camera functions. Each design passed the following checks. The [per-prop results](prop-review-results.json) record the cue-frame counts and the smallest number of visible part-center samples across the four tested frames in each view.

| Check | Coverage per prop |
|---|---|
| Set and camera combinations | All four production sets, six production cameras and one rear three-quarter view. Rendered all 28 combinations at 360 × 640, plus a 17-frame station turn. |
| Visibility | Cast orthographic rays through the evaluated scene at four frames in every camera and set. Required a visible prop in the wide shot, clue close-up and reverse view. Actor reaction shots can frame the prop out. |
| Environment | Checked the turning prop against the set meshes and both animated stock actors for 17 frames per set. The actors reach in the station, point in the archive, hop on the roof, and signal time-out in the hallway. Potential bounding-box overlaps were checked against mesh surfaces. |
| Support and framing | Measured the lowest actual mesh vertices against the tabletop and checked its contact patch against the edges. Measured the visible clue and plaque text in camera space as the camera zoomed. |
| Time and cuts | Evaluated 90 frames at 12 fps and 132 frames at 24 fps across 11 cue and visibility cases per rate. Revisited frames out of order, compared a completed turn with a new shot starting at the equivalent angle, and checked that the clue camera kept consistent framing through hidden and visible cuts. Tested a negative turn and two full positive revolutions. |
| Reuse | Loaded the same saved file twice with different paint and labels. Checked each instance and verified the original file retained its SHA-256. |

Across the 50 new props this produced 1,400 set/camera stills, 850 additional turn frames and 11,100 cue-frame evaluations. The four original stock props and an off-center custom test prop also passed. A nine-shot sequence went through the production timeline and encoder using a fixed voice-timing fixture. A second job restored all nine encoded shots byte-for-byte from the cache.

## What changed after viewing the renders

- The cached radio body originally extended from −8% to 108% of the clue frame. With the same saved model and viewing direction it occupied about 17% through 83%. Its bottom now meets the tabletop, and its plaque stays mounted when the radio turns.
- A balance-scale pan hit the reaching witness during the first turn test. Shortening the beam and narrowing the pans cleared the hand. The semaphore exposed a separate framing issue with its plaque. The clue camera now fits both the swept model and actual lettering.
- The gramophone now has a hollow flared horn. The hourglass has an open outline around visible sand, the desk globe has fitted land shapes, and the harp strings fill the space between the frame and soundboard. Added rear details to several machine cabinets and connected the screw-press handle to its spindle. Light-colored edges on the pinwheel and a cream semaphore post keep their silhouettes visible against the teal station wall.

These are tabletop scene props. Seventeen have a working axle for the turn cue. The other 33 rotate as complete models. The checks cover staging on the supplied display pedestal and representative actor motions. Hand attachments, weighing dynamics, cloth, liquid flow and arbitrary placements use different interactions.

## Scientific instruments

| Reel | Prop kind | Turn cue |
|---|---|---|
| 0:00 | `balance_scale` | Whole model |
| 0:03 | `bench_microscope` | Whole model |
| 0:06 | `survey_telescope` | Whole model |
| 0:09 | `desk_globe` | Globe inside the stationary ring |
| 0:12 | `cup_anemometer` | Cup rotor |
| 0:15 | `brass_orrery` | Planet arms around the sun |
| 0:18 | `gimbal_compass` | Compass needle |
| 0:21 | `metronome` | Whole model |
| 0:24 | `desk_gyroscope` | Inner gimbal |
| 0:27 | `sand_timer` | Whole model |
| 0:30 | `seismograph` | Whole model |
| 0:33 | `laboratory_still` | Whole model |
| 0:36 | `telegraph_key` | Whole model |
| 0:39 | `recording_barometer` | Dial pointer |
| 0:42 | `tuning_fork` | Whole model |
| 0:45 | `binocular_viewer` | Whole model |
| 0:48 | `tabletop_radiometer` | Four vanes |

## Machines and mechanisms

| Reel | Prop kind | Turn cue |
|---|---|---|
| 0:51 | `gramophone` | Whole model |
| 0:54 | `film_projector` | Whole model |
| 0:57 | `cassette_deck` | Whole model |
| 1:00 | `typewriter` | Whole model |
| 1:03 | `rotary_telephone` | Whole model |
| 1:06 | `twin_bell_alarm` | Minute hand |
| 1:09 | `bellows_camera` | Whole model |
| 1:12 | `tabletop_jukebox` | Whole model |
| 1:15 | `sewing_machine` | Handwheel |
| 1:18 | `screw_press` | T-handle |
| 1:21 | `tabletop_fan` | Fan blades behind the guard |
| 1:24 | `beacon_tower` | Beacon lens |
| 1:27 | `coffee_grinder` | Hand crank |
| 1:30 | `combination_safe` | Combination dial |
| 1:33 | `pinwheel_box` | Pinwheel |
| 1:36 | `railway_semaphore` | Signal arm |
| 1:39 | `ferris_wheel` | Wheel and capsules |

## Miniatures and keepsakes

| Reel | Prop kind | Turn cue |
|---|---|---|
| 1:42 | `cable_car` | Whole model |
| 1:45 | `truss_bridge` | Whole model |
| 1:48 | `water_tower` | Whole model |
| 1:51 | `signal_gantry` | Whole model |
| 1:54 | `parcel_cart` | Whole model |
| 1:57 | `diving_helmet` | Whole model |
| 2:00 | `treasure_chest` | Whole model |
| 2:03 | `folding_easel` | Whole model |
| 2:06 | `stone_gateway` | Whole model |
| 2:09 | `well_and_winch` | Whole model |
| 2:12 | `rocking_horse` | Whole model |
| 2:15 | `model_sailboat` | Whole model |
| 2:18 | `desk_harp` | Whole model |
| 2:21 | `camping_stove` | Whole model |
| 2:24 | `bonsai_planter` | Whole model |
| 2:27 | `ceramic_teapot` | Whole model |
