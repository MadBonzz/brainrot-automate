# Motion review · 50 additional performances

The 2 minute 2.75 second reel contains 50 chapters in the order below. Each chapter shows the same movement simultaneously from a three-quarter view and a side view at 12 fps. The object-handling sequences use imaginary props. A visible prop can be staged separately in the shot.

## What was checked

- Loaded the saved Blender Actions and measured every new performance on a stock character at 12 and 24 fps in Blender 4.3.2 on Linux. Checked the neutral frame before the cue, all authored channel keys, repeat or final hold, finite geometry, sole depth and specified foot plants. Also replayed each action with the shortest shot allowed by the late-cue rule.
- Checked 242 hand-position targets and 51 additional pose measurements at specified beats. The largest hand-position miss was 0.066 scene units after rounding up, within the specified tolerance. The largest horizontal drift during a declared foot plant was below 0.001 scene units. Airborne moves have separate takeoff and clearance checks where specified.
- Refined the time-out sign so one forearm crosses the upright forearm. Raised the free shoe during the tightrope weight shift. The review camera now fits the complete moving character in both views, including the half-turn hop.
- Rechecked the preceding 54 performances at both frame rates. Compared the eight original motions on the same saved pre-wrist cast before and after the wrist upgrade. Across every sampled frame, world transforms of the root, spine, head, both hands and both shoes agreed within 0.000001 per matrix element. The saved cast file kept its original SHA-256.
- Rendered three vertical two-actor shots with the production animation entry point using a saved pre-wrist lead and a newly built witness. Both characters could also use the same action. The three shots encoded all 27, 28 and 24 expected frames and were restored byte-for-byte from the shot cache. A separate check played one saved wrist action on two instances with staggered start times.

To reproduce a batch, replace `signals` in both paths below with `rhythm` or `daily_tasks` as needed. Read the resulting `checks.json` for measured values and individual errors.

```bash
blender -b --factory-startup --python-exit-code 1 --python tools/review_motions.py -- --batch signals --out review/signals --render
```

## Expressive gestures

| Reel time | Action | Movement |
|---|---|---|
| 0m 00.0s | `clap_three_times` | Open both arms and make three distinct palm contacts at chest height. |
| 0m 02.2s | `signal_timeout` | Hold one forearm across the top of the other to make a T, hold the signal and release. |
| 0m 04.4s | `quiet_please` | Bring a hand in front of the lips, hold, then signal downwards with the other palm. |
| 0m 06.8s | `me_then_you` | Touch the chest, pause, and extend the same hand straight toward the listener. |
| 0m 09.0s | `palms_together_thanks` | Meet the palms under the chin, dip the head, then separate them slowly. |
| 0m 11.4s | `blow_a_kiss` | Bring the palm to the mouth, tilt forward, then float the hand out and up. |
| 0m 13.8s | `sneeze_into_elbow` | Draw back, bring the crook of one elbow across the face, fold forward sharply, and recover. |
| 0m 16.2s | `stifle_a_yawn` | Raise a hand over the mouth on a slow backwards head tilt, then slump and let it fall. |
| 0m 18.9s | `dust_off_the_lapel` | Reach across the chest and brush lint off the opposite lapel twice. |
| 0m 21.1s | `hands_on_hips` | Put one hand and then the other on the hips, flare the elbows, and cock the head. |
| 0m 23.5s | `halt_at_the_corner` | Throw one palm forward, hold it as the head checks the corner, then slowly lower it. |
| 0m 25.7s | `call_across_the_room` | Cup both hands beside the mouth, lean out, then listen for an answer. |
| 0m 28.1s | `mime_binoculars` | Lift both hands to eye level, sight straight ahead and track something to the right. |
| 0m 30.6s | `signal_a_fork` | Bring the hands close together, then split them diagonally to indicate two possible routes. |
| 0m 32.8s | `zip_the_lips` | Pinch beside one corner of the mouth and trace a closed line across it. |
| 0m 35.2s | `hands_behind_the_back` | Sweep both arms behind the waist and hold a formal upright stance. |
| 0m 37.7s | `victory_double_pump` | Drive two bent arms above shoulder height, pull the elbows down, then pump overhead again. |

## Rhythm and footwork

