# -*- coding: utf-8 -*-
import psycopg2
import base64
from zipfile import ZipFile
from odoo import models, fields, api, os
from odoo.exceptions import ValidationError, UserError, _logger

import threading, odoo

class odoosh_bi(models.Model):
    _name = 'odoosh_bi.odoosh_bi'
    _description = 'odoosh_bi.odoosh_bi'

    db_host = fields.Char(string='Database Host Name', required=True)  # 'rds_host_url'
    db_user_name = fields.Char(string='Username', required=True)  # 'your_name'
    db_password = fields.Char(string='Password', required=True)  # 'your_db_password'
    db_name = fields.Char(string='Database Name', required=True)  # 'your_database_name'
    db_port = fields.Char(string='Database Port', required=True)  # 'database_to_backup_name'
    db_file = fields.Binary(string='Upload', required=True)  # 'pgDump file'
    db_filename = fields.Char(string='fileName')


    def _run_process(self, id):
        with api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                obj = new_env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
                db_host = obj.db_host
                user_name = obj.db_user_name
                db_name = obj.db_name
                port = obj.db_port
                pg_pass = obj.db_password
                db_to_bak = obj.db_name
                output = "backup_file.zip"
                db_bak_path = ''
                # print(db_host, user_name, db_name, port, pg_pass, db_to_bak)

                try:
                    if os.path.exists(output):
                        os.remove(output)

                    fd = base64.b64decode(obj.db_file)
                    f = open(output, "wb")
                    f.write(fd)
                    f.close()
                except Exception as e:
                    print(e)
                    return

                try:
                    with ZipFile(output, 'r') as zipObj:
                        listOfFileNames = zipObj.namelist()
                        for fileName in listOfFileNames:
                            if fileName.endswith('.sql'):
                                db_bak_path =  fileName
                                zipObj.extract(fileName)
                                break

                except:
                    print("Zip extraction error")
                    return

                try:
                    _logger.info('Restoring The Database to the RDS server')
                    os.system('PGPASSWORD=%s dropdb --host %s --port "%s" --username %s --if-exists %s' % (
                                pg_pass, db_host, port, user_name, db_to_bak))
                    os.system('PGPASSWORD=%s createdb --host %s --port "%s" --username %s %s' % (
                                pg_pass, db_host, port, user_name, db_to_bak))
                    os.system('PGPASSWORD=%s psql --host %s --port "%s" --username %s -d %s -f %s' % (
                                pg_pass, db_host, port, user_name, db_to_bak, db_bak_path))
                    _logger.info('Restore Completed')
                except Exception as e:
                    print(e)
                    print("Connection Error: Not connecting")


    @api.model
    def run_script(self, *args, **kwargs):
        obj = threading.Thread(target=self._run_process, args=(args[0][0],))
        obj.start()


    @api.model
    def create(self, vals):
        connection = None
        try:
            connection = psycopg2.connect(
                database=vals['db_name'],
                user=vals['db_user_name'],
                password=vals['db_password'],
                host=vals['db_host'],
                port=vals['db_port']
            )
        except Exception as e:
            print(e)
            raise ValidationError("Incorrect credentials Please check and try again")
        finally:
            if connection:
                connection.close()
                return super(odoosh_bi, self).create(vals)
    

    def write(self, vals):
        print(vals, self)
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', self.id)])
        print(obj)
        updated_vals = {
            'db_name': obj.db_name,
            'db_user_name': obj.db_user_name,
            'db_password': obj.db_password,
            'db_host': obj.db_host,
            'db_port': obj.db_port
        }
        for i in vals:
            updated_vals[i] = vals[i]

        connection = None
        try:
            connection = psycopg2.connect(
                database=updated_vals['db_name'],
                user=updated_vals['db_user_name'],
                password=updated_vals['db_password'],
                host=updated_vals['db_host'],
                port=updated_vals['db_port']
            )
        except Exception as e:
            print(e)
            raise ValidationError("Incorrect credentials Please check and try again")
        finally:
            if connection:
                connection.close()
        return super(odoosh_bi, self).write(vals)