# Series 60 symptoms — the entry catalog

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** Procedures cited here are summaries of public DDC
> technical service bulletins and SAE-published diagnostic methods.

The diagnostic agent starts by asking which symptom brought the truck
in. The seven symptoms in the fault tree cover most of what walks
into a shop with a Series 60 problem.

## no_start

The engine doesn't fire. Either the starter turns and the engine
never catches (cranks_no_fire), or the cab is fully dead (no_crank).
The no_start family routes to fuel-system or starter-circuit
troubleshooting — the no_crank path is almost always electrical, and
the cranks_no_fire path is almost always fuel or a single sensor
that gates fuel.

A real no_start is rare on a Series 60 in good maintenance. Most
"won't start" complaints are intermittent sensors, water-in-fuel, or
a dead ECA (engine control actuator) that won't energise the fuel
solenoid. Verify the basics before pulling injectors.

## rough_idle

The engine runs but shakes at idle. Pulls or stumbles under no
throttle input. A rough idle that's also rough under load is most often
an injector cylinder dropping or a sensor the ECM uses for idle
control. A rough idle that's smooth under load is usually an idle
validation issue — vacuum leaks, throttle-by-wire calibration, or
the air intake path.

## overheating

The temperature gauge climbs past 220°F under load. The cooling
family in the agent's tree separates "climbs_under_load" from
"high_at_idle" — the load case is almost always a flow or heat-
exchange problem (water pump, fan, radiator), the idle case is
usually a sensor or a thermostat that won't close.

On a Series 60, the cooling system holds 28-32 quarts depending on
the application. Top off before testing pressure, and never open a hot
system without the slow-release technique.

## black_smoke

Black smoke at the tailpipe is unburnt fuel. At idle, it's overfueling
or a stuck-open injector. Under load, it's the same — the difference
is how much air the turbo can shove in. Black smoke that comes and
goes with engine temperature is usually the EGR valve carbon-
packed; black smoke that's constant is a stuck injector or a fueling
calibration that the ECM can't recover from.

## white_smoke

White smoke that smells sweet is coolant in combustion — head gasket,
EPER (engine protection/coolant cooler under the intake), or a
cracked EGR cooler leaking coolant into the exhaust. White smoke that
doesn't smell sweet, especially on a cold start that clears up, is
normal condensation. White smoke at idle that doesn't clear is a
real fault.

## low_power

The truck pulls less than expected, especially on grades. Most often
an injector that's under-fueling or a turbo that's not spinning up.
EGR cooler plugging or a stuck EGR valve can also feel like "low
power" because they rob the engine of intake air.

## shutting_down

The engine quits while running. Sudden shutdown with the cab still
powered is fuel or the ECA; stumble-then-stop is a sensor the ECM
loses mid-run. A stumble that recurs after a restart is a sensor
code coming back; a stumble that disappears is an intermittent
connector or a fuel-supply issue that fixed itself.

## citations

- DDC Service Information Series 60, public-domain TSBs 13-36-71-002
  (cooling), 13-28-72-013 (EGR), 13-07-71-008 (fueling).
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."
- Owner-forum syntheses from TruckersReport and Thetruckersreport
  on symptom-to-fault mapping.