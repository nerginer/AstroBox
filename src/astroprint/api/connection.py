# coding=utf-8
__author__ = "Gina Häußge <osd@foosel.net>"
__author__ = "Daniel Arroyo <daniel@astroprint.com>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import octoprint.util as util

from flask import request, jsonify, make_response

from octoprint.settings import settings
from octoprint.server import printer, restricted_access, NO_CONTENT
from octoprint.server.api import api

from astroprint.printer.manager import printerManager



@api.route("/connection", methods=["GET"])
def connectionState():
	state, port, baudrate = printer.getCurrentConnection()
	current = {
		"state": state,
		"port": port,
		"baudrate": baudrate
	}
	return jsonify({"current": current, "options": printer.getConnectionOptions()})


@api.route("/connection", methods=["POST"])
@restricted_access
def connectionCommand():
	global printer

	valid_commands = {
		"connect": ["autoconnect"],
		"save": [],
		"disconnect": []
	}

	command, data, response = util.getJsonCommandFromRequest(request, valid_commands)
	if response is not None:
		return response

	if command == "connect":
		s = settings()

		driver = None
		port = None
		baudrate = None
		if "driver" in data.keys():
			driver = data["driver"]

			printer = printerManager(driver, printer._fileManager)

		options = printer.getConnectionOptions()

		if "port" in data.keys():
			port = data["port"]
			if port not in options["ports"]:
				return make_response("Invalid port: %s" % port, 400)

		if "baudrate" in data.keys():
			baudrate = data["baudrate"]
			baudrates = options["baudrates"]
			if baudrates and baudrate not in baudrates:
				return make_response("Invalid baudrate: %d" % baudrate, 400)

		if "save" in data.keys() and data["save"]:

			s.set(["serial", "driver"], driver)
			s.set(["serial", "port"], port)
			s.setInt(["serial", "baudrate"], baudrate)

		if "autoconnect" in data.keys():
			s.setBoolean(["serial", "autoconnect"], data["autoconnect"])

		s.save()

		printer.connect(port=port, baudrate=baudrate)

	elif command == "disconnect":
		printer.disconnect()

	elif command == "save":
		if "driver" in data.keys():

			s = settings()
			driver = data["driver"]

			s.set(["serial", "driver"], driver)
			s.save()

			printer = printerManager(driver)

	return NO_CONTENT

