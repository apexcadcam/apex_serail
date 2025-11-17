app_name = "apex_serial"
app_title = "Apex Serial"
app_publisher = "Gaber"
app_description = "Serial Number management tools for used and demo devices"
app_email = "gaber@example.com"
app_license = "mit"

# DocType JavaScript
doctype_js = {
	"Serial No": "public/js/serial_no.js",
}

# Installation
after_install = "apex_serial.install.after_install"
after_migrate = ["apex_serial.install.after_migrate"]

# Uninstallation
before_uninstall = "apex_serial.install.before_uninstall"

# Fixtures
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["module", "=", "Apex Serial"]
		],
	},
]

