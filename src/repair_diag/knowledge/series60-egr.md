# Series 60 — EGR and emissions family

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE papers.

## what this family covers

The EGR family is one of the smaller subtrees in the fault tree —
EGR-related complaints are a small fraction of Series 60 work,
but they're distinct enough that pulling them out of "electrical"
or "injector" makes the diagnosis cleaner. The family is gated by
"is the symptom accompanied by an EGR code or visible soot."

## the EGR cooler

The EGR cooler is mounted on the exhaust and is supposed to lower
the temperature of the recirculated exhaust gas before it enters
the intake. The cooler is a heat exchanger with coolant flowing
through it — internal coolant-to-exhaust leak is a known failure
mode. When it leaks, the symptom is sweet-smelling white smoke
under load, and the cooler can usually be diagnosed with a
pressure-test of the cooling system while the cooler is isolated.

A plugged cooler is a different failure — soot packs the cooler
cores from the exhaust side and chokes EGR flow. The symptom is
the engine falling on its face when the ECM commands EGR. The
fix is removal, clean, and inspect; replace if the cooler is
perforated or packed beyond cleaning.

## the EGR valve

The EGR valve opens on ECM command to admit recirculated exhaust
to the intake manifold. Carbon packing on the valve pintle is the
common failure — the valve sticks or its position sensor drifts.
A stuck valve presents as a code that returns immediately. A
drifting sensor presents as a code that's borderline — clears when
cold, comes back when the engine warms up.

## visible soot

Visible soot at the tailpipe that wasn't there a month ago is an
early-stage EGR fouling warning. The cooler and the valve are
packing. Cleaning before the cooler is fully plugged is preventive
maintenance — much cheaper than replacing a cooler.

## not-EGR

Some symptoms are routed to the EGR family in error — the customer
thinks it's an emissions problem because of smoke, but the actual
fault is fueling or cooling. The fault tree's last EGR node is
"not_egr": the symptom doesn't fit an EGR failure and should be
re-classified under injector, fuel, or electrical family. The
walk terminates at "not_egr" and the agent re-classifies.

## citations

- DDC Service Information Series 60, public-domain TSB
  13-28-72-013 (EGR cooler handling).
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport on EGR cooler service.

## anchors

### #cooler

EGR cooler failure. Internal coolant leak or soot packing.
Pressure-test cooling system with cooler isolated. Soot pack = clean
or replace.

### #valve

EGR valve stuck or position sensor drift. Carbon packing on pintle
is the common failure. Clean or replace.

### #soot

Soot buildup without a code — early-stage EGR fouling. Inspect the
valve and cooler; clean as preventive maintenance before the
cooler plugs.

### #not-egr

Symptom doesn't fit EGR. Re-classify under injector, fuel, or
electrical family and walk the appropriate subtree.