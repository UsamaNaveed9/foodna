# Copyright (c) 2013, smb and contributors
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
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120,
		},
		{
			"fieldname": "customer_name",
			"label": _("Customer Name"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "customer_group",
			"label": _("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
			"width": 120,
		},
		{
			"fieldname": "gross_sales",
			"label": _("Gross Sales"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "sales_cogs",
			"label": _("Sales COGS"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "discount",
			"label": _("Discount"),
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"fieldname": "sales_after_discount",
			"label": _("Sales After Discount"),
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"fieldname": "sales_return",
			"label": _("Sales Return"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "return_cogs",
			"label": _("Return COGS"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "net_sales",
			"label": _("Net Sales"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "net_sales_cogs",
			"label": _("Net Sales COGS"),
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"fieldname": "total_cogs",
			"label": _("Total COGS"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "gross_profit_amt",
			"label": _("Gross Profit Amount"),
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"fieldname": "gross_profit_pct",
			"label": _("Profit %"),
			"fieldtype": "Float",
			"width": 100,
		},
	]

def get_data(filters=None):
	data = []
	if not filters.customer_group:
		customer_list = frappe.db.get_list('Customer', pluck='name')
	else:
		customer_list = []
		customer_list = frappe.db.get_list('Customer',
			filters={
				'customer_group': filters.customer_group
			},
			fields=['name'],
			pluck='name'
		)

	for row in customer_list:
		condition = ""
		if filters.customer_group:
			condition += "and si.customer_group = '{0}'".format(filters.customer_group)
		cust_inv = frappe.get_list("Sales Invoice", filters={"customer": row})
		if len(cust_inv) > 0:
			entries = frappe.db.sql("""select si.customer as customer, si.customer_name as customer_name, si.customer_group as customer_group,
								(select sum(si1.grand_total) from `tabSales Invoice` as si1 where si1.is_return = 0 and si1.docstatus = 1 and
									si1.posting_date >= '{0}' and si1.posting_date <= '{1}' and si1.customer = '{2}') as net_sales,
								(select sum(si2.grand_total) from `tabSales Invoice` as si2 where si2.is_return = 1 and si2.docstatus = 1 and
									si2.posting_date >= '{0}' and si2.posting_date <= '{1}' and si2.customer = '{2}') / -1 as sales_return,
								(select sum(si3.discount_amount) from `tabSales Invoice` as si3 where si3.is_return = 0 and si3.docstatus = 1 and
									si3.posting_date >= '{0}' and si3.posting_date <= '{1}' and si3.customer = '{2}') as s_discount,
								(select sum(si3.discount_amount) from `tabSales Invoice` as si3 where si3.is_return = 1 and si3.docstatus = 1 and
									si3.posting_date >= '{0}' and si3.posting_date <= '{1}' and si3.customer = '{2}') / -1 as r_discount		
							   from `tabSales Invoice` as si
						where si.docstatus = 1 and si.posting_date >= '{0}' and si.posting_date <= '{1}' and si.customer = '{2}' {3}
						group by si.customer""".format(filters.from_date,filters.to_date,row,condition),as_dict=1)

			if entries:
				gross_sales = sales_after_discount = 0.0
				for entry in entries:
					if entry['r_discount']:
						entry['discount'] = entry['s_discount'] + entry['r_discount']
					else:
						entry['discount'] = entry['s_discount']

					if entry['sales_return'] and entry['net_sales']:
						entry['net_sales'] = entry['net_sales'] - entry['sales_return']	
						entry['gross_sales'] = entry['net_sales'] + entry['sales_return'] + entry['discount']
					elif entry['net_sales']:
						entry['gross_sales'] = entry['net_sales'] + entry['discount']
					if entry['net_sales'] and entry['sales_return']:
						entry['sales_after_discount'] = entry['gross_sales'] - entry['discount']	

					sales_invoice_list = frappe.db.get_list('Sales Invoice',
						filters=[
							['posting_date', 'between', [filters.from_date, filters.to_date]],
							['docstatus', '=', '1'],
							['customer', '=', entry['customer']],
							['is_return', '=', 0]
						],
						fields=['name'],
						pluck='name'
					)
					#frappe.errprint(sales_invoice_list)
					sales_cogs = 0 
					for s_inv in sales_invoice_list:
						s_cogs_value = frappe.db.get_value("GL Entry",{'account': 'Cost of Goods Sold - FN','voucher_no': s_inv},'debit')
						if s_cogs_value is not None:
							sales_cogs += s_cogs_value
					
					sales_invoice_list = frappe.db.get_list('Sales Invoice',
						filters=[
							['posting_date', 'between', [filters.from_date, filters.to_date]],
							['docstatus', '=', '1'],
							['customer', '=', entry['customer']],
							['is_return', '=', 1]
						],
						fields=['name'],
						pluck='name'
					)
					#frappe.errprint(sales_invoice_list)
					return_cogs = 0 
					for s_inv in sales_invoice_list:
						r_cogs_value = frappe.db.get_value("GL Entry",{'account': 'Cost of Goods Sold - FN','voucher_no': s_inv},'credit')
						if r_cogs_value is not None:
							return_cogs += r_cogs_value

					entry['sales_cogs'] = sales_cogs
					entry['return_cogs'] = return_cogs
					entry['net_sales_cogs'] = sales_cogs - return_cogs
					entry['total_cogs'] = sales_cogs + return_cogs
					if entry['net_sales']:
						entry['gross_profit_amt'] = entry['net_sales'] - entry['total_cogs']
						if entry['gross_profit_amt'] > 0:
							entry['gross_profit_pct'] = (entry['gross_profit_amt'] / entry['net_sales']) * 100
						else:
							entry['gross_profit_pct'] = 0
				for entry in entries:
					data.append(entry)

	
	return data	
