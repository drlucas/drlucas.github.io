Thanks to https://github.com/tinkertims/SVI-Ultra-Skelly-Tools/blob/main/comm_test.py for the code
drop this into your script file and then just add to your playlist with an argument for the voice you already setup


fpp@FPP-skelly:~/media/scripts $ cat skelly.py 
from bleak import BleakClient, BleakScanner
import asyncio
import sys

BLE_DEVICE_ADDRESS = "C3:93:D4:E0:63:18"
WRITE_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"

# Get file serial from command-line argument
try:
    FILE_SERIAL = int(sys.argv[1])
    if FILE_SERIAL not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        print(f"Invalid file serial {FILE_SERIAL}. Using default: 1")
        FILE_SERIAL = 1
except (IndexError, ValueError):
    print("No valid file serial provided. Using default: 1")
    FILE_SERIAL = 1

# =====================
#  Helper Utilities
# =====================
def crc8(data: bytes) -> str:
    """Calculate CRC8 using polynomial 0x8C (X^8 + X^5 + X^4 + 1)."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc >> 1) ^ 0x8C) if (crc & 1) else (crc >> 1)
    return f"{crc:02X}"

def build_cmd(tag: str, payload: str = "00") -> bytes:
    """
    Construct a BLE command:
    - tag: 2-char command tag (e.g. 'F3')
    - payload: hex string payload (auto-padded to 16 chars)
    - returns: full command as bytes
    """
    base_str = "AA" + tag + payload
    if len(payload) < 16:
        padding = "0" * (16 - len(payload))
        base_str += padding
    crc = crc8(bytes.fromhex(base_str))
    return bytes.fromhex(base_str + crc)

def pad_hex(hex_str: str, length: int):
    return hex_str.zfill(length)

def to_utf16le_hex(s: str) -> str:
    if not s:
        return ""
    return s.encode("utf-16le").hex()

def int_to_hex(n: int, byte_len: int):
    return pad_hex(hex(n)[2:], byte_len * 2).upper()

# ============
# Query Commands
# ============
def query_device_parameter(): return build_cmd("E0")
def query_live_mode(): return build_cmd("E1")
def query_volume(): return build_cmd("E5")
def query_bt_name(): return build_cmd("E6")
def query_version(): return build_cmd("EE")
def query_file_info(): return build_cmd("D0")
def query_song_order(): return build_cmd("D1")
def query_capacity(): return build_cmd("D2")

# =========
# Media Controls
# =========
def set_volume(vol: int): return build_cmd("FA", int_to_hex(vol, 1))
def play(): return build_cmd("FC", "01")
def pause(): return build_cmd("FC", "00")
def enable_classic_bt(): return build_cmd("FD", "01")
def set_music_mode(mode: int): return build_cmd("FE", int_to_hex(mode, 1))  # 0=device, 1=bt
def set_music_animation(action: int, cluster: int, filename: str):
    name_utf16 = to_utf16le_hex(filename) if filename else ""
    name_len = int_to_hex((len(name_utf16) // 2) + 2, 1) if filename else "00"
    payload = int_to_hex(action, 1) + "00" + int_to_hex(cluster, 4)
    if filename:
        payload += name_len + "5C55" + name_utf16
    else:
        payload += name_len
    return build_cmd("CA", payload)

# ============
# RGB & Light Controls
# ============
def set_mode(channel: int, mode: int, cluster: int, name: str):
    ch = "FF" if channel == -1 else int_to_hex(channel, 1)
    name_utf16 = to_utf16le_hex(name)
    name_len = int_to_hex((len(name_utf16) // 2) + 2, 1) if name else "00"
    payload = ch + int_to_hex(mode,1) + int_to_hex(cluster, 4) + (name_len + "5C55" + name_utf16 if name else name_len)
    return build_cmd("F2", payload)

def set_brightness(channel: int, brightness: int, cluster: int, name: str):
    ch = "FF" if channel == -1 else int_to_hex(channel, 1)
    name_utf16 = to_utf16le_hex(name)
    name_len = int_to_hex((len(name_utf16) // 2) + 2, 1) if name else "00"
    payload = ch + int_to_hex(brightness,1) + int_to_hex(cluster, 4) + (name_len + "5C55" + name_utf16 if name else name_len)
    return build_cmd("F3", payload)

def set_rgb(channel: int, r: int, g: int, b: int, loop: int, cluster: int, name: str):
    ch = "FF" if channel == -1 else int_to_hex(channel, 1)
    name_utf16 = to_utf16le_hex(name)
    name_len = int_to_hex((len(name_utf16) // 2) + 2, 1) if name else "00"
    payload = ch + int_to_hex(r,1) + int_to_hex(g,1) + int_to_hex(b,1) + int_to_hex(loop,1) + int_to_hex(cluster, 4)
    payload += (name_len + "5C55" + name_utf16) if name else name_len
    return build_cmd("F4", payload)

def set_speed(channel: int, speed: int, cluster: int, name: str):
    ch = "FF" if channel == -1 else int_to_hex(channel, 1)
    name_utf16 = to_utf16le_hex(name)
    name_len = int_to_hex((len(name_utf16) // 2) + 2, 1) if name else "00"
    payload = ch + int_to_hex(speed,1) + int_to_hex(cluster, 4) + (name_len + "5C55" + name_utf16 if name else name_len)
    return build_cmd("F6", payload)

def select_rgb_channel(channel: int):
    return build_cmd("F5", "FF" if channel == -1 else int_to_hex(channel, 1))

def set_eye_icon(icon: int, cluster: int, name: str):
    name_utf16 = to_utf16le_hex(name)
    payload = (
        int_to_hex(icon, 1) +
        "000000" +                         # 3-byte padding
        int_to_hex(cluster, 2) +           # 2-byte cluster ID
        "5C55" +                           # UTF-16LE BOM
        name_utf16                         # encoded name
    )
    return build_cmd("F9", payload)

# =============
# File Controls
# =============
def play_or_pause_file(serial: int, action: int):
    return build_cmd("C6", int_to_hex(serial, 2) + int_to_hex(action, 1))

def delete_file(serial: int, cluster: int):
    return build_cmd("C7", int_to_hex(serial, 2) + int_to_hex(cluster, 4))

def format_device():
    return build_cmd("C8", "00")

def set_music_order(total: int, index: int, file_serial: int, filename: str):
    name_utf16 = to_utf16le_hex(filename)
    name_len = int_to_hex((len(name_utf16)//2)+2, 1)
    payload = int_to_hex(total, 1) + int_to_hex(index, 1) + int_to_hex(file_serial, 2) + name_len + "5C55" + name_utf16
    return build_cmd("C9", payload)

# =======================
# Connection & Notification Handling
# =======================
def handle_notification(sender, data):
    hexstr = data.hex().upper()
    print(f"[NOTIFY] From {sender}: {hexstr}")

    def get_utf16le(data_bytes):
        try:
            return data_bytes.decode("utf-16le").strip("\x00")
        except Exception:
            return ""

    def get_ascii(hexstr):
        try:
            return bytes.fromhex(hexstr).decode("ascii").strip()
        except Exception:
            return ""

    if hexstr.startswith("BBE1"):
        action = int(hexstr[4:6], 16)
        lights = []
        light_data = hexstr[6:90]
        for i in range(6):
            chunk = light_data[i * 14: (i + 1) * 14]
            if len(chunk) < 14:
                continue
            chEffect = int(chunk[0:2], 16)
            effectGroup = int(chunk[2:4], 16)
            r = int(chunk[4:6], 16)
            g = int(chunk[6:8], 16)
            b = int(chunk[8:10], 16)
            brightness = int(chunk[10:12], 16)
            channel = int(chunk[12:14], 16)
            light = {
                "channel": channel,
                "brightness": brightness,
                "rgb": (r, g, b),
                "chEffect": chEffect,
                "effectGroup": effectGroup
            }
            lights.append(light)
        eye_icon = int(hexstr[90:92], 16)
        print(f"[PARSED] Action: {action}, Eye Icon: {eye_icon}, Lights: {lights}")
        return

    if hexstr.startswith("BBE5"):
        volume = int(hexstr[4:6], 16)
        print(f"[PARSED] Volume: {volume}")
        return

    if hexstr.startswith("BBE6"):
        length = int(hexstr[4:6], 16)
        name_hex = hexstr[6:6 + length * 2]
        name = get_ascii(name_hex)
        print(f"[PARSED] Classic BT Name: {name}")
        return

    if hexstr.startswith("BBE0"):
        channels = [int(hexstr[i:i+2], 16) for i in range(4, 16, 2)]
        pin_code = get_ascii(hexstr[16:24])
        wifi_password = get_ascii(hexstr[24:40])
        display_mode = int(hexstr[40:42], 16)
        name_len = int(hexstr[56:58], 16)
        name = get_ascii(hexstr[58:58 + name_len * 2])
        print(f"[PARSED] Channels: {channels}, Pin: {pin_code}, WiFi: {wifi_password}, Mode: {display_mode}, Name: {name}")
        return

    if hexstr.startswith("BBC6"):
        serial = int(hexstr[4:8], 16)
        playing = int(hexstr[8:10], 16)
        duration = int(hexstr[10:14], 16)
        print(f"[PARSED] Play/Pause - Serial: {serial}, Playing: {bool(playing)}, Duration: {duration}")
        return

    if hexstr.startswith("BBC7"):
        success = int(hexstr[4:6], 16)
        print(f"[PARSED] Delete File - Success: {success == 0}")
        return

    if hexstr.startswith("BBC8"):
        success = int(hexstr[4:6], 16)
        print(f"[PARSED] Format - Success: {success}")
        return

    if hexstr.startswith("BBD2"):
        capacity = int(hexstr[4:12], 16)
        file_count = int(hexstr[12:14], 16)
        action_mode = int(hexstr[14:16], 16)
        mode_str = "Set Action" if action_mode else "Transfer Mode"
        print(f"[PARSED] Capacity: {capacity}KB, File Count: {file_count}, Mode: {mode_str}")
        return

    if hexstr.startswith("BBD1"):
        count = int(hexstr[4:6], 16)
        data_str = hexstr[6:]
        if len(data_str) < count * 4:
            count = len(data_str) // 4
        orders = [int(data_str[i*4:i*4+4], 16) for i in range(count)]
        print(f"[PARSED] Music Order: {orders}")
        return

    if hexstr.startswith("BBD0"):
        file_index = int(hexstr[4:8], 16)
        cluster = int(hexstr[8:16], 16)
        total_files = int(hexstr[16:20], 16)
        length = int(hexstr[20:24], 16)
        attr = int(hexstr[24:26], 16)
        light_data = hexstr[26:110]
        lights = []
        for i in range(6):
            chunk = light_data[i*14:(i+1)*14]
            if len(chunk) == 14:
                chEffect = int(chunk[0:2], 16)
                effectGroup = int(chunk[2:4], 16)
                r = int(chunk[4:6], 16)
                g = int(chunk[6:8], 16)
                b = int(chunk[8:10], 16)
                brightness = int(chunk[10:12], 16)
                channel = int(chunk[12:14], 16)
                lights.append({
                    "channel": channel,
                    "brightness": brightness,
                    "rgb": (r, g, b),
                    "chEffect": chEffect,
                    "effectGroup": effectGroup
                })
        eye_icon = int(hexstr[110:112], 16)
        db_pos = int(hexstr[112:114], 16)
        name_utf16 = data[59:-1]
        name = get_utf16le(name_utf16)
        print(f"[PARSED] File Info:\n  Index: {file_index}, Cluster: {cluster}, Total: {total_files}\n  Attr: {attr}, Eye: {eye_icon}, DB Pos: {db_pos}, Name: {name}\n  Lights: {lights}")
        return

    print("[WARN] Unhandled notification.")

async def send_command(client, cmd_bytes):
    print(f"[SEND] {cmd_bytes.hex().upper()}")
    await client.write_gatt_char(WRITE_UUID, cmd_bytes)

async def run():
    print("Scanning for device...")

    device = None

    if BLE_DEVICE_ADDRESS and BLE_DEVICE_ADDRESS != "None":
        device = await BleakScanner.find_device_by_address(BLE_DEVICE_ADDRESS)
    else:
        print("No MAC address provided. Searching for device with name containing 'Animated Skelly'...")
        devices = await BleakScanner.discover(timeout=10.0)
        for d in devices:
            if d.name and "animated skelly" in d.name.lower():
                device = d
                print(f"[FOUND] '{d.name}' @ {d.address}")
                print(f"You can update BLE_DEVICE_ADDRESS = \"{d.address}\" in your script.")
                break

    if not device:
        print("Device not found.")
        return

    async with BleakClient(device) as client:
        print("Connected to", device.address)
        await client.start_notify(NOTIFY_UUID, handle_notification)

        # Query volume
        await send_command(client, query_volume())
        # Query BT name
        await send_command(client, query_bt_name())
        # Play specified file
        await send_command(client, play_or_pause_file(FILE_SERIAL, 1))
        # Wait 30 seconds
        await asyncio.sleep(30)

        print("Disconnecting...")
        await client.stop_notify(NOTIFY_UUID)
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run())
