# Series 60 — cooling system family

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE papers.

## what this family covers

The cooling family routes the diagnosis when the symptom is
overheating or white_smoke. The agent's tree splits cooling by
behavior under load vs. at idle, and by whether coolant is being
lost or just kept too hot.

## climbs_under_load with coolant loss

If the engine climbs past 220°F under load AND you're losing
coolant, the question is internal vs. external leak. Sweet smell
from the exhaust (white sweet-smelling smoke) means coolant is
reaching combustion — suspect head gasket or the EPER (engine
protection/coolant cooler under the intake manifold). External
leak means pressure-test cold and walk the radiator, hoses, water
pump weep hole, and the EPER housing.

## climbs_under_load without coolant loss

If the engine climbs but coolant stays put, the issue is airflow
or flow. Walk the fan engagement, the shroud seal, and the radiator
core. A fan that doesn't engage is a fan clutch failure. A clean
fan but a clogged radiator is debris or bugs on the air side. A
clean fan, clean radiator, but still overheating under load, is
the water pump (low flow) or a thermostat stuck closed — verify
with a thermometer at the upper radiator hose.

## high_at_idle

If the engine runs hot even at idle, the issue is usually a sensor
or a thermostat that won't close. Verify with an infrared
thermometer at the thermostat housing — if the housing reads normal
but the gauge reads high, the sender or the gauge cluster is the
fault, not the engine.

## head_gasket and EPER

The EPER is a coolant cooler mounted under the intake manifold.
Its job is to cool the EGR charge before it enters the cylinders.
Internally, it can leak coolant into the intake — symptom is sweet-
smelling white smoke under load. A failed head gasket presents the
same way. Pressure-test cold and watch for bubbles at the surge
tank.

## water pump and thermostat

The water pump impeller is service item but rarely the first to
fail. When it does, it weeps from the front seal before it loses
the vanes. A stuck thermostat presents as the gauge climbing without
coolant loss; a stuck-OPEN thermostat presents as the engine
running cold under load.

## fan clutch

The viscous fan clutch is a service item. A dead clutch free-spins
cold and won't lock under heat. Spin-test from any point during a
cold start and compare to a known-good truck.

## radiator airflow

A blocked radiator core is a common cause of climbs-under-load.
Pull the fan shroud and inspect the air-side face. Bugs, debris,
or a collapsed shroud seal will starve the core without producing
an obvious leak.

## citations

- DDC Service Information Series 60, public-domain TSB
  13-36-71-002 (cooling system pressure and service).
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport on EPER and head-gasket
  diagnosis.

## anchors

### #eper

EPER (engine protection/coolant cooler) under the intake manifold.
Internal leak = coolant in intake, sweet white smoke. External leak
= coolant under the manifold. Pressure-test cold.

### #external-leak

External coolant leak. Pressure-test cold; walk the radiator,
hoses, water pump, EPER housing for seepage.

### #water-pump

Water pump failure. Weeps from the front seal before losing vanes.
Test the upper radiator hose for heat under load.

### #fan-clutch

Viscous fan clutch. Free-spinning cold = dead. Replace as a unit.

### #radiator-airflow

Radiator core blockage on the air side. Pull the shroud; inspect
for bugs, debris, or collapsed seal.

### #thermostat

Thermostat stuck open (engine cold under load) or stuck closed
(engine climbs under load without loss). Replace.

### #temp-sensor

Coolant temperature sender or gauge cluster fault. Verify with an
infrared thermometer at the housing; if housing reads normal but
gauge reads high, the sender or gauge is at fault.