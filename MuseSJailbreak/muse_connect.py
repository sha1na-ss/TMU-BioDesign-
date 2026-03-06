import asyncio
import sys

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

# ── Known MUSE identifiers ────────────────────────────────────────────────────
# The Muse S (Athena) advertises itself with one of these name prefixes.
MUSE_NAME_PREFIXES = ("Muse", "Muse S", "Muse-S", "Muse S (Athena)", "Muse 2")

# Primary GATT service UUID broadcast by all Muse headbands.
MUSE_PRIMARY_SERVICE_UUID = "0000fe8d-0000-1000-8000-00805f9b34fb"

# ── Well-known Muse characteristic UUIDs ─────────────────────────────────────
MUSE_UUIDS = {
    # Control channel – send commands (start/stop streaming, keep-alive …)
    "control":           "273e0001-4c4d-454d-96be-f03bac821358",
    # EEG data channels (4 electrodes × 2 channels each on the Muse S)
    "eeg_tp9":           "273e0003-4c4d-454d-96be-f03bac821358",
    "eeg_af7":           "273e0004-4c4d-454d-96be-f03bac821358",
    "eeg_af8":           "273e0005-4c4d-454d-96be-f03bac821358",
    "eeg_tp10":          "273e0006-4c4d-454d-96be-f03bac821358",
    "eeg_aux":           "273e0007-4c4d-454d-96be-f03bac821358",
    # Accelerometer / gyroscope
    "accelerometer":     "273e000a-4c4d-454d-96be-f03bac821358",
    "gyroscope":         "273e0009-4c4d-454d-96be-f03bac821358",
    # Telemetry (battery level, ADC voltage, temperature)
    "telemetry":         "273e000b-4c4d-454d-96be-f03bac821358",
    # Headband status / connection quality
    "hsi_precision":     "273e000c-4c4d-454d-96be-f03bac821358",
    # PPG (photoplethysmography / heart-rate) – Muse S exclusive
    "ppg_ambient":       "273e000f-4c4d-454d-96be-f03bac821358",
    "ppg_infrared":      "273e0010-4c4d-454d-96be-f03bac821358",
    "ppg_red":           "273e0011-4c4d-454d-96be-f03bac821358",
}

# ASCII command that tells the Muse to start streaming data.
CMD_START = b"\x02\x64\x0a"   # '{d\n' in Muse protocol

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_muse_device(device: BLEDevice) -> bool:
    """Return True if the BLE advertisement looks like a Muse headband."""
    name = device.name or ""
    return any(name.startswith(prefix) for prefix in MUSE_NAME_PREFIXES)


async def scan_for_muse(timeout: float = 10.0) -> BLEDevice | None:
    """Scan for BLE devices and return the first Muse found, or None."""
    print(f"[scan]  Scanning for Muse S headband (timeout={timeout}s) …")
    devices = await BleakScanner.discover(timeout=timeout)
    for device in devices:
        if is_muse_device(device):
            print(f"[scan]  Found: {device.name!r}  |  address: {device.address}")
            return device
    return None


def print_uuid_table(client: BleakClient) -> None:
    """Pretty-print every service and characteristic UUID on the device."""
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│                    GATT Service / UUID Map                     │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for service in client.services:
        print(f"│  SERVICE  {service.uuid}")
        print(f"│           {service.description}")
        for char in service.characteristics:
            props = ", ".join(char.properties)
            print(f"│    CHAR   {char.uuid}")
            print(f"│           {char.description}  [{props}]")
            for desc in char.descriptors:
                print(f"│      DESC {desc.uuid}")
    print("└─────────────────────────────────────────────────────────────────┘\n")


def print_named_uuids() -> None:
    """Print the named Muse-specific UUIDs used in this script."""
    print("\n── Named Muse UUIDs used by this script ────────────────────────────")
    for name, uuid in MUSE_UUIDS.items():
        print(f"   {name:<20} {uuid}")
    print()


# ── Core connection logic ─────────────────────────────────────────────────────

async def run() -> None:
    # 1. Scan
    device = await scan_for_muse()
    if device is None:
        print("\n[error] No Muse S headband found nearby.")
        print("        Make sure the headband is powered on and in range, then retry.")
        sys.exit(1)

    # 2. Connect
    print(f"\n[connect] Connecting to {device.name!r} ({device.address}) …")
    async with BleakClient(device.address) as client:

        if not client.is_connected:
            print("[error] BleakClient reported not connected after context entry.")
            sys.exit(1)

        # ── ✅ Connection confirmed ────────────────────────────────────────
        print("\n" + "═" * 60)
        print(f"  ✅  CONNECTED to {device.name!r}")
        print(f"      Device address : {device.address}")
        print(f"      MTU             : {client.mtu_size} bytes")
        print("═" * 60)

        # 3. Enumerate and display all UUIDs
        print_uuid_table(client)
        print_named_uuids()

        # 4. Start the data stream via the control characteristic
        try:
            ctrl_uuid = MUSE_UUIDS["control"]
            await client.write_gatt_char(ctrl_uuid, CMD_START, response=True)
            print("[stream] Data streaming started (CMD_START sent).")
        except Exception as exc:
            print(f"[warn]  Could not send start command: {exc}")

        # 5. Keep the connection alive until the user interrupts
        print("\n[keep-alive]  Connection is being maintained.")
        print("              Press Ctrl-C to disconnect and exit.\n")
        try:
            while client.is_connected:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            pass

        print("\n[disconnect] Closing connection …")

    print("[disconnect] Disconnected cleanly. Goodbye.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n[interrupt] Caught Ctrl-C. Exiting.")
