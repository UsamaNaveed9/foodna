# Copyright (c) 2023, smb and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from frappe.model.document import Document

class CustomerPricingForm(Document):
	def before_submit(self):
		if self.customer_name:
			for i in self.items:
				item = frappe.get_doc("Item",i.item_code)
				check = ""
				if item.customer_items:
					for j in item.customer_items:
						if self.customer_name == j.customer_name:
							j.ref_code = i.customer_code
							item.save()
							check = j.customer_name

					if not check:
						cust_it = frappe.new_doc("Item Customer Detail")
						cust_it.customer_name = self.customer_name
						cust_it.customer_group = frappe.get_value('Customer',self.customer_name,'customer_group')
						cust_it.ref_code = i.customer_code
						item.append("customer_items", cust_it)
						item.save()

				else:
					cust_it = frappe.new_doc("Item Customer Detail")
					cust_it.customer_name = self.customer_name
					cust_it.customer_group = frappe.get_value('Customer',self.customer_name,'customer_group')
					cust_it.ref_code = i.customer_code
					item.append("customer_items", cust_it)
					item.save()

		if self.price_list:
			for i in self.items:
				if frappe.db.exists("Item Price", {"item_code": i.item_code,"price_list":self.price_list,"selling":1}):
					name = frappe.get_value('Item Price',{'item_code': i.item_code,'price_list':self.price_list,'selling':1},'name')
					p_record = frappe.get_doc("Item Price",name)
					p_record.price_list_rate = i.customer_price
					p_record.save()
				else:
					pr_add = frappe.new_doc("Item Price")
					pr_add.item_code = i.item_code
					pr_add.item_name = i.item_name
					pr_add.uom = i.uom
					pr_add.price_list = self.price_list
					pr_add.selling = 1
					pr_add.price_list_rate = i.customer_price
					pr_add.save()

	def submit(self):
		if len(self.items) > 2:
			msgprint(_("The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Customer Pricing Form and revert to the Draft stage"))
			self.queue_action('submit', timeout==5000)
		else:
			self._submit()			
