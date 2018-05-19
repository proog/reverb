import os
from datetime import datetime
from uuid import uuid4
from tempfile import mkdtemp
from flask import jsonify, abort, send_file, url_for, request
from flask.views import MethodView
from veracrypt import Volume, VolumeManager


def make_link(rel, endpoint, **values):
    return {"rel": rel, "href": url_for(endpoint, **values)}


def to_json(volume: Volume):
    is_mounted = volume.is_mounted()
    links = [make_link("self", VolumeAPI.view_name, name=volume.name)]

    if is_mounted:
        files_link = make_link("files", FilesAPI.view_name, name=volume.name)
        links.append(files_link)

    return {"name": volume.name, "mounted": is_mounted, "_links": links}


class BaseAPI(MethodView):

    def __init__(self, manager: VolumeManager):
        self.manager = manager

    def _get_volume(self, name):
        volume = self.manager.get_volume(name)

        if volume is None:
            abort(404)

        return volume


class RootAPI(MethodView):
    view_name = "root"

    def get(self):
        return jsonify({"_links": [make_link("volumes", VolumesAPI.view_name)]})


class VolumesAPI(BaseAPI):
    view_name = "volumes"

    def get(self):
        response = {
            "volumes": [to_json(v) for v in self.manager.get_volumes()],
            "_links": [make_link("self", VolumesAPI.view_name)],
        }
        return jsonify(response)


class VolumeAPI(BaseAPI):
    view_name = "volume"

    def get(self, name):
        volume = self._get_volume(name)
        return jsonify(to_json(volume))

    def put(self, name):
        volume = self._get_volume(name)
        options = request.get_json()
        password = options.get("password", "") if isinstance(options, dict) else ""

        if not volume.is_mounted():
            try:
                volume.mount(password, mkdtemp())
            except:
                abort(401)

        return jsonify(to_json(volume))

    def delete(self, name):
        volume = self._get_volume(name)

        if volume.is_mounted():
            volume.unmount()

        return jsonify(to_json(volume))


class FilesAPI(BaseAPI):
    view_name = "volume_files"

    def get(self, name, path=""):
        volume = self._get_volume(name)

        if not volume.is_mounted():
            abort(400)

        mount_path = volume.get_mount_path()
        path = path.strip("/")
        full_path = os.path.join(mount_path, path)

        if not os.path.abspath(full_path).startswith(mount_path):
            abort(400)

        if os.path.isfile(full_path):
            return send_file(full_path)

        if os.path.isdir(full_path):
            contents = self._map_directory(volume.name, path, full_path)
            response = {
                "contents": list(contents),
                "_links": [
                    make_link(
                        "self",
                        FilesAPI.view_name,
                        name=volume.name,
                        path=path if path != "" else None,
                    )
                ],
            }
            return jsonify(response)

        abort(404)

    def _map_directory(self, volume_name, relative_path, full_path):
        names = os.listdir(full_path)

        for name in names:
            absname = os.path.join(full_path, name)
            modified = datetime.utcfromtimestamp(os.path.getmtime(absname)).isoformat()
            link = make_link(
                "self",
                FilesAPI.view_name,
                name=volume_name,
                path=os.path.join(relative_path, name),
            )

            if os.path.isdir(absname):
                yield {
                    "type": "directory",
                    "name": name,
                    "modified": modified,
                    "_links": [link],
                }
            elif os.path.isfile(absname):
                yield {
                    "type": "file",
                    "name": name,
                    "modified": modified,
                    "size": os.path.getsize(absname),
                    "_links": [link],
                }
