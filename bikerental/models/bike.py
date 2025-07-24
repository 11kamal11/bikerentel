# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

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