| Reel time | Action | Movement |
|---|---|---|
| 0m 40.0s | `jumping_jack` | Spring outward with raised arms, land wide, then spring back to the starting stance. |
| 0m 42.1s | `half_turn_hop` | Wind up, rotate halfway around in the air, absorb the landing facing backwards. |
| 0m 44.3s | `grapevine_four_count` | Step sideways, cross the trailing foot behind, step out again and tap. |
| 0m 46.7s | `charleston_kick` | Flick the free foot forward, swing it behind with a bent knee, and counter-swing the arms. |
| 0m 49.1s | `skater_push_and_coast` | Push one leg diagonally behind, tuck the arms and coast on the other skate. |
| 0m 51.7s | `box_step` | Draw a four-corner dance step moving forward, side, back, then collect. |
| 0m 54.5s | `alternating_heel_digs` | Set the right heel out, collect, and repeat with the left while swinging the bent elbows. |
| 0m 57.6s | `stomp_then_freeze` | Wind the knee up, stamp down on the beat and stop in a wide bent-arm pose. |
| 0m 59.9s | `cross_body_knee_crunch` | Raise one knee towards the opposite elbow, release, and switch sides. |
| 1m 02.4s | `clock_face_foot_taps` | Keep the left shoe planted and tap the other foot towards twelve, three and six o’clock. |
| 1m 04.8s | `robot_isolations` | Move the head, then one forearm, then the other, with a separate held pose between accents. |
| 1m 07.2s | `body_wave` | Let a ripple pass from chin to chest to hips and knees, then roll upright. |
| 1m 09.6s | `backstroke_arm_drill` | Roll the shoulders and alternate an overhead recovery with the opposite arm’s downward sweep. |
| 1m 13.1s | `pendulum_leg_swing` | Balance on one foot and swing the free leg forward and back twice. |
| 1m 15.6s | `skip_an_imaginary_rope` | Circle both forearms outside the hips and make two quick hops as the rope passes underneath. |
| 1m 17.6s | `sprinter_push_off` | Lower into a staggered start, tip forward, drive the back knee through and pump the opposite arm. |
| 1m 20.1s | `tightrope_weight_shift` | Stretch the arms along a balance line, transfer weight on a narrow base, then lift the free shoe. |

## Everyday actions

| Reel time | Action | Movement |
|---|---|---|
| 1m 22.5s | `take_a_phone_call` | Lift a handset to the ear, listen, nod twice and lower it. |
| 1m 25.0s | `check_a_wristwatch` | Turn the left wrist face up, glance down, and tap the watch twice with the other hand. |
| 1m 27.3s | `sip_and_check_the_cup` | Raise a hot cup to the lips, tilt it gently, then lower it and peer inside. |
| 1m 29.9s | `pour_from_a_pitcher` | Hold a cup low, raise a pitcher above it, tip the wrist and return it upright. |
| 1m 32.4s | `wring_out_a_cloth` | Grip an imaginary cloth at two ends and twist the wrists in opposite directions twice. |
| 1m 35.1s | `type_then_press_enter` | Alternate hands on a keyboard, move the right hand out and strike Enter. |
| 1m 37.5s | `press_elevator_buttons` | Find a high button, press it twice, then lower the hand to a second button. |
| 1m 39.9s | `steer_an_s_curve` | Grip opposite sides of a wheel, steer left, countersteer, and straighten. |
| 1m 42.5s | `compose_a_snapshot` | Bring a camera up, level the frame, press the shutter and check the picture below. |
| 1m 44.9s | `compare_two_weights` | Act as a balance scale, weighing one palm, then the other, then bring both level. |
| 1m 47.4s | `deal_three_cards` | Hold the deck low and deal a card to each of three places across the table. |
| 1m 49.9s | `put_on_headphones` | Spread the ear cups above the temples, seat them over the ears, and adjust one side. |
| 1m 52.7s | `play_air_accordion` | Keep one keyboard hand steady while the other pulls and compresses the bellows twice. |
| 1m 55.2s | `strum_air_guitar` | Hold the neck out to one side, strike down and up twice, then let the last chord ring. |
| 1m 57.7s | `draw_a_curtain_open` | Take the curtain near the center, sweep it out to one side, hold it and look out. |
| 2m 00.1s | `ladle_and_serve` | Dip a ladle into a pot, lift it level, carry it sideways and tip it into the waiting bowl. |
