"""The fault tree — the deterministic decision tree the agent asks through.

The tree is **data + a pure walk function.** No I/O, no model calls, no
globals. The model classifies the answer (yes / no / which); the code
decides which node comes next. ("The model classifies. The code
decides." — same commitment as ctrl-a-jr's pricing module, ported
from there.)

Each node holds:
- an `id` and a `question` (the text the agent reads aloud)
- `expected_keys` — the keys a valid answer can take
- `child` — answer_key -> next_node_id; the special key "_conclude"
  ends the walk with `conclusion` as the diagnosis
- `procedure` — a citation ref the agent surfaces when it lands here
- `conclusion` — the leaf label when the walk ends at this node
- `safety` — a safety-warning doc id if entering it (the agent must
  either cite the doc or surface the warning explicitly)

This module is the source of truth for `tree_walk_validity` and
`safety_warning_acknowledged` checks in `evals/checks.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

CONCLUDE = "_conclude"


@dataclass(frozen=True)
class Node:
    id: str
    question: str
    expected_keys: tuple[str, ...]
    child: Mapping[str, str]
    procedure: str | None = None
    conclusion: str | None = None
    safety: str | None = None


# The tree itself — eight fault families routed from one root.
# 32 nodes total: 1 root + 4 family roots + 3-5 nodes per family,
# 8 leaves with conclusions.
NODES: dict[str, Node] = {

    # --- root --------------------------------------------------------
    "root": Node(
        id="root",
        question=(
            "What symptom brings the truck in today? Pick the closest match."
        ),
        expected_keys=("no_start", "rough_idle", "overheating", "black_smoke",
                       "white_smoke", "low_power", "shutting_down"),
        child={
            "no_start": "fam_no_start",
            "rough_idle": "fam_injector",
            "overheating": "fam_cooling",
            "black_smoke": "fam_injector",
            "white_smoke": "fam_cooling",
            "low_power": "fam_injector",
            "shutting_down": "fam_electrical",
        },
        procedure="series60-symptoms.md",
    ),

    # --- fault family: NO START ------------------------------------
    "fam_no_start": Node(
        id="fam_no_start",
        question=(
            "When you turn the key, what happens — does the engine crank "
            "(starter turns) but not fire, or no crank at all?"
        ),
        expected_keys=("cranks_no_fire", "no_crank"),
        child={
            "cranks_no_fire": "ns_fuel",
            "no_crank": "ns_electrical",
        },
    ),

    "ns_fuel": Node(
        id="ns_fuel",
        question=(
            "Is there fuel at the inlet to the filter housing when you "
            "crank? (Open the bleed briefly while someone cranks.)"
        ),
        expected_keys=("yes", "no"),
        child={
            "yes": "conclude_fuel_block",
            "no": "conclude_fuel_supply",
        },
        safety="safety-warnings.md#hot-fuel-pressure",
    ),

    "ns_electrical": Node(
        id="ns_electrical",
        question=(
            "Do the dash lights come on when you turn the key, or is "
            "the cab fully dead?"
        ),
        expected_keys=("lights_only", "dead"),
        child={
            "lights_only": "conclude_starter_circuit",
            "dead": "conclude_battery_or_ground",
        },
    ),

    # --- fault family: INJECTOR / FUELING ------------------------
    "fam_injector": Node(
        id="fam_injector",
        question=(
            "Is the truck under load (going uphill, towing) when the "
            "symptom is worst, or is it bad at idle too?"
        ),
        expected_keys=("under_load_only", "idle_and_load"),
        child={
            "under_load_only": "inj_load_only",
            "idle_and_load": "inj_idle_load",
        },
        procedure="series60-injector.md",
    ),

    "inj_load_only": Node(
        id="inj_load_only",
        question=(
            "Do you have any active fault codes from DDEC? If yes, list "
            "the top two (SPN/FMI)."
        ),
        expected_keys=("no_codes", "codes_present"),
        child={
            "no_codes": "conclude_injector_balance",
            "codes_present": "inj_codes",
        },
    ),

    "inj_codes": Node(
        id="inj_codes",
        question=(
            "Are the codes cylinder-specific (one or two cylinders "
            "flagged), or are they family-wide (e.g. SPN 651 FMI 7)?"
        ),
        expected_keys=("cylinder_specific", "family_wide"),
        child={
            "cylinder_specific": "conclude_single_injector",
            "family_wide": "conclude_injector_wiring_or_harness",
        },
    ),

    "inj_idle_load": Node(
        id="inj_idle_load",
        question=(
            "Does the truck smoke visibly at idle? If so, which color?"
        ),
        expected_keys=("none", "black", "white", "blue"),
        child={
            "none": "conclude_injector_balance",
            "black": "conclude_overfueling",
            "white": "conclude_coolant_in_combustion",
            "blue": "conclude_oil_in_combustion",
        },
    ),

    # --- fault family: COOLING ---------------------------------
    "fam_cooling": Node(
        id="fam_cooling",
        question=(
            "Is the temperature gauge climbing past 220°F under load, "
            "or is it steady but high even at cold idle?"
        ),
        expected_keys=("climbs_under_load", "high_at_idle"),
        child={
            "climbs_under_load": "cool_load",
            "high_at_idle": "cool_idle",
        },
        procedure="series60-cooling.md",
    ),

    "cool_load": Node(
        id="cool_load",
        question=(
            "Is there visible coolant loss (low coolant light, coolant "
            "on the ground, or surge tank empty)?"
        ),
        expected_keys=("yes", "no"),
        child={
            "yes": "cool_loss",
            "no": "cool_airflow",
        },
        safety="safety-warnings.md#hot-coolant-pressure",
    ),

    "cool_loss": Node(
        id="cool_loss",
        question=(
            "Does the engine smell sweet (coolant in oil or combustion), "
            "or is the leak external and visible?"
        ),
        expected_keys=("sweet_smell", "external_leak"),
        child={
            "sweet_smell": "conclude_head_gasket_or_eper",
            "external_leak": "conclude_external_coolant_leak",
        },
    ),

    "cool_airflow": Node(
        id="cool_airflow",
        question=(
            "Are the fan clutch engaging (fan roar on a hot restart) "
            "and the radiator core clean on the air side?"
        ),
        expected_keys=("yes", "no_fan", "no_clean"),
        child={
            "yes": "conclude_water_pump_or_thermostat",
            "no_fan": "conclude_fan_clutch",
            "no_clean": "conclude_radiator_blocked",
        },
    ),

    "cool_idle": Node(
        id="cool_idle",
        question=(
            "Does the engine run cold (gauge barely moves off the C) "
            "under load?"
        ),
        expected_keys=("yes", "no"),
        child={
            "yes": "conclude_thermostat_stuck_open",
            "no": "conclude_sensor_or_gauge",
        },
    ),

    # --- fault family: ELECTRICAL / SENSORS ----------------------
    "fam_electrical": Node(
        id="fam_electrical",
        question=(
            "Does the engine shut down suddenly while running, or does "
            "it stumble and lose power first?"
        ),
        expected_keys=("sudden", "stumble_then_stop"),
        child={
            "sudden": "elec_sudden",
            "stumble_then_stop": "elec_stumble",
        },
        procedure="series60-electrical.md",
    ),

    "elec_sudden": Node(
        id="elec_sudden",
        question=(
            "When it shuts down, do the gauges stay live for a moment, "
            "or does the whole cab go dead?"
        ),
        expected_keys=("dead", "gauges_live"),
        child={
            "dead": "conclude_battery_or_ground",
            "gauges_live": "conclude_fuel_or_eca",
        },
    ),

    "elec_stumble": Node(
        id="elec_stumble",
        question=(
            "Is there a DDEC code stored, and if so does it come back "
            "immediately after clearing?"
        ),
        expected_keys=("no_code", "code_returns"),
        child={
            "no_code": "conclude_intermittent_sensor",
            "code_returns": "conclude_active_sensor_fault",
        },
    ),

    # --- fault family: EGR / EMISSIONS (path --------------------
    "fam_egr": Node(
        id="fam_egr",
        question=(
            "Is the symptom accompanied by an active EGR-related code "
            "(SPN 3251, 2791, 2634 family), or by visible soot at the "
            "tailpipe that wasn't there a month ago?"
        ),
        expected_keys=("code_present", "soot_only", "neither"),
        child={
            "code_present": "egr_code",
            "soot_only": "conclude_egr_soot_buildup",
            "neither": "conclude_not_egr",
        },
        procedure="series60-egr.md",
        safety="safety-warnings.md#hot-egr",
    ),

    "egr_code": Node(
        id="egr_code",
        question=(
            "Did the code appear after the truck sat for a few days, or "
            "did it come on during a hard run?"
        ),
        expected_keys=("after_sit", "during_run"),
        child={
            "after_sit": "conclude_egr_cooler_plugged",
            "during_run": "conclude_egr_valve_or_position",
        },
    ),

    # --- leaves (conclusions) ------------------------------------
    "conclude_fuel_block": Node(
        id="conclude_fuel_block",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-injector.md#fuel-block",
        conclusion="Likely fuel starvation past the filter housing — check fuel lines, primary filter, and the lift pump. Verify with the bleed at the secondary filter head.",
    ),
    "conclude_fuel_supply": Node(
        id="conclude_fuel_supply",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-injector.md#fuel-supply",
        conclusion="No fuel at the filter housing — fault is upstream. Check tank pickup, lift pump, and primary fuel filter.",
    ),
    "conclude_starter_circuit": Node(
        id="conclude_starter_circuit",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-electrical.md#starter",
        conclusion="Cab powered but no crank — starter circuit fault. Check starter solenoid, neutral safety switch, and ignition switch signal.",
    ),
    "conclude_battery_or_ground": Node(
        id="conclude_battery_or_ground",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-electrical.md#battery",
        conclusion="Cab fully dead — battery, master disconnect, or main ground fault. Load-test batteries and inspect grounds before joining.",
    ),
    "conclude_injector_balance": Node(
        id="conclude_injector_balance",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-injector.md#balance-test",
        conclusion="Run a cylinder contribution / injector balance test. If one or two cylinders drop, replace those injectors; if all drop, suspect fuel pressure or harness.",
    ),
    "conclude_single_injector": Node(
        id="conclude_single_injector",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-injector.md#single-injector",
        conclusion="Cylinder-specific code — one injector or its harness is at fault. Swap the suspect injector with a neighbor and recheck; if the code follows, replace the injector.",
    ),
    "conclude_injector_wiring_or_harness": Node(
        id="conclude_injector_wiring_or_harness",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-electrical.md#injector-harness",
        conclusion="Family-wide injector codes — fault is in the shared harness or the ECM driver, not the injectors themselves. Inspect harness chafing at the rocker cover pass-through and ECM connector pin tension.",
    ),
    "conclude_overfueling": Node(
        id="conclude_overfueling",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-injector.md#overfueling",
        conclusion="Black smoke at idle — overfueling or stuck-open injector. Pull injector balance and check for an injector that won't close.",
    ),
    "conclude_coolant_in_combustion": Node(
        id="conclude_coolant_in_combustion",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#eper",
        conclusion="White sweet-smelling smoke — coolant in combustion. Likely head gasket or EPER (coolant cooler under the intake). Pressure-test the cooling system with the radiator cap off and look for bubbles.",
        safety="safety-warnings.md#hot-coolant-pressure",
    ),
    "conclude_oil_in_combustion": Node(
        id="conclude_oil_in_combustion",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-sensors.md#oil-consumption",
        conclusion="Blue smoke — oil in combustion. Worn valve guides or turbo seal. Compression test plus leak-down to localize.",
    ),
    "conclude_head_gasket_or_eper": Node(
        id="conclude_head_gasket_or_eper",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#eper",
        conclusion="Coolant loss with sweet smell — head gasket or EPER (engine protection/coolant cooler under the intake manifold). Pressure-test and inspect the EPER for internal leak.",
        safety="safety-warnings.md#hot-coolant-pressure",
    ),
    "conclude_external_coolant_leak": Node(
        id="conclude_external_coolant_leak",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#external-leak",
        conclusion="External coolant leak — pressurize the system cold and walk the radiator, hoses, water pump weep hole, and the EPER housing for seepage.",
    ),
    "conclude_water_pump_or_thermostat": Node(
        id="conclude_water_pump_or_thermostat",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#water-pump",
        conclusion="Climbs under load but no loss — likely water pump (low flow) or stuck-closed thermostat. Verify fan engagement and check the upper radiator hose for heat at operating temp; if cool, the thermostat is stuck.",
    ),
    "conclude_fan_clutch": Node(
        id="conclude_fan_clutch",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#fan-clutch",
        conclusion="Fan not engaging under load — fan clutch failure. Spin the fan cold; if it free-spins, the viscous clutch is dead.",
    ),
    "conclude_radiator_blocked": Node(
        id="conclude_radiator_blocked",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#radiator-airflow",
        conclusion="Radiator airflow fault. Pull the fan shroud and inspect the radiator core face; bugs, debris, or a collapsed shroud seal will starve the core.",
    ),
    "conclude_thermostat_stuck_open": Node(
        id="conclude_thermostat_stuck_open",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-cooling.md#thermostat",
        conclusion="Engine cold under load — thermostat stuck open. Replace; a stuck-open thermostat mimics a cold-running engine and robs heat under load.",
    ),
    "conclude_sensor_or_gauge": Node(
        id="conclude_sensor_or_gauge",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-sensors.md#temp-sensor",
        conclusion="Temperature gauge fault — verify with an infrared thermometer at the thermostat housing. If the housing reads normal but the gauge reads high, the sender or gauge cluster is at fault.",
    ),
    "conclude_fuel_or_eca": Node(
        id="conclude_fuel_or_eca",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-electrical.md#eca",
        conclusion="Sudden shutdown with cab still powered — likely fuel solenoid (ECA) or a fuel-supply interruption, not an electrical fault. Verify fuel pressure at the secondary filter head and check the ECA for click on key-on.",
    ),
    "conclude_intermittent_sensor": Node(
        id="conclude_intermittent_sensor",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-sensors.md#intermittent",
        conclusion="No active code but stumble — intermittent sensor or connector. With the engine running, wiggle the harness at the most likely connectors (CKP, CMP, MAP) and see if the stumble reproduces.",
    ),
    "conclude_active_sensor_fault": Node(
        id="conclude_active_sensor_fault",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-sensors.md#active-sensor",
        conclusion="Active sensor fault — replace the sensor named by the code. If the same code returns immediately after replacement, the harness or ECM pin is the real fault, not the sensor.",
    ),
    "conclude_egr_cooler_plugged": Node(
        id="conclude_egr_cooler_plugged",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-egr.md#cooler",
        conclusion="EGR code after the truck sat — EGR cooler plugged with soot. Remove, clean, and pressure-test; replace if the cooler is perforated or the cores are packed.",
        safety="safety-warnings.md#hot-egr",
    ),
    "conclude_egr_valve_or_position": Node(
        id="conclude_egr_valve_or_position",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-egr.md#valve",
        conclusion="EGR code during a hard run — EGR valve stuck or position sensor drift. Remove the valve and check for carbon packing; clean or replace.",
        safety="safety-warnings.md#hot-egr",
    ),
    "conclude_egr_soot_buildup": Node(
        id="conclude_egr_soot_buildup",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-egr.md#soot",
        conclusion="Soot buildup without a code — early-stage EGR fouling. Inspect the valve and cooler for carbon; clean as preventive maintenance before the cooler plugs.",
        safety="safety-warnings.md#hot-egr",
    ),
    "conclude_not_egr": Node(
        id="conclude_not_egr",
        question="(conclude)",
        expected_keys=(),
        child={},
        procedure="series60-egr.md#not-egr",
        conclusion="Not EGR — symptom doesn't fit an EGR failure. Re-classify under injector, fuel, or electrical family and walk the appropriate subtree.",
    ),
}


def get_node(node_id: str) -> Node:
    """Look up a node by id. Raises KeyError if the node doesn't exist —
    the eval harness counts that as a tree_walk_validity failure."""
    return NODES[node_id]


def walk(start: str, answers: Mapping[str, str]) -> tuple[list[str], str]:
    """Walk the fault tree deterministically.

    `start` is the root node id (usually `"root"`); `answers` is a
    mapping of node_id -> the answer key given at that node.

    Returns `(path, conclusion)` where `path` is the list of node ids
    visited in order, and `conclusion` is the leaf's `conclusion`
    text. The walk stops at the first node whose answer is
    `_conclude` (the special key) OR whose `child[answer]` is
    `_conclude`.

    Raises `KeyError` if a node id is unknown OR an answer key is not
    in `expected_keys` — the eval harness treats both as failures
    rather than silently picking a default.
    """
    path: list[str] = []
    current = start
    while True:
        node = NODES[current]  # KeyError => unknown node
        path.append(node.id)

        answer = answers.get(node.id)
        if answer is None:
            raise KeyError(f"no answer given for node {node.id!r}")

        if answer not in node.expected_keys:
            raise KeyError(
                f"node {node.id!r}: answer {answer!r} not in expected_keys "
                f"{node.expected_keys!r}"
            )

        next_id = node.child.get(answer)
        if next_id is None:
            raise KeyError(
                f"node {node.id!r}: answer {answer!r} has no child defined"
            )

        if next_id == CONCLUDE:
            return path, node.conclusion or ""
        # A leaf node — its `child` map is empty, so walking into it
        # would expect an answer that doesn't exist. Treat the leaf
        # itself as the conclusion.
        next_node = NODES.get(next_id)
        if next_node is None:
            raise KeyError(
                f"node {node.id!r}: child {next_id!r} does not exist"
            )
        if not next_node.child:
            path.append(next_node.id)
            return path, next_node.conclusion or ""
        current = next_id


def root_id() -> str:
    """The root node id, exposed for the CLI to seed the walk."""
    return "root"