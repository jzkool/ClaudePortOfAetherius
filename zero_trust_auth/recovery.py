import datetime
import os
import uuid


def request_recovery(user_identifier: str) -> str:
    """
    Log an in-person recovery request and return a one-time reference code.

    No key material is generated or transmitted digitally. The reference
    code must be brought physically to the issuing authority alongside
    valid government-issued photo ID.
    """
    if not user_identifier or not user_identifier.strip():
        raise ValueError("user_identifier must not be empty")

    ref = uuid.uuid4().hex[:12].upper()
    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    log_path = os.environ.get("ZT_RECOVERY_LOG", "recovery_requests.log")
    entry = (
        f"{timestamp}  REF={ref}  USER={user_identifier.strip()}  "
        f"STATUS=PENDING_IN_PERSON\n"
    )
    with open(log_path, "a") as f:
        f.write(entry)

    return ref


def print_recovery_instructions(ref: str) -> None:
    print(
        f"""
╔{'═' * 58}╗
║  IN-PERSON KEY RECOVERY REQUIRED{' ' * 25}║
╠{'═' * 58}╣
║{' ' * 58}║
║  Your reference code:  {ref:<12s}{' ' * 23}║
║{' ' * 58}║
║  To obtain a new key set you MUST:{' ' * 22}║
║    1. Appear in person at the issuing authority.{' ' * 10}║
║    2. Present valid government-issued photo ID.{' ' * 11}║
║    3. Provide this reference code.{' ' * 24}║
║{' ' * 58}║
║  There is NO digital recovery path.{' ' * 21}║
║  Keys will NOT be issued by email, SMS, or remotely.{' ' * 5}║
║{' ' * 58}║
╚{'═' * 58}╝
"""
    )
