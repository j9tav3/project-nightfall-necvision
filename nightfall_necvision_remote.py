#!/usr/bin/env python3
"""
NECVISION - CTF HTB-2026 Project Nightfall IR Remote Control
Interactive remote control for NECVISION display wall.
Protocol: NEC 4-byte [0x42, 0xBD, CMD, ~CMD]
"""

import socket
import json
import urllib.request
import sys
import os

# ===== CONFIG =====
IP = '154.57.164.63'
WEB_PORT = 32212
IR_PORT = 31939
ADDR = 0x42
NADDR = (~ADDR) & 0xFF  # 0xBD

WEB = f'http://{IP}:{WEB_PORT}'

# ===== COMMAND MAP =====
COMMANDS = {
    # Digits
    '0': 0x00, '1': 0x01, '2': 0x02, '3': 0x03, '4': 0x04,
    '5': 0x05, '6': 0x06, '7': 0x07, '8': 0x08, '9': 0x09,
    # Functions
    'VOL+':  0x14, 'VOLUP':   0x14, 'V+': 0x14,
    'VOL-':  0x15, 'VOLDOWN': 0x15, 'V-': 0x15,
    'CH+':   0x16, 'CHUP':    0x16, 'C+': 0x16,
    'CH-':   0x17, 'CHDOWN':  0x17, 'C-': 0x17,
    'INPUT': 0x1B,
    'POWER': 0x45, 'PWR': 0x45, 'ONOFF': 0x45,
    'MUTE':  0x46,
}

# ===== FUNCTIONS =====

def send_ir(cmd):
    """Send NEC 4-byte command to IR port"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((IP, IR_PORT))
        s.send(bytes([ADDR, NADDR, cmd, (~cmd) & 0xFF]))
        s.close()
        return True
    except Exception as e:
        print(f'  [!] Send error: {e}')
        return False

def get_state():
    """Get current TV state"""
    try:
        resp = urllib.request.urlopen(f'{WEB}/api/state', timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        print(f'  [!] API error: {e}')
        return None

def reset_tv():
    """Reset TV to default state"""
    try:
        req = urllib.request.Request(f'{WEB}/api/reset', method='POST')
        urllib.request.urlopen(req, timeout=5)
        print('  [OK] TV reset to default')
    except Exception as e:
        print(f'  [!] Reset error: {e}')

def get_stream_url():
    """Get current stream GIF URL"""
    try:
        resp = urllib.request.urlopen(f'{WEB}/api/stream', timeout=5)
        return resp.geturl()
    except:
        return None

def show_status():
    """Display current TV state"""
    s = get_state()
    if not s: return
    stream = get_stream_url()
    print(f"""
  {'='*50}
  Power:  {'ON' if s['power'] else 'OFF':>8}
  Input:  {s['input_name']:>8} (idx {s['input_index']})
  Channel:{s['channel']:>8}
  Volume: {s['volume']:>8}
  Muted:  {str(s['muted']):>8}
  Digits: {repr(s['digit_buffer']):>8}
  {'='*50}
  Stream: {stream}
""")

def show_help():
    print("""
  ===== NECVISION REMOTE CONTROL =====
  
  DIGITS:     0 1 2 3 4 5 6 7 8 9
  POWER:      power / pwr / onoff
  VOLUME:     vol+ / vol- / v+ / v-
  CHANNEL:    ch+ / ch- / c+ / c-
  INPUT:      input
  MUTE:       mute
  
  SPECIALS:
  status      Show current TV state + stream URL
  reset       Reset TV to default
  stream      Show stream GIF URL
  combo X X   Send multiple commands (e.g. "combo 1 2 3")
  help        Show this menu
  exit/quit   Exit
  ====================================
""")

def execute(cmd_str):
    """Parse and execute a command string"""
    cmd_str = cmd_str.strip().upper()
    
    if not cmd_str:
        return
    
    # Special commands
    if cmd_str in ('EXIT', 'QUIT'):
        print('  Bye!')
        sys.exit(0)
    elif cmd_str == 'HELP':
        show_help()
        return
    elif cmd_str == 'STATUS':
        show_status()
        return
    elif cmd_str == 'RESET':
        reset_tv()
        return
    elif cmd_str == 'STREAM':
        url = get_stream_url()
        print(f'  Stream URL: {url}')
        return
    elif cmd_str.startswith('COMBO'):
        parts = cmd_str.split()
        for p in parts[1:]:
            execute(p)
        return
    
    # Look up command
    cmd = COMMANDS.get(cmd_str)
    if cmd is None:
        print(f'  [?] Unknown command: {cmd_str}')
        return
    
    # Send it
    if send_ir(cmd):
        print(f'  [>>] {cmd_str}')
        # Show brief status
        s = get_state()
        if s:
            power = 'ON' if s['power'] else 'OFF'
            print(f'  [TV] Power:{power} Input:{s["input_name"]} Ch:{s["channel"]} Vol:{s["volume"]} Mute:{s["muted"]}')

# ===== MAIN =====

if __name__ == '__main__':
    print("""
  ╔══════════════════════════════════╗
  ║     NECVISION REMOTE CONTROL     ║
  ║   Task Force Nightfall - j9tav3  ║
  ╠══════════════════════════════════╣
  ║  Address: 0x42                   ║
  ║  Type 'help' for commands        ║
  ╚══════════════════════════════════╝
""")
    
    show_status()
    
    while True:
        try:
            # Check for piped input or interactive
            if os.isatty(sys.stdin.fileno()):
                line = input('\n  CMD> ').strip()
                if line:
                    execute(line)
            else:
                # Read from pipe/redirect
                for line in sys.stdin:
                    execute(line.strip())
                break
        except KeyboardInterrupt:
            print('\n  Interrupted.')
            break
        except EOFError:
            break
