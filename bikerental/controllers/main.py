# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from datetime import datetime

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

    @http.route('/bikerental/add_to_cart', type='json', auth='public', website=True)
    def add_to_cart(self, bike_id, quantity=1, start_date=None, end_date=None):
        """Add bike to cart"""
        session_id = request.session.sid
        if not session_id:
            return {'error': 'Session not available'}
        
        bike = request.env['bikerental.bike'].sudo().browse(int(bike_id))
        if not bike.exists() or not bike.active:
            return {'error': 'Bike not found'}
        
        # Check if item already in cart
        cart_item = request.env['bikerental.cart'].sudo().search([
            ('session_id', '=', session_id),
            ('bike_id', '=', bike.id)
        ], limit=1)
        
        if cart_item:
            cart_item.quantity += int(quantity)
            if start_date:
                cart_item.start_date = start_date
            if end_date:
                cart_item.end_date = end_date
        else:
            request.env['bikerental.cart'].sudo().create({
                'session_id': session_id,
                'bike_id': bike.id,
                'quantity': int(quantity),
                'start_date': start_date,
                'end_date': end_date,
            })
        
        # Get cart count
        cart_count = sum(request.env['bikerental.cart'].sudo().search([
            ('session_id', '=', session_id)
        ]).mapped('quantity'))
        
        return {'success': True, 'cart_count': cart_count}

    @http.route('/bikerental/cart', type='http', auth='public', website=True)
    def view_cart(self, **kwargs):
        """View shopping cart"""
        session_id = request.session.sid
        cart_items = request.env['bikerental.cart'].sudo().search([
            ('session_id', '=', session_id)
        ])
        
        total = 0
        for item in cart_items:
            days = 1
            if item.start_date and item.end_date:
                delta = item.end_date - item.start_date
                days = max(1, delta.days)
            item.days = days
            item.total_price = item.bike_id.rental_price * item.quantity * days
            total += item.total_price
        
        return request.render('bikerental.cart_page', {
            'cart_items': cart_items,
            'total': total,
        })

    @http.route('/bikerental/remove_from_cart', type='json', auth='public', website=True)
    def remove_from_cart(self, cart_item_id):
        """Remove item from cart"""
        session_id = request.session.sid
        cart_item = request.env['bikerental.cart'].sudo().search([
            ('id', '=', int(cart_item_id)),
            ('session_id', '=', session_id)
        ], limit=1)
        
        if cart_item:
            cart_item.unlink()
            return {'success': True}
        return {'error': 'Item not found'}

    @http.route('/bikerental/checkout', type='http', auth='public', website=True)
    def checkout(self, **kwargs):
        """Checkout page"""
        session_id = request.session.sid
        cart_items = request.env['bikerental.cart'].sudo().search([
            ('session_id', '=', session_id)
        ])
        
        if not cart_items:
            return request.redirect('/bikerental/cart')
        
        total = 0
        for item in cart_items:
            days = 1
            if item.start_date and item.end_date:
                delta = item.end_date - item.start_date
                days = max(1, delta.days)
            item.days = days
            item.total_price = item.bike_id.rental_price * item.quantity * days
            total += item.total_price
        
        return request.render('bikerental.checkout_page', {
            'cart_items': cart_items,
            'total': total,
        })

    @http.route('/bikerental/process_order', type='http', auth='public', website=True, methods=['POST'])
    def process_order(self, **kwargs):
        """Process the rental order"""
        session_id = request.session.sid
        cart_items = request.env['bikerental.cart'].sudo().search([
            ('session_id', '=', session_id)
        ])
        
        if not cart_items:
            return request.redirect('/bikerental/cart')
        
        # Create order
        order_vals = {
            'customer_name': kwargs.get('customer_name'),
            'customer_email': kwargs.get('customer_email'),
            'customer_phone': kwargs.get('customer_phone'),
            'start_date': kwargs.get('start_date'),
            'end_date': kwargs.get('end_date'),
            'payment_method': kwargs.get('payment_method'),
            'notes': kwargs.get('notes', ''),
        }
        
        order = request.env['bikerental.order'].sudo().create(order_vals)
        
        # Create order lines
        for item in cart_items:
            request.env['bikerental.order.line'].sudo().create({
                'order_id': order.id,
                'bike_id': item.bike_id.id,
                'quantity': item.quantity,
            })
        
        # Clear cart
        cart_items.unlink()
        
        # Handle payment
        if kwargs.get('payment_method') == 'online':
            return request.redirect('/bikerental/payment/%s' % order.id)
        else:
            order.payment_status = 'pending'
            return request.redirect('/bikerental/order_success/%s' % order.id)

    @http.route('/bikerental/payment/<int:order_id>', type='http', auth='public', website=True)
    def payment_page(self, order_id, **kwargs):
        """Online payment page"""
        order = request.env['bikerental.order'].sudo().browse(order_id)
        if not order.exists():
            return request.not_found()
        
        return request.render('bikerental.payment_page', {
            'order': order,
        })

    @http.route('/bikerental/process_payment', type='http', auth='public', website=True, methods=['POST'])
    def process_payment(self, **kwargs):
        """Process online payment (simulation)"""
        order_id = int(kwargs.get('order_id'))
        order = request.env['bikerental.order'].sudo().browse(order_id)
        
        if not order.exists():
            return request.not_found()
        
        # Simulate payment processing
        payment_success = kwargs.get('card_number') and len(kwargs.get('card_number', '')) >= 16
        
        if payment_success:
            order.payment_status = 'paid'
            return request.redirect('/bikerental/order_success/%s' % order.id)
        else:
            order.payment_status = 'failed'
            return request.render('bikerental.payment_failed', {'order': order})

    @http.route('/bikerental/order_success/<int:order_id>', type='http', auth='public', website=True)
    def order_success(self, order_id, **kwargs):
        """Order success page"""
        order = request.env['bikerental.order'].sudo().browse(order_id)
        if not order.exists():
            return request.not_found()
        
        return request.render('bikerental.order_success', {
            'order': order,
        })

    @http.route('/bikerental/my_orders', type='http', auth='public', website=True)
    def my_orders(self, **kwargs):
        """Customer order history page"""
        email = kwargs.get('email')
        if not email:
            return request.render('bikerental.order_lookup', {})
        
        orders = request.env['bikerental.order'].sudo().search([
            ('customer_email', '=', email)
        ])
        
        return request.render('bikerental.my_orders', {
            'orders': orders,
            'email': email,
        })
