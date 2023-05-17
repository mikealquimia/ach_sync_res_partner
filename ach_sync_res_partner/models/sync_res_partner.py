# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xmlrpc.client
import logging
_logger = logging.getLogger(__name__)

class SyncResPartner(models.Model):
    _name = 'sync.res_partner'
    _description = 'Sync Res Partner'

    name = fields.Char(string="Name", required=True)
    state = fields.Selection([('draft','Draft'),('logging','Logging'),('progress','Progress'),('done','Done')], string="State", default='draft')
    url_database = fields.Char(string="URL", required=True)
    database_name = fields.Char(string="Database", required=True)
    username_database = fields.Char(string="User Name", required=True)
    password_username_database = fields.Char(string="Password", required=True)

    type_sync = fields.Selection([('advance','Advance'),('normal','Normal')], string="Type sync", default='normal')
    partner_fields_ids = fields.One2many('sync.partner_fields', 'odoo_sync_id', string="Fields")

    def logging_db(self):
        url = self.url_database
        db = self.database_name
        username = self.username_database
        password = self.password_username_database
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        version = common.version()
        uid = common.authenticate(db, username, password, {})
        if uid:
            self.write({'state':'logging'})
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url_database))
            try:
                partner_fields = models.execute_kw(self.database_name, uid, self.password_username_database, 'ir.model.fields', 'search_read', [[['model_id','=','res.partner']]], {'fields': ['name','field_description','ttype']})
                if partner_fields:
                    for line in self.partner_fields_ids:
                        line.unlink()
                    for field in partner_fields:
                        vals = {
                            'name': field['name'],
                            'name_import': field['name'],
                            'field_description_import': field['field_description'],
                            'ttype_import': field['ttype'],
                            'odoo_sync_id': self.id,
                        }
                        self.env['sync.partner_fields'].create(vals)
                    model_partner = self.env['ir.model'].search([('model','=','res.partner')],limit=1)
                    field_exist = self.env['ir.model.fields'].search([('model_id','=',model_partner.id)])
                    for line in self.partner_fields_ids:
                        for fields in field_exist:
                            if line.name_import == fields.name and line.ttype_import == fields.ttype:
                                line.write({'name_dest': fields.id, 'import_field': True})
            except:
                raise UserError('An error has occurred with the connection data, verify your data access or server data')
        else:
            raise UserError('An error has occurred with the connection data, verify your data access')
    
    def import_data(self):
        return

class SyncPartnerFields(models.Model):
    _name = 'sync.partner_fields'
    _description = 'Odoo Sync Ir Models Fields'

    name = fields.Char(string="Name")
    name_import = fields.Char(string="Field Import")
    field_description_import = fields.Char(string="Description Import")
    ttype_import = fields.Selection([
        ('binary','binary'),('boolean','boolean'),('char','char'),('date','date'),('datetime','datetime'),
        ('float','float'),('html','html'),('integer','integer'),('many2many','many2many'),('many2one','many2one'),('monetary','monetary'),
        ('many2one_reference','many2one_reference'),('one2many','one2many'),('reference','reference'),('selection','selection'),('text','text')],
        string="Type Import")
    name_dest = fields.Many2one('ir.model.fields', string="Field Dest")
    ttype_dest = fields.Selection([
        ('binary','Binary'),('boolean','Boolean'),('char','Char'),('date','Date'),('datetime','Datetime'),
        ('float','Float'),('html','Html'),('integer','Integer'),('many2many','Many2many'),('many2one','Many2one'),('monetary','Monetary'),
        ('many2one_reference','Many2one Reference'),('one2many','One2many'),('reference','Reference'),('selection','Selection'),('text','Text')],
        string="Type Dest", related="name_dest.ttype")
    import_field = fields.Boolean(string="Import", default=False)
    odoo_sync_id = fields.Many2one('sync.res_partner', string="Odoo Sync")