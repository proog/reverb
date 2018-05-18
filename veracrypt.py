import os.path
import subprocess
import re
import shlex

VERACRYPT = "/Applications/VeraCrypt.app/Contents/MacOS/VeraCrypt"


class Volume:

    def __init__(self, name, volume_path):
        self.name = name
        self.volume_path = os.path.abspath(volume_path)

    def mount(self, password, mount_path, readonly=False):
        args = [
            VERACRYPT,
            "--text",
            "--non-interactive",
            "--stdin",
            self.volume_path,
            mount_path,
        ]

        if readonly:
            args.insert(-2, "--mount-options=ro")

        p = subprocess.run(args, input=password.encode("utf-8"), timeout=10)
        p.check_returncode()

    def unmount(self):
        args = [VERACRYPT, "--text", "--dismount", self.volume_path]
        p = subprocess.run(args)
        p.check_returncode()

    def is_mounted(self):
        return self.get_mount_path() is not None

    def get_mount_path(self):
        line = self._get_list_entry()
        return line[2] if line is not None else None

    def _get_list_entry(self):
        args = [VERACRYPT, "--text", "--list"]
        p = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding="utf-8"
        )

        if p.returncode != 0:
            return None

        parsed = _parse_list(p.stdout)
        return next((x for x in parsed if x[0] == self.volume_path), None)


class VolumeManager:

    def __init__(self, volume_dir):
        self.volume_dir = os.path.abspath(volume_dir)
        self.volumes = [
            Volume(name, os.path.join(self.volume_dir, name))
            for name in os.listdir(self.volume_dir)
        ]

    def get_volumes(self):
        return self.volumes

    def get_volume(self, name) -> Volume:
        return next((v for v in self.volumes if v.name == name), None)


def _parse_list(output):
    lines = re.findall(r"^\d+: (.+)$", output, re.MULTILINE)
    return [tuple(shlex.split(line)) for line in lines]
