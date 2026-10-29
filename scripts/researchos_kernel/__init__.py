"""ResearchOS scheduling kernel (plan v4).

Stdlib only and free of private paths, so the same package ships in the public
starter. Dependencies point inward: clients (scripts/ros.py) -> adapters
(researchos_adapters) -> kernel. The kernel reads only its rule table and data contracts
(``rules``) and writes only its ledger family (``ledger``); the research graph is read by the
adapters and reaches the kernel as a snapshot. ``atomic_files`` is the one atomic-write and
lock owner; the server and data layers import it from here. The protocol contracts
(``admission_state``, ``candidate_envelope``, ``context_receipt``, ``handoff_receipt``,
``task_envelope``, ``result_contract``, ``rule_evolution``) are pure normalizers that every
client and the server share; they do no I/O.
"""

KERNEL_VERSION = "0.1.0"
