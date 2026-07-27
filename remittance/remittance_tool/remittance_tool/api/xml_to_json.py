import xml.etree.ElementTree as ET

import frappe


@frappe.whitelist()
def convert_sap_xml_to_json(xml_string):
	namespaces = {
		"d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
		"m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
		"atom": "http://www.w3.org/2005/Atom",
	}

	root = ET.fromstring(xml_string)
	entries = []

	for entry in root.findall("atom:entry", namespaces):
		properties = entry.find(".//m:properties", namespaces)

		if properties is not None:
			entry_data = {}
			for prop in properties:
				tag = prop.tag.split("}")[1] if "}" in prop.tag else prop.tag
				entry_data[tag] = prop.text if prop.text else ""

			entries.append(entry_data)

	return entries
