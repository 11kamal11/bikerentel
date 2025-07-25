# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime

class Bike(models.Model):
    _name = 'bikerental.bike'
    _description = 'Bike'
    _order = 'name'

    name = fields.Char(string='Bike Name', required=True)
    brand = fields.Char(string='Brand', required=True)
    model = fields.Char(string='Model')
    bike_type_id = fields.Many2one('bikerental.bike.type', string='Bike Type')
    description = fields.Text(string='Description')
    rental_price = fields.Float(string='Rental Price (per day)', required=True)
    cost_price = fields.Float(string='Cost Price')
    purchase_date = fields.Date(string='Purchase Date')
    is_available = fields.Boolean(string='Available', compute='_compute_is_available')
    active = fields.Boolean(string='Active', default=True)
    serial_number = fields.Char(string='Serial Number')
    color = fields.Char(string='Color')
    gear_count = fields.Integer(string='Number of Gears')
    stock_quantity = fields.Integer(string='Stock Quantity', default=1)
    age_years = fields.Integer(string='Age (Years)', compute='_compute_age_years')
    profit_margin = fields.Float(string='Profit Margin (%)', compute='_compute_profit_margin', store=True)

    @api.depends('stock_quantity')
    def _compute_is_available(self):
        for record in self:
            record.is_available = record.stock_quantity > 0

    @api.depends('purchase_date')
    def _compute_age_years(self):
        for record in self:
            if record.purchase_date:
                today = date.today()
                record.age_years = today.year - record.purchase_date.year
            else:
                record.age_years = 0

    @api.depends('rental_price', 'cost_price')
    def _compute_profit_margin(self):
        for record in self:
            if record.cost_price and record.rental_price:
                record.profit_margin = ((record.rental_price - record.cost_price) / record.cost_price) * 100
            else:
                record.profit_margin = 0.0

    @api.constrains('rental_price', 'cost_price')
    def _check_prices(self):
        for record in self:
            if record.rental_price < 0:
                raise ValidationError("Rental price cannot be negative.")
            if record.cost_price < 0:
                raise ValidationError("Cost price cannot be negative.")

class BikeType(models.Model):
    _name = 'bikerental.bike.type'
    _description = 'Bike Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')
    bike_ids = fields.One2many('bikerental.bike', 'bike_type_id', string='Bikes')
    bike_count = fields.Integer(string='Number of Bikes', compute='_compute_bike_count')

    @api.depends('bike_ids')
    def _compute_bike_count(self):
        for record in self:
            record.bike_count = len(record.bike_ids.filtered('active'))


class RentalOrder(models.Model):
    _name = 'bikerental.order'
    _description = 'Bike Rental Order'
    _order = 'create_date desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, default='New')
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_email = fields.Char(string='Customer Email', required=True)
    customer_phone = fields.Char(string='Customer Phone')
    start_date = fields.Datetime(string='Rental Start Date', required=True)
    end_date = fields.Datetime(string='Rental End Date', required=True)
    total_days = fields.Integer(string='Total Days', compute='_compute_total_days', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('online', 'Online Payment')
    ], string='Payment Method', required=True)
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], string='Payment Status', default='pending')
    order_line_ids = fields.One2many('bikerental.order.line', 'order_id', string='Order Lines')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('bikerental.order') or 'New'
        return super(RentalOrder, self).create(vals)

    @api.depends('start_date', 'end_date')
    def _compute_total_days(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.total_days = max(1, delta.days)
            else:
                record.total_days = 1

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(line.subtotal for line in record.order_line_ids)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_start_rental(self):
        self.state = 'in_progress'

    def action_return(self):
        self.state = 'returned'

    def action_cancel(self):
        self.state = 'cancelled'


class RentalOrderLine(models.Model):
    _name = 'bikerental.order.line'
    _description = 'Rental Order Line'

    order_id = fields.Many2one('bikerental.order', string='Order', required=True, ondelete='cascade')
    bike_id = fields.Many2one('bikerental.bike', string='Bike', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price', related='bike_id.rental_price', store=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price', 'order_id.total_days')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price * (record.order_id.total_days or 1)


class Cart(models.Model):
    _name = 'bikerental.cart'
    _description = 'Shopping Cart'

    session_id = fields.Char(string='Session ID', required=True)
    bike_id = fields.Many2one('bikerental.bike', string='Bike', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    create_date = fields.Datetime(string='Created', default=fields.Datetime.now)
