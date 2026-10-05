# Series 60 — injector and fueling family

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE papers.

## what this family covers

The injector family routes the diagnosis when the symptom is
rough_idle, black_smoke, or low_power — three different ways the
same underlying fault presents itself.

Most injector complaints on the Series 60 fall into one of four
buckets:

1. **A single injector has failed or is failing.** Cylinder-specific
   DDEC codes (e.g. SPN 651 FMI 7 on a single cylinder) point
   here. The fix is to swap the suspect injector with a neighbor
   and recheck — if the code follows the part, replace the injector.
2. **An injector is over-fueling.** Black smoke at idle, especially
   when warm, is most often a stuck-open injector dumping body. The
   injector balance test catches this directly.
3. **The injector harness or ECM driver is at fault.** Family-wide
   codes (the same SPN/FMI on every cylinder) point here. The fix is
   not the injectors — it's the wiring harness chafe at the rocker
   cover pass-through, or the ECM connector pin tension.
4. **Injector balance is off — every cylinder is slightly weak.**
   No codes, but the engine runs rough and the balance test shows
   a small drop on each cylinder. Suspect fuel pressure or a
   failing lift pump.

## fuel-block and fuel-supply

If the engine cranks but doesn't catch, the question is whether fuel
is reaching the filter housing. Open the bleed at the secondary
filter head briefly while someone cranks — if you see fuel, the
problem is past the filter (a plugged secondary filter, an air leak on
the suction side, or the injectors themselves). If you don't see
fuel, the problem is upstream — tank pickup, lift pump, primary
filter, or a stuck fuel-transfer pump on a multi-tank rig.

## balance test procedure

The DDEC supports an injector balance test that mechanically cuts
each cylinder one at a time and measures the RPM drop. A weak
cylinder drops less RPM than the others. Run the test on a warm
engine, in neutral, with the parking brake set. Watch the RPM drop
on the live-data stream rather than guessing.

A balance test that shows one weak cylinder means swap-and-test.
A balance test that shows all cylinders weak by similar amounts
means fuel pressure or air delivery, not the injectors.

## overfueling

Black smoke at idle is overfueling. The most common cause is a
stuck-open injector that won't close; the secondary cause is an
ECM fueling map that needs a reflash. Don't reflash before pulling
the balance. If the balance test passes, the ECM is the suspect.

## citations

- DDC Service Information Series 60, public-domain TSB
  13-07-71-008 (fuel system diagnostics).
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport on injector-balance
  procedures.

## anchors

### #fuel-block

When fuel is at the filter housing but the engine still doesn't
fire, suspect the secondary circuit. The secondary fuel filter
itself, the lines to the cylinder head, and the injector return
rails are the four points to walk. Look for kinks in the lines, an
air leak on the suction side, or a clogged secondary filter.

### #fuel-supply

When fuel is NOT at the filter housing, the fault is upstream. Tank
pickup screen, primary fuel filter, lift pump, and the fuel-transfer
pump on multi-tank rigs are the candidates. A quick visual check is
to crack the primary filter housing and see if the bowl is full.

### #balance-test

Run the DDEC injector balance test on a warm engine, in neutral,
parking brake set. Watch the RPM drop per cylinder. A single weak
cylinder means swap-and-test; an even-but-low drop means fuel
pressure or air delivery.

### #single-injector

A cylinder-specific SPN/FMI code, or a balance test showing one weak
cylinder, points to a single bad injector. Swap with a neighbor; if
the code follows, replace the injector.

### #overfueling

Black smoke at idle — overfueling. Pull the balance; if balance
passes, suspect ECM fueling map or reflash.