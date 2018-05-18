import pytest
import shutil
import testhelper
from os import makedirs
from os.path import exists, join, abspath
from veracrypt import Volume, _parse_list

MOUNT_PATH = "/tmp/testvolume-mount"


@pytest.fixture
def volume():
    testhelper.reset_test_data()
    return Volume("test", join(testhelper.VOLUMES_PATH, "test"))


def test_mount(volume: Volume):
    volume.mount("foo", MOUNT_PATH)
    mount_path = volume.get_mount_path()
    assert exists(mount_path)

    volume.unmount()
    assert volume.get_mount_path() is None
    assert not exists(mount_path)


def test_rw(volume: Volume):
    volume.mount("foo", MOUNT_PATH)
    filename = join(volume.get_mount_path(), "bar.txt")

    with open(filename, "w") as f:
        f.write("hello!\n")

    with open(filename, "r") as f:
        assert f.read() == "hello!\n"

    volume.unmount()


def test_ro(volume: Volume):
    volume.mount("foo", MOUNT_PATH, readonly=True)
    filename = join(volume.get_mount_path(), "bar.txt")

    with pytest.raises(IOError):
        with open(filename, "w") as f:
            f.write("hello!\n")

    with open(filename, "r") as f:
        assert f.read() == "unmodified\n"

    volume.unmount()


def test_is_mounted(volume: Volume):
    volume.mount("foo", MOUNT_PATH)
    assert volume.is_mounted()

    volume.unmount()
    assert not volume.is_mounted()


def test_parse_list():
    output = (
        "1: /foo/bar/baz.vc /dev/disk4 '/tmp/something with spaces'\n\n"
        "something completely different\n"
        "2: 'what about this' /dev/disk5 /tmp/somethingelse\n"
    )
    expected = [
        ("/foo/bar/baz.vc", "/dev/disk4", "/tmp/something with spaces"),
        ("what about this", "/dev/disk5", "/tmp/somethingelse"),
    ]

    parsed = _parse_list(output)
    assert parsed == expected
