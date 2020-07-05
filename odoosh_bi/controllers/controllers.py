# -*- coding: utf-8 -*-
# from odoo import http


# class OdooshBi(http.Controller):
#     @http.route('/odoosh_bi/odoosh_bi/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoosh_bi/odoosh_bi/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoosh_bi.listing', {
#             'root': '/odoosh_bi/odoosh_bi',
#             'objects': http.request.env['odoosh_bi.odoosh_bi'].search([]),
#         })

#     @http.route('/odoosh_bi/odoosh_bi/objects/<model("odoosh_bi.odoosh_bi"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoosh_bi.object', {
#             'object': obj
#         })
