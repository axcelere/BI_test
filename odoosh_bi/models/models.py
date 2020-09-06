# -*- coding: utf-8 -*-
import datetime as datetime
import psycopg2
import base64
import pdb
import threading, odoo
import datetime
from zipfile import ZipFile
from odoo import models, fields, api, os
from odoo.exceptions import ValidationError, UserError, _logger, Warning


class odoosh_bi(models.Model):
    _name = 'odoosh_bi.odoosh_bi'
    _description = 'odoosh_bi.odoosh_bi'

    db_host = fields.Char(string='Database Host Name')  # 'rds_host_url'
    db_user_name = fields.Char(string='Username')  # 'your_name'
    db_password = fields.Char(string='Password')  # 'your_db_password'
    db_name = fields.Char(string='Database Name')  # 'your_database_name'
    db_port = fields.Char(string='Database Port')  # 'port'
    db_file = fields.Binary(string='Upload' )  # 'pgDump file'
    db_name_for_backup = fields.Char(string='Create DB For Backup')
    last_updated_RDS = fields.Text(string='last RDS update', default="Logs:__")
    logs = fields.Text(string='logs', default="Logs:_")
    blockFlag = fields.Boolean(string='Block Flag', default=False)

    @api.model
    def checkupdate(self, vals):
        connection = None
        try:
            connection = psycopg2.connect(
                database=vals['database'],
                user=vals['user'],
                password=vals['password'],
                host=vals['host'],
                port=vals['port']
            )
            
            if connection:
                cursor = connection.cursor()
                check_table = '''select count(*) from information_schema.tables where table_schema = 'public';'''
                cursor.execute(check_table)
                list_tables = cursor.fetchall()
                _logger.critical('>>>>>>>>>>>>>>>>>', list_tables)
                # print(list_tables)
                if (list_tables == [(0,)]):
                    # print("database is empty")
                    connection.close()
                    return True
                else:
                    # print("database is not empty")
                    connection.close()
                    return False
        except Exception as e:
            print(e)
        finally:
            if connection:
                connection.close()

    def _run_process(self, id):
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
        db_host = obj.db_host
        user_name = obj.db_user_name
        db_name = obj.db_name_for_backup
        port = obj.db_port
        pg_pass = obj.db_password
        db_to_bak = db_name
        output = "backup_file.zip"
        db_bak_path = ''
        
        val = {
            'database': db_name,
            'user': user_name,
            'password': pg_pass,
            'host': db_host,
            'port': port
        }

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
                        db_bak_path = fileName
                        zipObj.extract(fileName)
                        break
        except:
            print("Zip extraction error")
            return
        _logger.critical('>>>>>>>>>>>>>>>>>', 1)
        try:
            _logger.critical('Restoring The Database to the RDS server')
            _logger.critical('>>>>>>>>>>>>>>>>>', 2)

            os.system('PGPASSWORD=%s dropdb --host %s --port "%s" --username %s --if-exists %s' % (
                pg_pass, db_host, port, user_name, db_to_bak))
            _logger.critical('>>>>>>>>>>>>>>>>>', 3)

            os.system('PGPASSWORD=%s createdb --host %s --port "%s" --username %s %s' % (
                pg_pass, db_host, port, user_name, db_to_bak))
            _logger.critical('>>>>>>>>>>>>>>>>>', 4)
            
            status = self.checkupdate(val)
            _logger.critical('>>>>>>>>>>>>>>>>>', 5)

            if status == True:
                os.system('PGPASSWORD=%s psql --host %s --port "%s" --username %s -d %s -f %s' % (
                    pg_pass, db_host, port, user_name, db_to_bak, db_bak_path))
                _logger.critical('>>>>>>>>>>>>>>>>>', 6)
                status = self.checkupdate(val)
                if status == False:
                    _logger.critical('Restore Completed')
                else:
                    _logger.critical("Error While Restoring Database")
            else:
                _logger.critical("Database is Being Used Somewhere")
            
        except Exception as e:
            _logger.critical("Error While Restoring Database", e)


    def run_script(self, *args, **kwargs):
        id = self.id # args[0][0]
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
        try:
            self._run_process(id)
        except Exception as e:
            print(e)
            _logger.critical("Error While Restoring Database", e)
        
    @api.model
    def create(self, vals):
        if 'db_name_for_backup' in vals:
            vals['db_name_for_backup'] = vals['db_name_for_backup'].replace(" ", "")
            obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('db_name_for_backup', '=', vals['db_name_for_backup'])]).ids
            if obj:
                raise ValidationError("Database name is not unique, already been used in other backup")
        
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
        if 'db_name_for_backup' in vals:
            vals['db_name_for_backup'] = vals['db_name_for_backup'].replace(" ", "")
            obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('db_name_for_backup', '=', vals['db_name_for_backup'])]).ids
            if len(obj) > 0 or (len(obj) == 1 and self.id not in obj):
                raise ValidationError("Database name is not unique, already been used in other backup")
        print(vals, self)
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', self.id)])
        # print(obj)
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
