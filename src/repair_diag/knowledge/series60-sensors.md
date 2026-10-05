# Series 60 — sensors reference

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE papers.

## what this doc covers

The electrical family cites back to this doc when the symptom is a
sensor fault rather than a wiring or component fault. Sensors fail
in three modes: dead (no signal ever), stuck (signal out of range
but present), and intermittent (works most of the time).

## coolant temperature sensor

The CTS is a thermistor that changes resistance with temperature. A
plugged CTS makes the engine run rich because the ECM sees
"cold" all the time. A dead CTS lights the gauge. Verify with an
infrared thermometer at the housing — if housing and gauge disagree,
the sender is suspect.

## crankshaft position sensor (CKP)

The CKP is the primary position sensor. A dead CKP means no fuel
runs and no DDEC communication. A stuck CKP presents as a hard
start, a code that returns immediately, and a no-fire condition.
A intermittent CKP is a connector chafe at the bellhousing pass-
through or at the sensor itself.

## camshaft position sensor (CMP)

The CMP gives the ECM the phase reference for injection timing.
A dead CMP on a Series 60 with electronic unit injectors means no
fire — the ECM refuses to fire without phase confirmation. A stuck
CMP presents as a code that returns after clearing and a noticeable
power loss.

## MAP and boost sensors

The MAP sensor measures intake manifold pressure. A plugged MAP
sensor line (carbon, oil) presents as a low-power complaint without
a code. A dead MAP sensor lights a code and limits power. Boost is
measured downstream of the turbo and is the ECM's reference for
fueling dose under boost.

## rail-pressure sensor

The rail-pressure sensor measures common-rail pressure. The
Series 60's fuel system holds pressure at idle, and a failing rail-
pressure sensor presents as a stumble under boost or a hard-start
after the truck sits for a day. A dead rail-pressure sensor
prevents fuel delivery entirely.

## oil-in-combustion sensors

There is no direct sensor for "oil in combustion" — diagnosis is by
blue smoke at the tailpipe plus a consumption test. A consumption
test: fill the oil to the upper mark, run the engine for a measured
mileage or hours, refill to the upper mark, measure the volume
added. Series 60 oil consumption over 1 qt per 1,000 miles is the
common threshold for service.

## citations

- DDC Service Information Series 60, public-domain TSBs on sensor
  service and connector inspection.
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport on sensor diagnostics.

## anchors

### #intermittent

Intermittent sensor or connector chafe. With the engine running,
wiggle the harness at the suspect connector (CKP, CMP, MAP) and see
if the stumble reproduces. Code-free + stumble = suspect
intermittent, not a hard sensor fault.

### #active-sensor

Active sensor fault — replace the sensor named by the code. If the
code returns immediately, the harness or ECM pin is the real
fault, not the sensor.

### #oil-consumption

Oil-in-combustion diagnosis. Run a measured consumption over a known
distance or work hours. Series 60 threshold is roughly 1 qt per
1,000 miles. Above that, walk the turbo seal and the valve guides.

### #temp-sensor

Coolant temperature sender. Verify with an infrared thermometer;
if housing reads normal but gauge reads high, the sender or gauge
is at fault.