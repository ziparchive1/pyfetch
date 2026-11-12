#!/usr/bin/env python3
import os
import platform
import re
import shutil
import socket
import subprocess

R = "\033[0m"
W = "\033[1;37m"

LOGOS = {
    "arch": ("\033[1;36m", "\033[1;34m", [
        "       /\\        ",
        "      /  \\       ",
        "     /\\   \\      ",
        "    /      \\     ",
        "   /   ,,   \\    ",
        "  /   |  |  -\\   ",
        " /_-''    ''-_\\  ",
    ]),
    "debian": ("\033[1;31m", "\033[0;31m", [
        "    _,met$$$$$gg.    ",
        " ,g$$$$$$$$$$$$$$$P. ",
        ",g$$P\"     \"\"\"Y$$.\". ",
        "$$P'              `$$",
        "$$                 $$",
        "`$$.             ,$$'",
        " `$$P'         `$$P' ",
        "    `\"\"\"\"\"\"\"\"\"\"'     ",
    ]),
    "ubuntu": ("\033[1;33m", "\033[1;31m", [
        "         _       ",
        "     ---(_)      ",
        " _/  ---  \\      ",
        "(_) |   |        ",
        "  \\  --- _/      ",
        "     ---(_)      ",
    ]),
    "fedora": ("\033[1;34m", "\033[1;36m", [
        "      _____      ",
        "     /   __)\\    ",
        "     |  /  \\ \\   ",
        "  ___|  |__/ /   ",
        " / (_    _)_/    ",
        "/ /  |  |        ",
        "\\ \\__/  |        ",
        " \\(_____/        ",
    ]),
    "gentoo": ("\033[1;35m", "\033[0;35m", [
        "  _-----_        ",
        " (       \\       ",
        "(    0    \\      ",
        " \\         )     ",
        " /      _--      ",
        "(______-         ",
    ]),
    "void": ("\033[1;32m", "\033[0;32m", [
        "    _______      ",
        " _ \\______ -     ",
        "| \\  ___  \\ |    ",
        "| | /   \\ | |    ",
        "| | \\___/ | |    ",
        "| \\______ \\_|    ",
        " -_______\\       ",
    ]),
    "alpine": ("\033[1;34m", "\033[1;37m", [
        "   /\\ /\\         ",
        "  // \\  \\        ",
        " //   \\  \\       ",
        "//     \\  \\      ",
        "        \\  \\     ",
    ]),
    "mint": ("\033[1;32m", "\033[1;37m", [
        "  _____________  ",
        " |_            \\ ",
        "   | | _____ | | ",
        "   | | | | | | | ",
        "   | | | | | | | ",
        "   | \\_____/ | | ",
        "   \\_________/   ",
    ]),
    "linux": ("\033[1;33m", "\033[1;37m", [
        "     .--.        ",
        "    |o_o |       ",
        "    |:_/ |       ",
        "   //   \\ \\      ",
        "  (|     | )     ",
        " /'\\_   _/`\\     ",
        " \\___)=(___/     ",
    ])
}

def get_distro_info():
    distro_id = "linux"
    pretty_name = f"{platform.system()} {platform.release()}"
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_id = line.split("=", 1)[1].strip().strip('"').lower()
                elif line.startswith("PRETTY_NAME="):
                    pretty_name = line.split("=", 1)[1].strip().strip('"')
    return distro_id, pretty_name

def get_uptime():
    try:
        with open("/proc/uptime") as f:
            s = float(f.readline().split()[0])
        d, rem = divmod(s, 86400)
        h, rem = divmod(rem, 3600)
        m, _ = divmod(rem, 60)
        parts = []
        if d: parts.append(f"{int(d)}d")
        if h: parts.append(f"{int(h)}h")
        parts.append(f"{int(m)}m")
        return " ".join(parts)
    except:
        return "Unknown"

def get_cpu():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    cpu = line.split(":", 1)[1].strip()
                    for j in ["(R)", "(TM)", "CPU", "@", "Processor"]:
                        cpu = cpu.replace(j, "")
                    return " ".join(cpu.split())
    except:
        pass
    return platform.processor() or "Unknown"

def get_ram():
    try:
        m = {}
        with open("/proc/meminfo") as f:
            for line in f:
                p = line.split()
                m[p[0].rstrip(":")] = int(p[1])
        total = m["MemTotal"] / 1024
        avail = m.get("MemAvailable", m.get("MemFree", 0)) / 1024
        used = total - avail
        return f"{used:.0f} MiB / {total:.0f} MiB ({used / total * 100:.0f}%)"
    except:
        return "Unknown"

