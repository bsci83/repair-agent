# Series 60 — electrical and sensors family

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE papers.

## what this family covers

The electrical family routes the diagnosis when the symptom is
shutting_down, or when a no_start symptom's body becomes "cab fully
dead." The DDEC is a closed electrical system: every sensor
ground, every injector driver, and the ECA (engine control
actuator) are downstream of the ECM.

## sudden vs. stumble

A sudden shutdown with the cab still powered is fuel-supply or the
ECA itself. The ECA is the solenoid that the ECM uses to cut fuel
when the key is turned off; if it fails closed (no fuel) or fails
open (engine continues to run with key off), it can present as a
shutdown while the gauges stay live.

A stumble-then-stop is a sensor the ECM loses mid-cycle — most
often the CKP (crankshaft position), CMP (camshaft position), or
the rail-pressure sensor. The ECM may or may not log a code
depending on how the data went out of range.

## battery and grounds

A "cab fully dead" no-start is almost always battery, master
disconnect, or main ground. The Series 60 grounds in battery and the
cab; the cab-to-chassis ground strap is a common failure point.
Load-test the batteries first (a 12V cell battery should hold above
9.6V under load for 15 seconds), then inspect grounds.

## injector harness

The injector harness runs from the ECM, around the back of the
engine, and to each injector connector at the rocker cover. The
pass-through at the rocker cover is the chafe point. Family-wide
injector faults (the same code on every cylinder) point to the
harness, not the injectors.

## ECA and fuel solenoid

The ECA (engine control actuator) is the fuel shutoff solenoid.
When the key is on but the engine is stopped, the ECA should click
on key-on. A silent ECA is a dead ECA or no signal from the ECM. If
the ECA clicks but the engine still won't start, the fault is
downstream — fuel pressure, injector, or air.

## DDEC ECM connector

The ECM connector has many pins. Each pin is rated for a finite
number of insertions before the tension relaxes. A loose pin
presents as an intermittent sensor or a family-wide fault. Pull
the connector and inspect each pin for tension with a proper ECM
pin tool; replace the connector pigtail if any pin is loose.

## citations

- DDC Service Information Series 60, public-domain TSB
  13-07-71-008 (electrical diagnostics).
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport on ECM connector
  service.

## anchors

### #starter

Starter circuit fault. Check starter solenoid, neutral safety
switch, ignition switch signal. Cab-powered-but-no-crank.

### #battery

Battery, master disconnect, or main ground fault. Load-test
batteries (15-second load, 9.6V minimum); walk ground straps
between cab and chassis.

### #injector-harness

Injector harness chafe at the rocker cover pass-through, or ECM
connector pin tension. Family-wide injector codes = suspect harness,
not injectors.

### #eca

Engine Control Actuator (fuel shutoff solenoid). Should click on
key-on. Silent ECA = dead ECA or no ECM signal.