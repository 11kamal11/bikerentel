# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class BikeRentalController(http.Controller):

    @http.route('/bikerental/test', type='http', auth='public', website=True)
    def bikerental_test(self, **kwargs):
        """Simple test page to verify routing works"""
        return request.render('bikerental.bikerental_test', {})

    @http.route('/bikerental', type='http', auth='public', website=True)
    def bikerental_home(self, **kwargs):
        """Display all bikes on the rental homepage"""
        try:
            bikes = request.env['bikerental.bike'].sudo().search([('active', '=', True)])
            types = request.env['bikerental.bike.type'].sudo().search([])
            return request.render('bikerental.bikerental_home', {
                'bikes': bikes,
                'types': types,
            })
        except Exception as e:
            return request.render('bikerental.bikerental_simple', {
                'error': str(e)
            })

    @http.route('/bikerental/bike/<int:bike_id>', type='http', auth='public', website=True)
    def bike_detail(self, bike_id, **kwargs):
        """Display detailed view of a single bike"""
        bike = request.env['bikerental.bike'].sudo().browse(bike_id)
        if not bike.exists() or not bike.active:
            return request.not_found()
        related_bikes = request.env['bikerental.bike'].sudo().search([
            ('bike_type_id', '=', bike.bike_type_id.id),
            ('id', '!=', bike.id),
            ('active', '=', True)
        ], limit=4)
        return request.render('bikerental.bike_detail', {
            'bike': bike,
            'related_bikes': related_bikes,
        })

    @http.route('/bikerental/type/<int:type_id>', type='http', auth='public', website=True)
    def bikes_by_type(self, type_id, **kwargs):
        """Display bikes filtered by type"""
        bike_type = request.env['bikerental.bike.type'].sudo().browse(type_id)
        if not bike_type.exists():
            return request.not_found()
        bikes = request.env['bikerental.bike'].sudo().search([
            ('bike_type_id', '=', type_id),
            ('active', '=', True)
        ])
        types = request.env['bikerental.bike.type'].sudo().search([])
        return request.render('bikerental.bikerental_home', {
            'bikes': bikes,
            'types': types,
            'current_type': bike_type,
        })

    @http.route('/bikerental/search', type='http', auth='public', website=True)
    def bike_search(self, search='', **kwargs):
        """Search bikes by name or brand"""
        domain = [('active', '=', True)]
        if search:
            domain.extend([
                '|', '|',
                ('name', 'ilike', search),
                ('brand', 'ilike', search),
                ('description', 'ilike', search)
            ])
        bikes = request.env['bikerental.bike'].sudo().search(domain)
        types = request.env['bikerental.bike.type'].sudo().search([])
        return request.render('bikerental.bikerental_home', {
            'bikes': bikes,
            'types': types,
            'search_term': search,
        })