def get_gpu():
    if shutil.which("lspci"):
        try:
            out = subprocess.check_output(["lspci"], text=True)
            for line in out.splitlines():
                if any(k in line for k in ["VGA compatible controller", "3D controller", "Display controller"]):
                    gpu = line.split(":", 2)[-1].strip()
                    if "(rev" in gpu:
                        gpu = gpu.split("(rev")[0].strip()
                    return gpu
        except:
            pass
    return "Unknown"

def get_board():
    for path in ["/sys/class/dmi/id/product_name", "/sys/firmware/devicetree/base/model"]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    val = f.read().strip()
                    if val: return val
            except: pass
    return "Unknown"

def get_packages():
    managers = {
        "pacman": ["pacman", "-Qq"],
        "dpkg": ["dpkg-query", "-f", "${binary:Package}\n", "-W"],
        "rpm": ["rpm", "-qa"],
        "emerge": ["qlist", "-I"] if shutil.which("qlist") else ["equery", "list"],
        "xbps": ["xbps-query", "-l"],
        "apk": ["apk", "info"],
        "flatpak": ["flatpak", "list"],
        "snap": ["snap", "list"]
    }
    res = []
    for name, cmd in managers.items():
        if shutil.which(cmd[0]):
            try:
                out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
                count = len([line for line in out.splitlines() if line.strip()])
                if count > 0:
                    res.append(f"{count} ({name})")
            except: pass
    return ", ".join(res) if res else "Unknown"

def get_wm_de():
    de = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION")
    if de: return de
    candidates = ["i3", "xmonad", "sway", "bspwm", "openbox", "awesome", "dwm", "hyprland", "gnome-shell", "kwin", "xfce4-session", "mate-session", "lxqt-session"]
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open(f"/proc/{pid}/comm") as f:
                    comm = f.read().strip()
                    if comm in candidates:
                        return comm
            except: continue
    return "TTY / None"

def get_disk():
    try:
        t, u, _ = shutil.disk_usage("/")
        gb = 1024 ** 3
        return f"{u / gb:.1f} GiB / {t / gb:.1f} GiB ({u / t * 100:.0f}%)"
    except:
        return "Unknown"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def strip_ansi(text):
    return re.sub(r'\033\[[0-9;]*m', '', text)

def main():
    distro_id, pretty_os = get_distro_info()
    c1, c2, raw_logo = LOGOS.get(distro_id, LOGOS["linux"])
    
    logo_width = max(len(line) for line in raw_logo)
    logo = [f"{c1}{line.ljust(logo_width)}{R}" for line in raw_logo]
    logo_pad = " " * logo_width

    user = os.environ.get("USER", "user")
    host = socket.gethostname()
    shell = os.path.basename(os.environ.get("SHELL", "sh"))
    term = os.environ.get("TERM", "unknown")

    info = [
        f"{W}{user}{R}@{W}{host}{R}",
        f"{c2}{'-' * (len(user) + len(host) + 1)}{R}",
        f"{c1}OS:{R}        {pretty_os}",
        f"{c1}Host:{R}      {get_board()}",
        f"{c1}Kernel:{R}    {platform.release()}",
        f"{c1}Uptime:{R}    {get_uptime()}",
        f"{c1}Packages:{R}  {get_packages()}",
        f"{c1}Shell:{R}     {shell}",
        f"{c1}DE/WM:{R}     {get_wm_de()}",
        f"{c1}Terminal:{R}  {term}",
        f"{c1}IP (Local):{R}{get_local_ip()}",
        f"{c1}CPU:{R}       {get_cpu()}",
        f"{c1}GPU:{R}       {get_gpu()}",
        f"{c1}Memory:{R}    {get_ram()}",
        f"{c1}Disk (/):{R}  {get_disk()}",
        "",
        " ".join(f"\033[4{i}m   \033[0m" for i in range(8))
    ]

    max_lines = max(len(logo), len(info))

    print()
    for i in range(max_lines):
        l_part = logo[i] if i < len(logo) else logo_pad
        i_part = info[i] if i < len(info) else ""
        print(f"{l_part}   {i_part}")
    print()

if __name__ == "__main__":
    main()
