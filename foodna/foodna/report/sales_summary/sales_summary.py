# Copyright (c) 2023, smb and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	return [
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Data",
			"width": 300,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "sales_qty",
			"label": _("Sales Quantity"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "return_qty",
			"label": _("Return Quantity"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "net_sales",
			"label": _("Net Sales"),
			"fieldtype": "Float",
			"width": 120,
		},
	]

def get_data(filters=None):
	data = []
	if not filters.customer:
		customer_list = frappe.db.get_list('Customer', pluck='name')
	else:
		customer_list = []
		customer_list.append(filters.customer)
	for row in customer_list:
		condition = ""
		if filters.item:
			condition += "and sii.item_code = '{0}'".format(filters.item)
		entries = frappe.db.sql("""select sii.item_code as item_code, sii.item_name as item_name,
                                (select if(sum(sii1.qty),sum(sii1.qty),0) from `tabSales Invoice` as si1 join `tabSales Invoice Item` as sii1 where sii1.parent = si1.name
                                        and si1.is_return = 0 and sii1.item_code = sii.item_code and sii1.docstatus = 1 and
                                        '{0}' < si1.posting_date < '{1}' and si1.customer = '{2}') as sales_qty,
                                (select if(sum(sii1.qty),sum(sii1.qty),0) from `tabSales Invoice` as si1 join `tabSales Invoice Item` as sii1 where sii1.parent = si1.name
                                        and si1.is_return = 1 and sii1.item_code = sii.item_code and sii1.docstatus = 1 and
                                        '{0}' < si1.posting_date < '{1}' and si1.customer = '{2}') / -1 as return_qty,
                                sum(sii.qty) as net_sales from `tabSales Invoice` as si join `tabSales Invoice Item` as sii on si.name = sii.parent
                        where si.docstatus = 1 and '{0}' < si.posting_date < '{1}' and si.customer = '{2}' {3}
                        group by sii.item_code""".format(filters.from_date,filters.to_date,row,condition),as_dict=1)
		if entries:
			total_sales = total_return = total_net_sales = 0.0
			for entry in entries:
				entry['sales_qty'] += entry['return_qty'] 
				entry['net_sales'] = entry['sales_qty'] - entry['return_qty']
				total_sales += entry['sales_qty']
				total_return += entry['return_qty']
				total_net_sales += entry['net_sales']
			cus_name = frappe.db.get_value("Customer",row,"customer_name")
			data.append({'item_code': row, 'item_name': cus_name , 'sales_qty': total_sales, 'return_qty': total_return, 'net_sales': total_net_sales, 'indent': 0 })
			for entry in entries:
				entry.update({'indent': 1})
				data.append(entry)
	return data

