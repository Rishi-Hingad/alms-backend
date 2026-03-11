frappe.listview_settings["Lease Management"] = {
	get_indicator: function (doc) {
		const status_colors = {
			Active: "green",
			Terminated: "red",
			Modified: "blue",
			Discarded: "yellow",
			"Agreement Expired": "grey",
		};

		let color = status_colors[doc.status] || "orange";

		return [__(doc.status), color, `status,=,${doc.status}`];
	},
};
