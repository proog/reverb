import pytest
import os
import testhelper
from flask.testing import Client
from app import make_app
from veracrypt import VolumeManager

manager = VolumeManager(testhelper.VOLUMES_PATH)
app = make_app(manager)


def get_href(obj, rel):
    links = obj["_links"]
    return next(link["href"] for link in links if link["rel"] == rel)


def unmount_all():
    for volume in manager.get_volumes():
        try:
            volume.unmount()
        except:
            pass


@pytest.fixture
def client():
    testhelper.reset_test_data()
    yield app.test_client()
    unmount_all()


def test_root(client: Client):
    res = client.get("/")
    data = res.get_json()

    assert res.status_code == 200
    assert len(data["_links"]) == 1


def test_get_volumes(client: Client):
    res = client.get("/volumes")
    data = res.get_json()

    assert res.status_code == 200
    assert len(data["volumes"]) == len(manager.get_volumes())
    assert data["volumes"][0]["name"] == "test"


def test_get_volume(client: Client):
    res = client.get("/volumes/test")
    data = res.get_json()

    assert res.status_code == 200
    assert data["name"] == "test"
    assert not data["mounted"]
    assert len(data["_links"]) == 1


def test_put_volume(client: Client):
    res = client.put("/volumes/test", json={"password": "foo"})
    data = res.get_json()

    assert res.status_code == 200
    assert data["name"] == "test"
    assert data["mounted"]
    assert len(data["_links"]) == 2


@pytest.mark.parametrize("password", [("",), ("FOO",)])
def test_put_volume_incorrect_password(client: Client, password):
    res = client.put("/volumes/test", json={"password": password})
    data = res.get_json()

    assert res.status_code == 401


def test_delete_volume(client: Client):
    res = client.put("/volumes/test", json={"password": "foo"})
    href = get_href(res.get_json(), "self")

    res = client.delete(href)
    data = res.get_json()

    assert res.status_code == 200
    assert data["name"] == "test"
    assert not data["mounted"]
    assert len(data["_links"]) == 1


def test_get_files(client: Client):
    res = client.put("/volumes/test", json={"password": "foo"})
    href = get_href(res.get_json(), "files")

    res = client.get(href)
    data = res.get_json()

    assert res.status_code == 200
    assert any(
        x["name"] == "bar.txt" and x["type"] == "file" and x["size"] == 11
        for x in data["contents"]
    )
    assert any(
        x["name"] == "foo" and x["type"] == "directory" for x in data["contents"]
    )
