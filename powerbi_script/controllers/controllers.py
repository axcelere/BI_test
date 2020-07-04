# -*- coding: utf-8 -*-
from odoo import http

# class PowerbiScheduler(http.Controller):
#     @http.route('/powerbi_scheduler/powerbi_scheduler/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/powerbi_scheduler/powerbi_scheduler/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('powerbi_scheduler.listing', {
#             'root': '/powerbi_scheduler/powerbi_scheduler',
#             'objects': http.request.env['powerbi_scheduler.powerbi_scheduler'].search([]),
#         })

#     @http.route('/powerbi_scheduler/powerbi_scheduler/objects/<model("powerbi_scheduler.powerbi_scheduler"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('powerbi_scheduler.object', {
#             'object': obj
#         })