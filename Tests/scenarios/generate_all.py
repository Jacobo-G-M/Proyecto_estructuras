"""
Tests / scenarios / generate_all.py
Script to generate and validate all 6 JSON test scenarios required by Section 16 of SismoLab AVL.
"""

import os
import sys
import json
import copy
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Business.observatory import Observatory
from Business.geographical_map import Geographical_map
from Models.event import Event
from Models.node import Node
from Models.report import Report
from Models.station import Station
from Models.zone import Zone
from Business.scenario_persistence import ScenarioPersistence


OUTPUT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "saved_versions", "test_cases"))


def run_case_1():
    print("=== Generating Caso 1: Límites y Empates ===")
    obs = Observatory()
    z1 = Zone(1, "Zona Central Metropolitana", True, (300.0, 500.0), (300.0, 500.0))
    obs.geographical_map = Geographical_map(zones=[z1])

    st1 = Station(1, "Estacion Alfa", (400.0, 400.0))
    obs.stations = [st1]
    obs.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)

    # Evento B: M=4.5, H=30.0 fuera de zona -> P=2
    ev_b = obs.create_event(10, 4.5, 30.0, (200.0, 400.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    # Evento D: M=5.0, H=40.0, ID=20 -> P=2
    ev_d = obs.create_event(20, 5.0, 40.0, (200.0, 400.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    # Evento E: M=5.0, H=40.0, ID=35 -> P=2 (desempate con D por ID)
    ev_e = obs.create_event(35, 5.0, 40.0, (200.0, 400.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    # Evento A: M=4.5, H=30.0 exactamente en el borde x=300.0 de zona poblada -> P=3
    ev_a = obs.create_event(50, 4.5, 30.0, (300.0, 400.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    # Evento C: M=6.0, H=100.0 en cualquier zona -> P=3
    ev_c = obs.create_event(60, 6.0, 100.0, (100.0, 100.0), datetime(2026, 10, 4, 10, 0, 0), st1)

    assert ev_a.priority == 3, f"Expected P=3, got {ev_a.priority}"
    assert ev_b.priority == 2, f"Expected P=2, got {ev_b.priority}"
    assert ev_c.priority == 3, f"Expected P=3, got {ev_c.priority}"
    assert ev_d.priority == 2, f"Expected P=2, got {ev_d.priority}"
    assert ev_e.priority == 2, f"Expected P=2, got {ev_e.priority}"

    data = ScenarioPersistence.export_to_dict(obs)
    errs = ScenarioPersistence.validate_topology_data(data)
    assert len(errs) == 0, f"Errors in Case 1: {errs}"

    filepath = os.path.join(OUTPUT_DIR, "caso1_limites_empates.json")
    ScenarioPersistence.export_to_json(obs, filepath)
    print(f"  -> Exported to {filepath} (0 validation errors)")


def run_case_2():
    print("=== Generating Caso 2: Corrección y Reporte Antiguo ===")
    obs = Observatory()
    st1 = Station(1, "Estacion S1", (500.0, 500.0))
    obs.stations = [st1]
    obs.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)

    # Context events to appreciate tree structure
    obs.create_event(50, 4.2, 50.0, (500.0, 500.0), datetime(2026, 10, 4, 7, 0, 0), st1)
    obs.create_event(200, 6.0, 20.0, (500.0, 500.0), datetime(2026, 10, 4, 7, 30, 0), st1)
    obs.create_event(300, 6.5, 10.0, (500.0, 500.0), datetime(2026, 10, 4, 7, 45, 0), st1)

    # Initial event ID 100: M=4.8, H=70.0, P=2, Review 1
    ev100 = obs.create_event(100, 4.8, 70.0, (500.0, 500.0), datetime(2026, 10, 4, 8, 0, 0), st1)
    assert ev100.priority == 2
    assert ev100.review == 1
    assert ev100.get_key() == (2, 4.8, 100)

    # Prepare initial report queue with:
    # 1. Accepted correction: Rev 2, M=6.2, H=15.0 -> P=3
    # 2. Outdated report: Rev 1, M=4.8, H=70.0 -> to be discarded
    r_corr = Report(
        id=100,
        magnitude=6.2,
        depth=15.0,
        epicenter=(500.0, 500.0),
        date_time=datetime(2026, 10, 4, 8, 0, 0),
        review=2,
        origin_station=[st1]
    )
    r_old = Report(
        id=100,
        magnitude=4.8,
        depth=70.0,
        epicenter=(500.0, 500.0),
        date_time=datetime(2026, 10, 4, 8, 0, 0),
        review=1,
        origin_station=[st1]
    )

    obs.report_queue.enqueue(r_corr)
    obs.report_queue.enqueue(r_old)

    # Save initial state BEFORE processing reports
    filepath_init = os.path.join(OUTPUT_DIR, "caso2_correccion_reporte_antiguo_inicial.json")
    ScenarioPersistence.export_to_json(obs, filepath_init)
    print(f"  -> Initial state exported to {filepath_init}")

    # Process step 1: Correction Accepted
    res1 = obs.process_report_step()
    assert res1["decision"] == "Correction Accepted"
    assert obs.events_dict[100].priority == 3
    assert obs.events_dict[100].review == 2
    assert obs.events_dict[100].get_key() == (3, 6.2, 100)
    assert obs.metrics.corrections_accepted == 1

    # Process step 2: Outdated Report Discarded
    res2 = obs.process_report_step()
    assert res2["decision"] == "Discarded: Outdated Revision"
    assert obs.events_dict[100].review == 2
    assert obs.events_dict[100].get_key() == (3, 6.2, 100)
    assert obs.metrics.discarded_reports == 1

    # Save final state AFTER processing both reports
    filepath_final = os.path.join(OUTPUT_DIR, "caso2_correccion_reporte_antiguo_final.json")
    ScenarioPersistence.export_to_json(obs, filepath_final)
    print(f"  -> Processed final state exported to {filepath_final}")


def run_case_3():
    print("=== Generating Caso 3: Reporte Tardío y Réplicas ===")
    obs = Observatory()
    obs.distance_epicenter = 40.0
    obs.max_time = 48.0
    obs.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)
    st1 = Station(1, "Central", (400.0, 400.0))
    obs.stations = [st1]

    # Event 1: 10:00, M=5.6, (400.0, 400.0)
    ev1 = obs.create_event(1, 5.6, 20.0, (400.0, 400.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    # Event 2: 10:20, M=4.2, (410.0, 405.0) -> replica of Event 1
    ev2 = obs.create_event(2, 4.2, 15.0, (410.0, 405.0), datetime(2026, 10, 4, 10, 20, 0), st1)

    assert len(obs.associations) == 1
    assert obs.associations[0].chosen_reference.id == 1
    assert [r.id for r in obs.associations[0].referenced_by] == [2]

    # Report for Event 3 (Llega después pero ocurrió ANTES: 09:55, M=6.1, (402.0, 403.0))
    r3 = Report(
        id=3,
        magnitude=6.1,
        depth=12.0,
        epicenter=(402.0, 403.0),
        date_time=datetime(2026, 10, 4, 9, 55, 0),
        review=1,
        origin_station=[st1]
    )
    obs.report_queue.enqueue(r3)

    # Save state before late arrival is processed
    filepath_pre = os.path.join(OUTPUT_DIR, "caso3_reporte_tardio_antes.json")
    ScenarioPersistence.export_to_json(obs, filepath_pre)

    # Process step in queue: late report arrives and creates event 3 with reclustering
    res3 = obs.process_report_step()
    assert res3["decision"] == "New Event Registered"
    assert 3 in obs.events_dict

    # Associations should now have EV-3 as chosen_reference, and [1, 2] as replicas
    assert len(obs.associations) == 1
    assoc = obs.associations[0]
    assert assoc.chosen_reference.id == 3
    replica_ids = sorted([r.id for r in assoc.referenced_by])
    assert replica_ids == [1, 2], f"Expected replicas [1, 2], got {replica_ids}"

    filepath_post = os.path.join(OUTPUT_DIR, "caso3_reporte_tardio_despues.json")
    ScenarioPersistence.export_to_json(obs, filepath_post)
    print(f"  -> Re-associated state exported to {filepath_post}")


def run_case_4():
    print("=== Generating Caso 4: Rotaciones y Modo Estrés ===")
    st1 = Station(1, "Estacion S1", (500.0, 500.0))

    # --- Part A: Sequence of insertions demonstrating LL, RR, LR, RL ---
    # We create an insertion list JSON suitable for load_by_insertions
    insertions_list = [
        # LL trigger: 30, 20, 10
        {"id": 30, "magnitude": 4.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:00:00", "review": 1},
        {"id": 20, "magnitude": 4.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:05:00", "review": 1},
        {"id": 10, "magnitude": 4.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:10:00", "review": 1},
        # RR trigger: 40, 50, 60
        {"id": 40, "magnitude": 5.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:15:00", "review": 1},
        {"id": 50, "magnitude": 5.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:20:00", "review": 1},
        {"id": 60, "magnitude": 5.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:25:00", "review": 1},
        # LR trigger: 80, 70, 75
        {"id": 80, "magnitude": 6.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:30:00", "review": 1},
        {"id": 70, "magnitude": 6.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:35:00", "review": 1},
        {"id": 75, "magnitude": 6.0, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:40:00", "review": 1},
        # RL trigger: 85, 95, 90
        {"id": 85, "magnitude": 6.2, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:45:00", "review": 1},
        {"id": 95, "magnitude": 6.2, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:50:00", "review": 1},
        {"id": 90, "magnitude": 6.2, "depth": 20.0, "epicenter": [500.0, 500.0], "date_time": "2026-10-04T01:55:00", "review": 1},
    ]

    filepath_seq = os.path.join(OUTPUT_DIR, "caso4_rotaciones_secuencia.json")
    with open(filepath_seq, "w", encoding="utf-8") as f:
        json.dump({"events": insertions_list}, f, indent=2)
    print(f"  -> Insertion sequence exported to {filepath_seq}")

    # Validate that load_by_insertions executes without errors
    cmp_res = ScenarioPersistence.load_by_insertions(filepath_seq)
    print(f"  -> AVL vs BST comparison: AVL height={cmp_res['metrics']['avl_height']}, BST height={cmp_res['metrics']['bst_height']}")

    # --- Part B: Stress Mode and Recovery ---
    obs_stress = Observatory()
    obs_stress.stress_mode = True
    obs_stress.stations = [st1]
    obs_stress.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)

    # Insert events in strictly ascending key order
    for idx in [1, 2, 3, 4, 5, 6, 7]:
        obs_stress.create_event(idx, 4.0, 10.0, (500.0, 500.0), datetime(2026, 10, 4, 1, 0, 0), st1)

    # Verify degenerated tree
    assert obs_stress.tree.root.id == 1
    assert abs(obs_stress.tree.root.balance_factor()) > 2, f"Expected |BF| > 2, got {obs_stress.tree.root.balance_factor()}"

    # Export degenerated stress topology
    filepath_stress = os.path.join(OUTPUT_DIR, "caso4_estres_desbalanceado.json")
    ScenarioPersistence.export_to_json(obs_stress, filepath_stress)
    print(f"  -> Degenerated stress topology exported to {filepath_stress}")

    # Recover balance via global_recovery (calls tree.restore_balance())
    obs_stress.global_recovery()
    assert obs_stress.stress_mode is False
    assert abs(obs_stress.tree.root.balance_factor()) <= 1
    # Check all nodes have |BF| <= 1
    for nd in obs_stress.tree.preorder():
        assert abs(nd.balance_factor()) <= 1

    filepath_rec = os.path.join(OUTPUT_DIR, "caso4_estres_recuperado.json")
    ScenarioPersistence.export_to_json(obs_stress, filepath_rec)
    print(f"  -> Rebalanced restored topology exported to {filepath_rec}")


def run_case_5():
    print("=== Generating Caso 5: Archivo Masivo de Subárboles ===")
    obs = Observatory()
    st1 = Station(1, "Central", (500.0, 500.0))
    obs.stations = [st1]
    obs.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)
    obs.max_tree_age = 72

    # Old date: 98 hours ago (> 72 hours)
    dt_old = datetime(2026, 9, 30, 10, 0, 0)
    # Recent date: 2 hours ago (keeps global root 50 from being eligible)
    dt_recent = datetime(2026, 10, 4, 10, 0, 0)

    # Global root: Node 50 (recent date)
    obs.create_event(50, 3.5, 10.0, (500.0, 500.0), dt_recent, st1)

    # Subtree A (Eligible, 3 nodes: 12, 10, 14, all P=1, all age > 72h)
    obs.create_event(12, 2.5, 10.0, (500.0, 500.0), dt_old, st1)  # root of A
    obs.create_event(10, 2.0, 10.0, (500.0, 500.0), dt_old, st1)  # left of A
    obs.create_event(14, 3.0, 10.0, (500.0, 500.0), dt_old, st1)  # right of A

    # Subtree B (NOT Eligible: root 62, left 60, right 70 has P=2)
    obs.create_event(62, 4.2, 10.0, (500.0, 500.0), dt_old, st1)  # root of B (P=1, age>72)
    obs.create_event(60, 4.0, 10.0, (500.0, 500.0), dt_old, st1)  # left of B (P=1, age>72)
    obs.create_event(70, 5.0, 10.0, (500.0, 500.0), dt_old, st1)  # right of B (P=2! DISQUALIFIES B)

    # Save initial topology before archiving
    filepath_init = os.path.join(OUTPUT_DIR, "caso5_archivo_subarboles.json")
    ScenarioPersistence.export_to_json(obs, filepath_init)
    print(f"  -> Pre-archival topology exported to {filepath_init}")

    # Preview archival
    prev = obs.archive_subtree(execute=False)
    assert prev["best_root_id"] == 12, f"Expected Subtree A root 12, got {prev['best_root_id']}"
    assert prev["count"] == 3
    assert set(prev["affected_ids"]) == {10, 12, 14}

    # Execute mass archival
    res = obs.archive_subtree(execute=True)
    assert len(obs.historic.archived) == 3
    assert set(obs.historic.archived.keys()) == {10, 12, 14}
    assert 12 not in obs.events_dict
    assert 10 not in obs.events_dict
    assert 14 not in obs.events_dict
    assert 70 in obs.events_dict  # Subtree B remains untouched!
    assert 62 in obs.events_dict
    assert 60 in obs.events_dict

    # Save topology after archiving
    filepath_archived = os.path.join(OUTPUT_DIR, "caso5_archivo_subarboles_post_archivo.json")
    ScenarioPersistence.export_to_json(obs, filepath_archived)
    print(f"  -> Post-archival topology exported to {filepath_archived}")

    # Test Undo of mass archive
    undo_res = obs.undo_action()
    assert undo_res is not None
    assert len(obs.historic.archived) == 0
    assert 12 in obs.events_dict
    assert 10 in obs.events_dict
    assert 14 in obs.events_dict
    print("  -> Undo action executed successfully: restored all 3 nodes.")


def run_case_6():
    print("=== Generating Caso 6: Persistencia, Consistencia y Rechazo ===")
    obs = Observatory()
    st1 = Station(1, "Central", (500.0, 500.0))
    obs.stations = [st1]
    obs.clock_simulation = datetime(2026, 10, 4, 12, 0, 0)

    # Base valid scenario
    obs.create_event(10, 5.0, 20.0, (500.0, 500.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    obs.create_event(20, 5.5, 20.0, (500.0, 500.0), datetime(2026, 10, 4, 10, 0, 0), st1)
    base_dict = ScenarioPersistence.export_to_dict(obs)

    # 1. Error: BST ordering violation (left child with key > parent)
    bad_bst = copy.deepcopy(base_dict)
    # Force Node 20 as left child of Node 10
    for nd in bad_bst["tree"]["nodes"]:
        if nd["id"] == 10:
            nd["left_id"] = 20
            nd["right_id"] = None
        elif nd["id"] == 20:
            nd["left_id"] = None
            nd["right_id"] = None
    errs_bst = ScenarioPersistence.validate_topology_data(bad_bst)
    assert any("Global BST order violation" in e for e in errs_bst), f"Expected BST violation, got: {errs_bst}"
    fp_bst = os.path.join(OUTPUT_DIR, "caso6_error_bst_invalido.json")
    with open(fp_bst, "w", encoding="utf-8") as f:
        json.dump(bad_bst, f, indent=2)
    print(f"  -> 1. Bad BST exported to {fp_bst} (Rejected: {errs_bst[0]})")

    # 2. Error: Duplicate IDs across active and historic
    bad_dup = copy.deepcopy(base_dict)
    # Put Node 10 in historic.archived as well
    ev10_data = copy.deepcopy(bad_dup["tree"]["nodes"][0]["event"])
    bad_dup["historic"]["archived"].append(ev10_data)
    errs_dup = ScenarioPersistence.validate_topology_data(bad_dup)
    assert any("ID overlap between active and archived" in e for e in errs_dup), f"Expected duplicate error, got: {errs_dup}"
    fp_dup = os.path.join(OUTPUT_DIR, "caso6_error_ids_duplicados.json")
    with open(fp_dup, "w", encoding="utf-8") as f:
        json.dump(bad_dup, f, indent=2)
    print(f"  -> 2. Duplicate IDs exported to {fp_dup} (Rejected: {errs_dup[0]})")

    # 3. Error: Inconsistent heights / balance factors
    bad_h = copy.deepcopy(base_dict)
    # Tamper with height and BF of node 20
    for nd in bad_h["tree"]["nodes"]:
        if nd["id"] == 20:
            nd["height"] = 99
            nd["balance_factor"] = -7
    errs_h = ScenarioPersistence.validate_topology_data(bad_h)
    assert any("stored height 99 does not match" in e for e in errs_h)
    assert any("stored balance factor -7 does not match" in e for e in errs_h)
    fp_h = os.path.join(OUTPUT_DIR, "caso6_error_alturas_inconsistentes.json")
    with open(fp_h, "w", encoding="utf-8") as f:
        json.dump(bad_h, f, indent=2)
    print(f"  -> 3. Inconsistent heights exported to {fp_h} (Rejected: {errs_h})")

    # 4. Error: Unbalanced tree loaded in normal mode (stress_mode: false)
    # Create chain 10 -> 20 -> 30 with balance factor -2
    chain_dict = copy.deepcopy(base_dict)
    chain_dict["stress_mode"] = False
    chain_dict["tree"]["root_id"] = 10
    ev30 = copy.deepcopy(bad_dup["tree"]["nodes"][1]["event"])
    ev30["id"] = 30
    ev30["magnitude"] = 5.8
    ev30["priority"] = 2
    chain_dict["tree"]["nodes"] = [
        {
            "id": 10,
            "left_id": None,
            "right_id": 20,
            "height": 2,
            "balance_factor": -2,
            "event": bad_dup["tree"]["nodes"][0]["event"]
        },
        {
            "id": 20,
            "left_id": None,
            "right_id": 30,
            "height": 1,
            "balance_factor": -1,
            "event": bad_dup["tree"]["nodes"][1]["event"]
        },
        {
            "id": 30,
            "left_id": None,
            "right_id": None,
            "height": 0,
            "balance_factor": 0,
            "event": ev30
        }
    ]
    errs_unbal = ScenarioPersistence.validate_topology_data(chain_dict)
    assert any("Unbalanced topology" in e for e in errs_unbal), f"Expected unbalanced error, got: {errs_unbal}"
    fp_unbal = os.path.join(OUTPUT_DIR, "caso6_error_desbalance_sin_estres.json")
    with open(fp_unbal, "w", encoding="utf-8") as f:
        json.dump(chain_dict, f, indent=2)
    print(f"  -> 4. Unbalanced without stress exported to {fp_unbal} (Rejected: {errs_unbal[0]})")


if __name__ == "__main__":
    run_case_1()
    run_case_2()
    run_case_3()
    run_case_4()
    run_case_5()
    run_case_6()
    print("\n>>> ALL 6 CASES GENERATED AND VALIDATED 100% SUCCESSFULLY! <<<")
