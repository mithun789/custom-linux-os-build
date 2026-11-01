#!/usr/bin/env python3
"""Boot and install tests for Orchard OS images in QEMU.

Runs headless on any Linux server (KVM is used when /dev/kvm exists, TCG
otherwise). Drives the guest over the serial console and takes screenshots
through the QEMU monitor.

Tests:
  iso-menu    ISO boots through GRUB on BIOS and UEFI (menu shows on serial)
  live        live session reaches the desktop (xfdesktop, plank, panel run)
  install     orchard-install writes the system to a virtual disk
  installed   installed disk boots on BIOS and UEFI to the login screen
  gui-install graphical installer (Calamares): erase disk, create user,
              install, then boot the installed disk and log in

Usage:
  qemu-test.py ISO [--tests iso-menu,live,install,installed] [--out DIR]
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pexpect

KVM = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.W_OK)
SLOW = 1 if KVM else 4  # timeout multiplier for software emulation
OVMF_CODE = next((p for p in ["/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_CODE.fd"]
                  if os.path.exists(p)), None)
OVMF_VARS = next((p for p in ["/usr/share/OVMF/OVMF_VARS_4M.fd", "/usr/share/OVMF/OVMF_VARS.fd"]
                  if os.path.exists(p)), None)

RESULTS = []


def log(msg):
    print(f"\n\033[1;34m[test]\033[0m {msg}", flush=True)


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    mark = "\033[1;32mPASS\033[0m" if ok else "\033[1;31mFAIL\033[0m"
    print(f"{mark} {name} {detail}", flush=True)


class VM:
    def __init__(self, workdir, name, disk=None, iso=None, uefi=False, kernel=None,
                 initrd=None, append=None, mem=4096, logfile=None):
        self.workdir = Path(workdir)
        self.name = name
        self.mon_path = str(self.workdir / f"{name}.mon")
        args = ["qemu-system-x86_64", "-m", str(mem), "-smp", "4",
                "-display", "none", "-vga", "std",
                "-serial", "stdio", "-monitor", f"unix:{self.mon_path},server,nowait",
                "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
                "-no-reboot"]
        if KVM:
            args += ["-enable-kvm", "-cpu", "host"]
        else:
            args += ["-accel", "tcg,thread=multi", "-cpu", "max"]
        if uefi:
            vars_copy = self.workdir / f"{name}-vars.fd"
            shutil.copy(OVMF_VARS, vars_copy)
            args += ["-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
                     "-drive", f"if=pflash,format=raw,file={vars_copy}"]
        if disk:
            args += ["-drive", f"file={disk},if=virtio,format=qcow2"]
        if iso:
            args += ["-drive", f"file={iso},media=cdrom,readonly=on"]
            if not kernel:
                args += ["-boot", "d"]
        if kernel:
            args += ["-kernel", kernel, "-initrd", initrd, "-append", append]
        self.args = args
        self.child = pexpect.spawn(args[0], args[1:], encoding="utf-8", codec_errors="replace",
                                   timeout=60, maxread=65536)
        self.child.logfile_read = logfile or sys.stdout

    def expect(self, pattern, timeout):
        return self.child.expect(pattern, timeout=timeout * SLOW)

    def send(self, line):
        self.child.sendline(line)

    def monitor(self, cmd):
        for _ in range(50):
            try:
                s = socket.socket(socket.AF_UNIX)
                s.connect(self.mon_path)
                break
            except OSError:
                time.sleep(0.2)
        s.recv(4096)
        s.sendall((cmd + "\n").encode())
        time.sleep(1)
        out = s.recv(65536).decode(errors="replace")
        s.close()
        return out

    def screenshot(self, path):
        ppm = str(Path(path).with_suffix(".ppm"))
        self.monitor(f"screendump {ppm}")
        for _ in range(20):
            if os.path.exists(ppm) and os.path.getsize(ppm) > 0:
                break
            time.sleep(0.5)
        time.sleep(1)
        subprocess.run(["convert", ppm, str(path)], check=False)
        os.unlink(ppm)
        log(f"screenshot: {path}")

    def run(self, cmd, timeout=120, prompt=r"ORCHARD_OK_(\d+)"):
        """Run a shell command on the serial console, return its exit code."""
        self.send(f"{cmd}; echo ORCHARD_OK_$?")
        self.expect(prompt, timeout)
        return int(self.child.match.group(1))

    def kill(self):
        try:
            self.monitor("quit")
        except Exception:
            pass
        self.child.close(force=True)


def login(vm, user, password, timeout=600):
    vm.expect(r"login:", timeout)
    time.sleep(2)
    vm.send(user)
    i = vm.child.expect([r"[Pp]assword:", r"\$ $", r"\$\s"], timeout=60 * SLOW)
    if i == 0:
        vm.send(password)
        vm.expect(r"\$ ", 120)
    vm.send("export PS1='$ ' TERM=dumb; stty cols 200")
    vm.expect(r"\$ ", 30)


def extract_boot_files(iso, workdir):
    k = Path(workdir) / "vmlinuz"
    i = Path(workdir) / "initrd"
    for src, dst in (("/casper/vmlinuz", k), ("/casper/initrd", i)):
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", iso, "-extract", src, str(dst)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(k), str(i)


def test_iso_menu(iso, work, out):
    for fw in ("bios", "uefi"):
        if fw == "uefi" and not OVMF_CODE:
            record("iso-menu-uefi", False, "OVMF not installed")
            continue
        vm = VM(work, f"isomenu-{fw}", iso=iso, uefi=(fw == "uefi"))
        try:
            vm.expect(r"Try or Install Orchard OS", 180)
            time.sleep(3)
            vm.screenshot(out / f"iso-grub-{fw}.png")
            record(f"iso-menu-{fw}", True)
        except pexpect.TIMEOUT:
            record(f"iso-menu-{fw}", False, "GRUB menu not seen on serial")
        finally:
            vm.kill()


def test_live_and_install(iso, work, out, do_install):
    disk = work / "disk.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "20G"], check=True,
                   stdout=subprocess.DEVNULL)
    kernel, initrd = extract_boot_files(iso, work)
    append = "boot=casper quiet splash console=tty0 console=ttyS0,115200n8"
    vm = VM(work, "live", disk=str(disk), iso=iso, kernel=kernel, initrd=initrd, append=append)
    try:
        login(vm, "orchard", "", timeout=900)
        record("live-boot", True, "serial login as live user")

        ok = False
        deadline = time.time() + 600 * SLOW
        while time.time() < deadline:
            if vm.run("pgrep -x xfdesktop >/dev/null && pgrep -x plank >/dev/null && pgrep -x xfce4-panel >/dev/null") == 0:
                ok = True
                break
            time.sleep(10)
        time.sleep(30 * SLOW)  # let the welcome window and wallpaper settle
        vm.screenshot(out / "live-desktop.png")
        record("live-desktop", ok, "xfdesktop + xfce4-panel + plank running")

        checks = {
            "live-os-release": "grep -q 'Orchard OS' /etc/os-release",
            "live-theme": "test -d /usr/share/themes/WhiteSur-Light -a -d /usr/share/icons/WhiteSur",
            "live-no-snap": "! dpkg -l snapd 2>/dev/null | grep -q '^ii'",
            "live-tools": "command -v orchard-install orchard-ai orchard-appearance orchard-welcome >/dev/null",
            "live-network": "nmcli -t -f STATE general | grep -q connected",
            "live-ai-tools": "command -v orchard-agent orchard-voice orchard-guard orchard-restore orchard-drivers >/dev/null",
            "live-agent-cli": "orchard-agent providers | grep -q huggingface",
            "live-guard-check": "sudo orchard-guard check && test -f /var/log/orchard/guard-alerts.log",
            "live-zram": "swapon --show | grep -q zram",
            "live-firewall": "sudo ufw status | grep -q 'Status: active'",
            "live-earlyoom": "systemctl is-active earlyoom",
            "live-compositor": "pgrep -x picom || DISPLAY=:0 XAUTHORITY=/home/orchard/.Xauthority xfconf-query -c xfwm4 -p /general/use_compositing | grep -q true",
            "live-kernel-hwe": "uname -r | grep -qE '^(7|[89])\\.'",
            "live-vscode": "test -x /usr/bin/code || { echo 'VS Code missing (vendor repo unreachable at build time?)'; false; }",
            "live-global-menu": "ls /usr/lib/x86_64-linux-gnu/gtk-3.0/modules/ | grep -q appmenu",
            "live-launchpad": "command -v orchard-launchpad && test -f /usr/share/icons/hicolor/scalable/apps/orchard-launchpad.svg",
            "live-glass-css": "test -f /usr/share/orchard/gtk/glass-light.css -a -f /usr/share/orchard/gtk/frost-light.css",
            "live-ollama-deps": "command -v zstd",
            "live-installer-layout": "grep -q partitionLayout /etc/calamares/modules/partition.conf",
            "live-clamav": "clamscan --version",
            "live-vbox-guest": "test -e /usr/bin/VBoxClient",
        }
        for name, cmd in checks.items():
            record(name, vm.run(cmd) == 0)
        # Diagnostics for the desktop compositor.
        vm.run("cat ~/.config/orchard/picom.log; pgrep -a -f orchard-compositor; "
               "DISPLAY=:0 XAUTHORITY=/home/orchard/.Xauthority xfconf-query -c xfwm4 -p /general/use_compositing; "
               "glxinfo -B 2>&1 | head -5")

        # Dark appearance switch inside the running session.
        env = "DISPLAY=:0 XAUTHORITY=/home/orchard/.Xauthority DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus"
        rc = vm.run(f"{env} orchard-appearance dark")
        time.sleep(8 * SLOW)
        vm.screenshot(out / "live-desktop-dark.png")
        record("live-appearance-dark", rc == 0)
        vm.run(f"{env} orchard-appearance light")

        # Graphical installer starts.
        vm.run(f"(sudo -E env {env} calamares >/tmp/calamares.log 2>&1 &)")
        started = False
        for _ in range(30):
            time.sleep(5 * SLOW)
            if vm.run(f"{env} xdotool search --name 'Installer' >/dev/null 2>&1 && pgrep -x calamares >/dev/null") == 0:
                started = True
                break
        time.sleep(10 * SLOW)
        vm.screenshot(out / "live-installer.png")
        record("live-calamares", started, "Calamares window open")
        vm.run("sudo pkill -x calamares; true")

        if do_install:
            vm.send("sudo orchard-install --disk /dev/vda --user tester --password orchard123 "
                    "--hostname orchard-test --timezone Europe/London --serial --yes "
                    "; echo INSTALL_RESULT_$?")
            vm.child.expect(r"INSTALL_RESULT_(\d+)", timeout=3600 * SLOW)
            rc = int(vm.child.match.group(1))
            record("install", rc == 0, f"orchard-install to /dev/vda (exit {rc})")
        vm.send("sudo poweroff")
        time.sleep(5)
    except pexpect.TIMEOUT as exc:
        vm.screenshot(out / "live-timeout.png")
        record("live", False, f"timeout: {str(exc).splitlines()[0]}")
    finally:
        vm.kill()
    return disk


def test_installed(disk, work, out):
    for fw in ("bios", "uefi"):
        if fw == "uefi" and not OVMF_CODE:
            record("installed-uefi", False, "OVMF not installed")
            continue
        vm = VM(work, f"installed-{fw}", disk=str(disk), uefi=(fw == "uefi"))
        try:
            login(vm, "tester", "orchard123", timeout=900)
            record(f"installed-boot-{fw}", True)
            checks = {
                f"installed-{fw}-hostname": "test \"$(hostname)\" = orchard-test",
                f"installed-{fw}-sudo": "echo orchard123 | sudo -S -v",
                f"installed-{fw}-no-casper": "! dpkg -l casper 2>/dev/null | grep -q '^ii'",
                f"installed-{fw}-lightdm": "systemctl is-active lightdm",
                f"installed-{fw}-timezone": "test \"$(cat /etc/timezone)\" = Europe/London",
                f"installed-{fw}-swap": "swapon --show | grep -q swapfile",
                f"installed-{fw}-network": "nmcli -t -f STATE general | grep -q connected",
                f"installed-{fw}-guard-timer": "systemctl is-active orchard-guard.timer",
                f"installed-{fw}-firewall": "echo orchard123 | sudo -S ufw status | grep -q 'Status: active'",
                f"installed-{fw}-restore": "test -x /usr/bin/timeshift -a -x /usr/bin/orchard-restore",
                f"installed-{fw}-kernel-hwe": "uname -r | grep -qE '^(7|[89])\\.'",
            }
            for name, cmd in checks.items():
                record(name, vm.run(cmd, timeout=180) == 0)
            vm.run("systemctl --failed --no-legend | tee /dev/stderr | wc -l")
            time.sleep(20 * SLOW)
            vm.screenshot(out / f"installed-login-{fw}.png")
            vm.send("echo orchard123 | sudo -S poweroff")
            time.sleep(5)
        except pexpect.TIMEOUT as exc:
            vm.screenshot(out / f"installed-{fw}-timeout.png")
            record(f"installed-boot-{fw}", False, f"timeout: {str(exc).splitlines()[0]}")
        finally:
            vm.kill()



GUI_USER, GUI_PASS = "tester", "Orchard-2026!x"


def test_gui_install(iso, work, out):
    """Drive Calamares like a person would, then boot what it installed."""
    disk = work / "gui-disk.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "25G"], check=True,
                   stdout=subprocess.DEVNULL)
    kernel, initrd = extract_boot_files(iso, work)
    append = "boot=casper quiet splash console=tty0 console=ttyS0,115200n8"
    vm = VM(work, "gui", disk=str(disk), iso=iso, kernel=kernel, initrd=initrd, append=append, mem=6144)
    X = "DISPLAY=:0 XAUTHORITY=/home/orchard/.Xauthority"
    LOG = "/home/orchard/.cache/calamares/session.log"
    ok = False
    try:
        login(vm, "orchard", "", timeout=900)
        for _ in range(60):
            if vm.run("pgrep -x xfce4-panel >/dev/null && pgrep -x plank >/dev/null") == 0:
                break
            time.sleep(10)
        vm.run("pkill -f orchard-welcome; true")
        vm.run(f"(sudo -E env {X} calamares -D 6 >/tmp/cala.out 2>&1 &)")

        def wait_log(pattern, timeout):
            end = time.time() + timeout * SLOW
            while time.time() < end:
                if vm.run(f"grep -qE {pattern!r} {LOG}", timeout=60) == 0:
                    return True
                time.sleep(10)
            return False

        def win_origin():
            vm.send(f"{X} xdotool search --name 'Installer' getwindowgeometry | sed -n 's/.*Position: \\([0-9]*\\),\\([0-9]*\\).*/GEO \\1 \\2/p'")
            vm.child.expect(r"GEO (\d+) (\d+)", timeout=60)
            return int(vm.child.match.group(1)), int(vm.child.match.group(2))

        def click(rx, ry):
            ox, oy = win_origin()
            vm.run(f"{X} xdotool mousemove {ox + rx} {oy + ry} click 1")

        def key(k):
            vm.run(f"{X} xdotool key --delay 200 {k}")

        assert wait_log("All requirements have been checked", 600), "welcome page never became ready"
        key("alt+n"); time.sleep(15 * SLOW)            # -> Location
        key("alt+n"); time.sleep(15 * SLOW)            # -> Keyboard
        key("alt+n"); time.sleep(25 * SLOW)            # -> Partitions
        click(209, 207); time.sleep(3 * SLOW)          # Manual, then back to Erase so the plan is computed
        click(209, 98); time.sleep(15 * SLOW)
        vm.screenshot(out / "gui-partitions.png")
        assert wait_log("CreatePartitionJob|Create new .*partition", 120), "erase-disk plan has no partitions"
        key("alt+n"); time.sleep(15 * SLOW)            # -> Users
        click(98, 79)
        vm.run(f"{X} xdotool type --delay 80 'Orchard Tester'")
        click(98, 143)
        vm.run(f"{X} xdotool key ctrl+a BackSpace type --delay 80 {GUI_USER}")
        click(98, 271)
        vm.run(f"{X} xdotool type --delay 80 '{GUI_PASS}'")
        click(305, 271)
        vm.run(f"{X} xdotool type --delay 80 '{GUI_PASS}'")
        time.sleep(5)
        vm.screenshot(out / "gui-users.png")
        key("alt+n"); time.sleep(15 * SLOW)            # -> Summary
        vm.screenshot(out / "gui-summary.png")
        key("alt+i"); time.sleep(8 * SLOW)             # Install
        key("alt+i")                                   # "Install now" confirmation
        done = False
        end = time.time() + 7200 * SLOW
        while time.time() < end:
            if vm.run(f"grep -qiE 'raised an exception|Installation failed' {LOG}", timeout=60) == 0:
                break
            if vm.run(f"grep -q '( 30 / 30 )' {LOG} && ! pgrep -f 'rsync|unsquashfs' >/dev/null", timeout=60) == 0:
                time.sleep(60 * SLOW)
                done = True
                break
            time.sleep(30)
        vm.screenshot(out / "gui-finished.png")
        failed = vm.run(f"grep -qiE 'raised an exception|Installation failed' {LOG}", timeout=60) == 0
        record("gui-install", done and not failed, "Calamares erase-disk install, 30/30 steps")
        if not (done and not failed):
            vm.run(f"grep -iE -B2 -A8 'exception|failed' {LOG} | tail -40", timeout=60)
            return
        # Let the installed system talk on the serial console for the boot test.
        vm.run("sudo mount /dev/vda1 /mnt && for d in dev proc sys; do sudo mount --bind /$d /mnt/$d; done && "
               "sudo sed -i 's/^GRUB_CMDLINE_LINUX=.*/GRUB_CMDLINE_LINUX=\"console=tty0 console=ttyS0,115200n8\"/' /mnt/etc/default/grub && "
               "sudo chroot /mnt update-grub >/dev/null 2>&1; sudo umount -R /mnt", timeout=600)
        vm.send("sudo poweroff")
        time.sleep(10)
        ok = True
    except (pexpect.TIMEOUT, AssertionError) as exc:
        vm.screenshot(out / "gui-timeout.png")
        record("gui-install", False, str(exc).splitlines()[0][:120])
    finally:
        vm.kill()
    if not ok:
        return
    vm = VM(work, "gui-installed", disk=str(disk))
    try:
        login(vm, GUI_USER, GUI_PASS, timeout=900)
        record("gui-installed-boot", True, "login as the user created in Calamares")
        checks = {
            "gui-installed-sudo": f"echo '{GUI_PASS}' | sudo -S -v",
            "gui-installed-fstab": "findmnt -n / && grep -q '^UUID=' /etc/fstab",
            "gui-installed-no-casper": "! dpkg -l casper 2>/dev/null | grep -q '^ii'",
            "gui-installed-lightdm": "systemctl is-active lightdm",
        }
        for name, cmd in checks.items():
            record(name, vm.run(cmd, timeout=180) == 0)
        time.sleep(20 * SLOW)
        vm.screenshot(out / "gui-installed-login.png")
    except pexpect.TIMEOUT as exc:
        vm.screenshot(out / "gui-installed-timeout.png")
        record("gui-installed-boot", False, f"timeout: {str(exc).splitlines()[0]}")
    finally:
        vm.kill()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iso")
    ap.add_argument("--tests", default="iso-menu,live,install,installed,gui-install")
    ap.add_argument("--out", default="test-results")
    ap.add_argument("--work", default=None)
    args = ap.parse_args()

    tests = set(args.tests.split(","))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(args.work or tempfile.mkdtemp(prefix="orchard-test-"))
    work.mkdir(parents=True, exist_ok=True)
    # Work on a private copy so rebuilding the ISO cannot change it under a running VM.
    iso_copy = work / "test.iso"
    shutil.copy(Path(args.iso).resolve(), iso_copy)
    iso = str(iso_copy)
    log(f"ISO {iso}  KVM={'yes' if KVM else 'no (TCG, slow)'}  work={work}")

    if "iso-menu" in tests:
        test_iso_menu(iso, work, out)
    disk = work / "disk.qcow2"
    if "live" in tests or "install" in tests:
        disk = test_live_and_install(iso, work, out, "install" in tests)
    if "installed" in tests:
        if disk.exists():
            test_installed(disk, work, out)
        else:
            record("installed", False, "no installed disk")
    if "gui-install" in tests:
        test_gui_install(iso, work, out)

    print("\n================ Orchard OS test summary ================")
    for name, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {name:32s} {detail}")
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    with open(out / "summary.txt", "w") as f:
        for name, ok, detail in RESULTS:
            f.write(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
